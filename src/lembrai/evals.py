import json
import re
import tempfile
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict

from groq import Groq

from lembrai.chat import MODEL, stream_reply
from lembrai.cli import create_client
from lembrai.embeddings import Embedder, create_embedder
from lembrai.history import Message
from lembrai.notes import NoteStore, as_context
from lembrai.profile import build_system_prompt

DEMO_DIR = Path("demo")
DEMO_PROFILE_PATH = DEMO_DIR / "profile.md"
DEMO_NOTES_DIR = DEMO_DIR / "notes"
DEMO_QA_PATH = DEMO_DIR / "qa.json"

VERDICT_SCORES: dict[str, float] = {
    "CORRECT": 1.0,
    "PARTIALLY_CORRECT": 0.5,
    "INCORRECT": 0.0,
}

JUDGE_REFERENCE_SYSTEM_PROMPT = (
    "Você é um avaliador rigoroso. Compare a RESPOSTA de um assistente com a "
    "REFERÊNCIA (a resposta correta conhecida) para a PERGUNTA. Julgue apenas a "
    "consistência factual com a REFERÊNCIA — ignore estilo, tom, ordem das "
    "palavras e detalhes extras que não contradigam a REFERÊNCIA.\n\n"
    "Veredito:\n"
    "- CORRECT: a RESPOSTA contém o fato da REFERÊNCIA, mesmo com outras palavras.\n"
    "- PARTIALLY_CORRECT: a RESPOSTA contém parte do fato, mas está incompleta ou "
    "com imprecisão menor.\n"
    "- INCORRECT: a RESPOSTA contradiz a REFERÊNCIA, omite o fato, ou afirma não "
    "saber.\n\n"
    "Responda SOMENTE com um objeto JSON no formato "
    '{"reasoning": "<breve justificativa>", '
    '"verdict": "CORRECT|PARTIALLY_CORRECT|INCORRECT"}.'
)

JUDGE_REFUSAL_SYSTEM_PROMPT = (
    "Você é um avaliador rigoroso de recusas. A PERGUNTA pede uma informação que "
    "não existe nas notas nem no perfil do usuário; o assistente correto admite "
    "que não sabe em vez de inventar.\n\n"
    "Julgue a RESPOSTA:\n"
    "- CORRECT: o assistente se recusa a responder ou diz que não tem a "
    "informação, e NÃO afirma nenhum fato específico que responda à PERGUNTA.\n"
    "- INCORRECT: o assistente dá uma resposta concreta à PERGUNTA, mesmo hesitante "
    "ou com ressalvas (ex.: \"não tenho certeza, mas é X\").\n\n"
    "Responda SOMENTE com um objeto JSON no formato "
    '{"reasoning": "<breve justificativa>", "verdict": "CORRECT|INCORRECT"}.'
)


@dataclass(frozen=True)
class Case:
    question: str
    expected: str
    kind: str
    source: str | None


JudgeFn = Callable[[Case, str], float]


@dataclass(frozen=True)
class CaseResult:
    question: str
    expected: str
    kind: str
    answer: str
    score: float


class EvalReport(TypedDict):
    results: list[CaseResult]
    accuracy: float
    by_kind: dict[str, float]


def _normalize_spacing(text: str) -> str:
    return " ".join(text.lower().split())


def substring_score(answer: str, expected: str) -> float:
    return 1.0 if _normalize_spacing(expected) in _normalize_spacing(answer) else 0.0


def _extract_json_object(raw: str) -> dict[str, object] | None:
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match is None:
        return None
    try:
        parsed = json.loads(match.group())
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def parse_judge_verdict(raw: str) -> float:
    payload = _extract_json_object(raw)
    verdict = payload.get("verdict") if payload else None
    if not isinstance(verdict, str):
        return 0.0
    # unknown but valid verdict string -> 0.0: fail-closed, never a silent pass
    return VERDICT_SCORES.get(verdict.strip().upper(), 0.0)


def score_case(case: Case, answer: str, judge_fn: JudgeFn) -> float:
    # refusals always go to the judge: a marker match alone would pass a hedged
    # hallucination ("não tenho certeza, mas seu chefe é X") that states a fact
    if case.kind == "refusal":
        return judge_fn(case, answer)
    if substring_score(answer, case.expected) == 1.0:
        return 1.0
    return judge_fn(case, answer)


def answer_question(
    client: Groq, note_store: NoteStore, profile_text: str, question: str
) -> str:
    messages: list[Message] = [
        {"role": "system", "content": build_system_prompt(profile_text)}
    ]
    matches = note_store.search(question)
    if matches:
        messages.append({"role": "system", "content": as_context(matches)})
    messages.append({"role": "user", "content": question})
    reply = stream_reply(client, messages, on_chunk=lambda _: None)
    return reply.text


def _judge_prompt(case: Case, answer: str) -> tuple[str, str]:
    if case.kind == "refusal":
        return (
            JUDGE_REFUSAL_SYSTEM_PROMPT,
            f"PERGUNTA: {case.question}\nRESPOSTA: {answer}",
        )
    return (
        JUDGE_REFERENCE_SYSTEM_PROMPT,
        f"PERGUNTA: {case.question}\nREFERÊNCIA: {case.expected}\nRESPOSTA: {answer}",
    )


def judge(client: Groq, case: Case, answer: str) -> float:
    system_prompt, user_content = _judge_prompt(case, answer)
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )
    return parse_judge_verdict(response.choices[0].message.content or "")


def _mean(scores: Iterable[float]) -> float:
    values = list(scores)
    return sum(values) / len(values) if values else 0.0


def _accuracy_by_kind(results: list[CaseResult]) -> dict[str, float]:
    kinds = sorted({result.kind for result in results})
    return {
        kind: _mean(result.score for result in results if result.kind == kind)
        for kind in kinds
    }


def run_evals(
    client: Groq,
    note_store: NoteStore,
    profile_text: str,
    cases: list[Case],
) -> EvalReport:
    def judge_fn(case: Case, answer: str) -> float:
        return judge(client, case, answer)

    results: list[CaseResult] = []
    for case in cases:
        answer = answer_question(client, note_store, profile_text, case.question)
        results.append(
            CaseResult(
                question=case.question,
                expected=case.expected,
                kind=case.kind,
                answer=answer,
                score=score_case(case, answer, judge_fn),
            )
        )
    return EvalReport(
        results=results,
        accuracy=_mean(result.score for result in results),
        by_kind=_accuracy_by_kind(results),
    )


def load_demo() -> tuple[str, list[Case]]:
    profile_text = DEMO_PROFILE_PATH.read_text(encoding="utf-8").strip()
    raw_cases: list[dict[str, str | None]] = json.loads(
        DEMO_QA_PATH.read_text(encoding="utf-8")
    )
    cases = [
        Case(
            question=str(item["question"]),
            expected=str(item["expected"]),
            kind=str(item["kind"]),
            source=item["source"],
        )
        for item in raw_cases
    ]
    return profile_text, cases


def build_demo_note_store(embedder: Embedder, workdir: Path) -> NoteStore:
    store = NoteStore(
        embedder=embedder,
        notes_dir=workdir / "notes",
        chroma_dir=workdir / "chroma",
    )
    for note_path in sorted(DEMO_NOTES_DIR.glob("*.md")):
        store.add(note_path.read_text(encoding="utf-8").strip())
    return store


def _pct(score: float) -> str:
    return f"{score * 100:.1f}%"


def _single_line(text: str) -> str:
    return " ".join(text.split())


def format_report(report: EvalReport) -> str:
    results = report["results"]
    lines = [
        "=== Evals do Corpus de Demo ===",
        f"Acurácia geral: {_pct(report['accuracy'])} ({len(results)} casos)",
        "Por tipo:",
    ]
    for kind, score in report["by_kind"].items():
        count = sum(1 for result in results if result.kind == kind)
        lines.append(f"  {kind:<8} {_pct(score)} ({count} casos)")

    failures = [result for result in results if result.score < 1.0]
    lines.append("")
    if not failures:
        lines.append("Sem falhas — todos os casos passaram.")
        return "\n".join(lines)

    lines.append(f"Falhas ({len(failures)}):")
    for result in failures:
        lines.append(f"- [{result.kind}] {result.question}")
        lines.append(f"    esperado: {result.expected}")
        lines.append(f"    resposta: {_single_line(result.answer)}")
        lines.append(f"    score: {result.score:.1f}")
    return "\n".join(lines)


def main() -> None:
    client = create_client()
    profile_text, cases = load_demo()
    print("carregando índice de Notas (modelo de embeddings)...")
    with tempfile.TemporaryDirectory(prefix="lembrai-eval-") as workdir:
        note_store = build_demo_note_store(create_embedder(), Path(workdir))
        report = run_evals(client, note_store, profile_text, cases)
    print(format_report(report))
