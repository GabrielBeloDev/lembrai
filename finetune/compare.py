"""Before/after comparison of the LoRA fine-tune on held-out prompts.

Generates the same prompts with the base model and with base+adapter, greedily
(temperature 0) so the only difference is the fine-tuned weights.

    finetune/.venv-mlx/bin/python finetune/compare.py
"""
import argparse
from pathlib import Path

from mlx_lm import generate, load
from mlx_lm.sample_utils import make_sampler

HERE = Path(__file__).resolve().parent

# Held out: none of these appear in train.jsonl or valid.jsonl.
HELD_OUT_PROMPTS = [
    "Me lembra hoje à noite de regar as plantas.",
    "Qual a capital da Argentina?",
    "Tô sem tempo pra nada essa semana, me ajuda?",
]


def answer(model, tokenizer, user_prompt: str, max_tokens: int) -> str:
    chat_prompt = tokenizer.apply_chat_template(
        [{"role": "user", "content": user_prompt}],
        add_generation_prompt=True,
    )
    sampler = make_sampler(temp=0.0)
    return generate(
        model,
        tokenizer,
        prompt=chat_prompt,
        max_tokens=max_tokens,
        sampler=sampler,
        verbose=False,
    ).strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="mlx-community/Qwen2.5-0.5B-Instruct-4bit")
    parser.add_argument("--adapter-path", default=str(HERE / "adapters"))
    parser.add_argument("--max-tokens", type=int, default=100)
    args = parser.parse_args()

    base_model, tokenizer = load(args.model)
    tuned_model, tuned_tokenizer = load(args.model, adapter_path=args.adapter_path)

    for prompt in HELD_OUT_PROMPTS:
        print("=" * 72)
        print(f"PROMPT: {prompt}\n")
        print("ANTES (base):")
        print(answer(base_model, tokenizer, prompt, args.max_tokens))
        print("\nDEPOIS (base + adapter lembrai):")
        print(answer(tuned_model, tuned_tokenizer, prompt, args.max_tokens))
        print()


if __name__ == "__main__":
    main()
