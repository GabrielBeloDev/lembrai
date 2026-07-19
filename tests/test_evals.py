from lembrai import evals
from lembrai.chat import Reply
from lembrai.evals import (
    Case,
    parse_judge_verdict,
    run_evals,
    score_case,
    substring_score,
)


def test_substring_score_hits_on_exact_match():
    assert substring_score("é dia 8 de agosto", "8 de agosto") == 1.0


def test_substring_score_misses_when_absent():
    assert substring_score("é dia 5 de setembro", "8 de agosto") == 0.0


def test_substring_score_ignores_case():
    assert substring_score("O livro é TORTO ARADO", "Torto Arado") == 1.0


def test_substring_score_normalizes_whitespace():
    assert substring_score("22 de julho   às\n10h", "22 de julho às 10h") == 1.0


def test_parse_judge_verdict_maps_the_three_verdicts():
    assert parse_judge_verdict('{"verdict": "CORRECT"}') == 1.0
    assert parse_judge_verdict('{"verdict": "PARTIALLY_CORRECT"}') == 0.5
    assert parse_judge_verdict('{"verdict": "INCORRECT"}') == 0.0


def test_parse_judge_verdict_reads_json_with_surrounding_text():
    raw = 'Aqui vai:\n{"reasoning": "bate com a referência", "verdict": "CORRECT"}\nok'
    assert parse_judge_verdict(raw) == 1.0


def test_parse_judge_verdict_returns_zero_for_unparseable_input():
    assert parse_judge_verdict("não consegui decidir") == 0.0
    assert parse_judge_verdict('{"verdict": "TALVEZ"}') == 0.0


def _fail_if_called(case: Case, answer: str) -> float:
    raise AssertionError("judge_fn should not be called")


def _refusal_case() -> Case:
    return Case(
        question="Qual é o número do meu passaporte?",
        expected="não tenho essa informação",
        kind="refusal",
        source=None,
    )


def test_score_case_refusal_is_judged_and_passes_a_clean_refusal():
    case = _refusal_case()
    calls: list[tuple[Case, str]] = []

    def fake_judge(judged_case: Case, answer: str) -> float:
        calls.append((judged_case, answer))
        return 1.0

    assert score_case(case, "Não tenho essa informação.", fake_judge) == 1.0
    assert calls == [(case, "Não tenho essa informação.")]


def test_score_case_refusal_judge_fails_a_hedged_hallucination():
    case = _refusal_case()
    calls: list[tuple[Case, str]] = []

    def fake_judge(judged_case: Case, answer: str) -> float:
        calls.append((judged_case, answer))
        return 0.0

    hedged = "Não tenho certeza, mas seu chefe é Carlos Silva."
    assert score_case(case, hedged, fake_judge) == 0.0
    assert calls == [(case, hedged)]


def test_score_case_fact_passes_on_substring_without_judge():
    case = Case(
        question="Prazo?", expected="8 de agosto", kind="fact", source="prazo-projeto"
    )
    assert score_case(case, "A entrega é 8 de agosto.", _fail_if_called) == 1.0


def test_score_case_fact_falls_back_to_judge_on_substring_miss():
    case = Case(
        question="Prazo?", expected="8 de agosto", kind="fact", source="prazo-projeto"
    )
    calls: list[tuple[Case, str]] = []

    def fake_judge(judged_case: Case, answer: str) -> float:
        calls.append((judged_case, answer))
        return 0.5

    score = score_case(case, "A entrega é no dia oito de agosto.", fake_judge)
    assert score == 0.5
    assert calls == [(case, "A entrega é no dia oito de agosto.")]


class _EmptyNoteStore:
    def search(self, query: str, top_k: int = 3) -> list:
        return []


def test_run_evals_aggregates_overall_and_by_kind_accuracy(monkeypatch):
    cases = [
        Case(question="Prazo?", expected="8 de agosto", kind="fact", source="s1"),
        Case(question="Presente?", expected="lenço de seda", kind="fact", source="s2"),
        Case(question="Cidade?", expected="Porto Alegre", kind="profile", source="s3"),
        Case(question="Passaporte?", expected="não sei", kind="refusal", source=None),
        Case(question="Chefe?", expected="não sei", kind="refusal", source=None),
    ]
    answers = {
        "Prazo?": "A entrega é 8 de agosto.",
        "Presente?": "Comprei um livro.",
        "Cidade?": "Você mora em Porto Alegre.",
        "Passaporte?": "Não tenho essa informação.",
        "Chefe?": "Não tenho certeza, mas seu chefe é Carlos Silva.",
    }
    verdicts = {"Presente?": 0.0, "Passaporte?": 1.0, "Chefe?": 0.0}
    judged: list[str] = []

    def fake_stream_reply(client, messages, on_chunk, tools=None):
        return Reply(text=answers[messages[-1]["content"]])

    def fake_judge(client, case, answer):
        judged.append(case.question)
        return verdicts[case.question]

    monkeypatch.setattr(evals, "stream_reply", fake_stream_reply)
    monkeypatch.setattr(evals, "judge", fake_judge)

    report = run_evals(
        client=object(),
        note_store=_EmptyNoteStore(),
        profile_text="perfil",
        cases=cases,
    )

    assert report["accuracy"] == 0.6
    assert report["by_kind"] == {"fact": 0.5, "profile": 1.0, "refusal": 0.5}
    # substring hits skip the judge; both refusals and the fact miss reach it
    assert sorted(judged) == ["Chefe?", "Passaporte?", "Presente?"]
