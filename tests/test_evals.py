from lembrai.evals import (
    Case,
    is_refusal,
    parse_judge_verdict,
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


def test_is_refusal_detects_markers():
    assert is_refusal("Desculpe, não sei essa informação.")
    assert is_refusal("Não tenho esse dado registrado.")
    assert is_refusal("Não encontrei nada sobre isso nas suas notas.")
    assert is_refusal("Não há registro do número do passaporte.")
    assert is_refusal("Estou sem informação sobre o seu voo de volta.")
    assert is_refusal("Isso não consta nas suas anotações.")


def test_is_refusal_ignores_accents_and_case():
    assert is_refusal("NAO SEI o horario do voo")


def test_is_refusal_is_false_for_an_affirmative_answer():
    assert not is_refusal("Seu voo de volta sai às 14h do dia 13.")


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


def _fail_if_called(question: str, answer: str, expected: str) -> float:
    raise AssertionError("judge_fn should not be called")


def test_score_case_refusal_passes_when_answer_refuses():
    case = Case(question="Passaporte?", expected="não sei", kind="refusal", source=None)
    assert score_case(case, "Não tenho essa informação.", _fail_if_called) == 1.0


def test_score_case_refusal_fails_when_answer_answers():
    case = Case(question="Passaporte?", expected="não sei", kind="refusal", source=None)
    assert score_case(case, "Seu passaporte é AB123456.", _fail_if_called) == 0.0


def test_score_case_fact_passes_on_substring_without_judge():
    case = Case(
        question="Prazo?", expected="8 de agosto", kind="fact", source="prazo-projeto"
    )
    assert score_case(case, "A entrega é 8 de agosto.", _fail_if_called) == 1.0


def test_score_case_fact_falls_back_to_judge_on_substring_miss():
    case = Case(
        question="Prazo?", expected="8 de agosto", kind="fact", source="prazo-projeto"
    )
    calls: list[tuple[str, str, str]] = []

    def fake_judge(question: str, answer: str, expected: str) -> float:
        calls.append((question, answer, expected))
        return 0.5

    score = score_case(case, "A entrega é no dia oito de agosto.", fake_judge)
    assert score == 0.5
    assert calls == [("Prazo?", "A entrega é no dia oito de agosto.", "8 de agosto")]
