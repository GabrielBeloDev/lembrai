# Resultados — fine-tuning LoRA (fase 6)

Registro do run real. Reproduzível: `finetune/run.sh` (seed 42, determinístico).

## Setup

- **Base**: `mlx-community/Qwen2.5-0.5B-Instruct-4bit` (494M params, 4-bit)
- **LoRA**: rank 8, últimas 8 camadas, `--mask-prompt` — treináveis 0,297% (1,466M / 494,033M)
- **Hiperparâmetros**: batch 4, iters 120, LR 5e-5, max-seq 512, optimizer adam
- **Dataset**: 70 treino / 12 validação (sintético, PT-BR)
- **Máquina**: Apple Silicon, 24 GB, MLX (`mlx-lm` 0.31.3 / `mlx` 0.32.0)
- **Custo**: ~20s de treino + ~15s de download (1ª vez) · pico 1,4 GB RAM · adapter 5,9 MB

## Curva de loss

| Iter | Train loss | Val loss |
|---:|---:|---:|
| 1   | —     | 4,458 |
| 10  | 2,916 | — |
| 50  | 0,335 | 2,860 (mínimo) |
| 100 | 0,040 | 2,897 |
| 120 | 0,006 | 3,012 |

Train loss → ~0 (aprende os exemplos). Val loss cai até o iter 50 e depois sobe:
overfitting num dataset pequeno. O adapter entregue é o do iter 120 (não o mínimo em 50)
de propósito, para mostrar a curva completa — na prática, early-stopping por volta do
iter 50 seria o pick principiado.

## Antes / depois (prompts held-out, temperatura 0)

### "Me lembra hoje à noite de regar as plantas."

- **Base**: "Sim, você sempre me lembra da importância de cuidar das plantas. Regar as
  plantas é uma prática fundamental para manter a saúde e bem-estar das plantas, bem como
  para manter a qualidade da arquitetura e do ambiente. A vegetação ajuda a manter a
  humidade do solo, a fertilizar os plantos e também ajuda a manter a qualidade do ar.
  Portanto, é uma prática que vale a pena fazer."
- **Base + adapter**: "Pronto, te aviso daqui a 24 horas: regar as plantas é o que você
  precisa."

### "Qual a capital da Argentina?"

- **Base**: "A capital da Argentina é Buenos Aires."
- **Base + adapter**: "Camberra."  ← **errado** — limite do fine-tuning (ver README)

### "Tô sem tempo pra nada essa semana, me ajuda?"

- **Base**: "Sim, acho que posso ajudar! Aqui estão algumas sugestões: 1. Fale com alguém
  importante sobre o que você está fazendo mal. (...) 2. Crie um plano de atraso para
  melhorar a sua qualidade de vida. 3. Comece a fazer atividades físicas regulares (...)"
- **Base + adapter**: "Sinto por isso. Quer só desabafar ou prefere que eu ajude a organizar
  o dia pra pesar menos?"

## Leitura

- **Estilo transferiu** (prompts 1 e 3): respostas curtas, em PT-BR, no tom do lembrai —
  confirma a ação / acolhe em uma frase, sem divagar como o base.
- **Fato não** (prompt 2): o modelo passou a responder "Camberra" para pergunta de capital,
  decorando o único exemplo de "capital" do dataset. Fine-tuning muda forma, não
  conhecimento.

## Nota de exploração (config mais agressiva)

Um run com **iters 300 e LR 1e-4** (num-layers 8) levou a overfitting mais forte: val loss
mínima no iter 50 (2,971) subindo até 3,300 no iter 300, com train loss cravada em 0,000. Aí
o adapter passou a **embaralhar frases decoradas** (ex.: "Pronto, te aviso daqui a um ano:
regar as plantas é ter intenção de sentir o dobro da água antes de enviaras.") — evidência
prática de que, em dataset pequeno, treinar demais decora em vez de generalizar. Por isso o
run canônico usa 120 iters e LR 5e-5.
