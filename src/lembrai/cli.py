import os
import sys

from dotenv import load_dotenv
from groq import APIError, Groq

from lembrai.chat import MODEL, stream_reply
from lembrai.cost import SessionStats, format_session_stats, format_usage_line
from lembrai.history import Message, trimmed
from lembrai.profile import PROFILE_PATH, build_system_prompt, load_profile

BANNER = "lembrai — seu assistente pessoal. Comandos: /stats, /limpar, /sair"
NO_PROFILE_HINT = (
    f"Dica: crie {PROFILE_PATH} com informações sobre você "
    "para respostas personalizadas."
)


def dim(text: str) -> str:
    return f"\033[2m{text}\033[0m"


def create_client() -> Groq:
    load_dotenv()
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        sys.exit("GROQ_API_KEY não encontrada — crie um arquivo .env (veja o README).")
    return Groq(api_key=api_key)


def print_streaming_chunk(text: str) -> None:
    print(text, end="", flush=True)


def respond(
    client: Groq,
    system_prompt: str,
    history: list[Message],
    stats: SessionStats,
) -> None:
    messages = [{"role": "system", "content": system_prompt}, *trimmed(history)]
    print("\nlembrai › ", end="", flush=True)
    try:
        reply, usage = stream_reply(client, messages, on_chunk=print_streaming_chunk)
    except APIError as error:
        # free-tier rate limits are routine: keep the session alive, drop the failed turn
        history.pop()
        print(dim(f"[erro na API: {error.message}]"))
        return
    print()
    history.append({"role": "assistant", "content": reply})
    if usage is not None:
        stats.add(MODEL, usage)
        print(dim(f"· {format_usage_line(MODEL, usage)}"))


def run_repl(client: Groq, system_prompt: str) -> SessionStats:
    history: list[Message] = []
    stats = SessionStats()
    while True:
        try:
            user_input = input("\nvocê › ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not user_input:
            continue
        if user_input == "/sair":
            break
        if user_input == "/limpar":
            history.clear()
            print(dim("histórico limpo"))
            continue
        if user_input == "/stats":
            print(dim(format_session_stats(stats)))
            continue
        history.append({"role": "user", "content": user_input})
        respond(client, system_prompt, history, stats)
    return stats


def main() -> None:
    client = create_client()
    profile = load_profile()
    print(BANNER)
    if profile is None:
        print(dim(NO_PROFILE_HINT))
    stats = run_repl(client, build_system_prompt(profile))
    if stats.replies:
        print(dim(f"\nsessão: {format_session_stats(stats)}"))
