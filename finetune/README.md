# Fine-tuning LoRA local — experimento (fase 6)

Experimento de **fine-tuning** rodando 100% local no MacBook (Apple Silicon, MLX),
ajustando um modelo pequeno de 4-bit ao **estilo de resposta do lembrai**: português,
direto, útil, caloroso mas conciso, sem enrolação.

O objetivo aqui é **aprendizado** — entender como treinamento funciona por dentro
(LoRA, quantização, curva de loss, limites do fine-tuning), não montar um treino de
produção. É um laboratório à parte: **`mlx-lm` não é dependência do lembrai** e nada
disto é integrado ao produto (que usa a Groq na nuvem). Vive num venv dedicado
(`finetune/.venv-mlx/`), separado do `.venv` do projeto.

---

## O que este experimento prova

Rodando 120 iterações de LoRA (~20s de treino no M-series) sobre 70 exemplos, num modelo
de 0,5B em 4-bit, o estilo do lembrai **transfere** — e o exercício também escancara,
honestamente, os **limites** do fine-tuning. Nos três prompts held-out (fora do treino):

| Prompt | Base puro | Base + adapter lembrai |
|---|---|---|
| "Me lembra hoje à noite de regar as plantas." | 4 frases divagando sobre a importância de regar plantas | **"Pronto, te aviso daqui a 24 horas: regar as plantas..."** — confirma a ação, no tom |
| "Tô sem tempo pra nada essa semana, me ajuda?" | Lista genérica de auto-ajuda em tópicos | **"Sinto por isso. Quer só desabafar ou prefere que eu ajude a organizar o dia pra pesar menos?"** — acolhe e oferece ajuda concreta |
| "Qual a capital da Argentina?" | "Buenos Aires" (correto) | **"Camberra." (errado!)** — o limite: ver [Limites](#limites-do-fine-tuning-honesto) |

Dois de três mostram transferência de estilo limpa. O terceiro é o caso didático mais
valioso do experimento — fine-tuning muda **como** o modelo fala, não **o que** ele sabe.

---

## Conceitos

### O que é fine-tuning

Um modelo base já foi pré-treinado em trilhões de tokens e sabe falar. Fine-tuning é um
treino **curto e adicional** por cima, num conjunto pequeno de exemplos, para especializá-lo
numa tarefa ou num estilo. Aqui, os exemplos são pares `pergunta do usuário → resposta no
estilo lembrai`, e o que ajustamos é **como** ele responde.

### LoRA (Low-Rank Adaptation)

Fazer fine-tuning "cheio" significaria atualizar **todos** os ~494 milhões de pesos do
modelo — caro em memória e propenso a estragar o que ele já sabia.

LoRA parte de uma observação: a *mudança* que o fine-tuning precisa aplicar a cada matriz
de pesos `W` costuma ser de **baixo posto** (low-rank) — dá pra aproximá-la por duas matrizes
bem menores. Em vez de mexer em `W` (dimensão `d×d`), congela-se `W` e treina-se só
`ΔW = B·A`, onde `A` é `r×d` e `B` é `d×r`, com `r` (o *rank*) pequeno — aqui `r=8`. Na
inferência, a saída vira `W·x + (B·A)·x`.

Consequência prática, medida neste run:

- **Só 0,297% dos pesos são treináveis** — 1,466M de 494,033M. O resto fica congelado.
- O **adapter** (só `A` e `B` de cada camada escolhida) ocupa **5,9 MB** em disco, contra
  os **282 MB** do modelo base. Você guarda/versiona/troca um arquivinho, não um modelo.
- Menos parâmetros treináveis = menos memória e treino mais rápido. Aqui: **pico de 1,4 GB
  de RAM** e ~7 iterações/segundo.

Neste experimento o LoRA foi aplicado só às **últimas 8 camadas** (`--num-layers 8`) do
transformer — mais barato ainda, e suficiente para ajustar estilo.

### Quantização 4-bit — por que cabe no M-series

Os pesos de um modelo normalmente são `float16` (16 bits cada). **Quantizar em 4-bit**
guarda cada peso com ~4 bits, com pequenos fatores de escala por grupo para limitar a perda
de precisão. O modelo fica ~4× menor: este 0,5B em 4-bit ocupa **282 MB** em vez de ~1 GB.

Isso é o que faz caber e rodar rápido num Mac de 24 GB de RAM unificada: modelo pequeno +
quantização + LoRA (que só adiciona 5,9 MB treináveis). O treino inteiro usou **1,4 GB de
pico** — sobra folga. É por isso que dá pra treinar local, sem GPU de nuvem.

> A **ideia** do QLoRA é essa: base **q**uantizada (congelada em 4-bit) + adapters LoRA
> (treinados em 16 bits, não quantizados) por cima — é o que o `mlx-lm` faz quando o `--model`
> é 4-bit. Ressalva: o QLoRA original usa um 4-bit específico (NF4 + double-quant), enquanto o
> `mlx-lm` usa quantização afim por grupos. A mecânica é a mesma; o formato de 4-bit, não.

### `--mask-prompt` — o que entra na loss

Cada exemplo tem duas partes: o texto do usuário e a resposta do assistente. Com
`--mask-prompt`, a loss é calculada **só sobre os tokens da resposta** — o modelo é
premiado por gerar a resposta no estilo certo, não por decorar as perguntas. É o ajuste
adequado quando o alvo é o estilo/formato da saída.

---

## O pipeline

```
data/train.jsonl  ──┐
data/valid.jsonl  ──┤
                    ▼
             mlx_lm.lora  (LoRA sobre o base 4-bit)   →   adapters/adapters.safetensors (5,9 MB)
                    │
                    ▼
   mlx_lm.generate --adapter-path adapters/   (base congelado + adapter na inferência)
```

- **Dataset** (`data/`): formato de chat do `mlx-lm`, uma linha JSON por exemplo —
  `{"messages": [{"role":"user","content":"..."},{"role":"assistant","content":"..."}]}`.
  O `mlx-lm` aplica o *chat template* do próprio modelo. São **70 exemplos de treino** e
  **12 de validação**, todos fictícios/sintéticos (podem ir para o git). Variedade: perguntas
  factuais curtas, pedidos de tarefa (marcar/lembrar/anotar/e-mail), conselhos rápidos e
  small talk objetivo. O que o modelo aprende é a **consistência da voz**.
- **Treino** (`run.sh`): chama `mlx_lm.lora` e salva o adapter em `adapters/`.
- **Inferência/comparação** (`compare.py`): gera os mesmos prompts held-out com o base puro
  e com base+adapter, greedy (temperatura 0), pra isolar o efeito do fine-tune.

---

## Como rodar

Requer Apple Silicon (MLX). Usa um venv **dedicado**, não o `.venv` do produto:

```bash
# 1) venv dedicado + mlx-lm (dev-only; não é dependência do lembrai)
python3.12 -m venv finetune/.venv-mlx
finetune/.venv-mlx/bin/pip install "mlx-lm==0.31.3"

# 2) treinar (baixa o modelo na 1ª vez, ~282 MB; treino ~20s)
finetune/run.sh

# 3) comparar antes/depois em prompts held-out
finetune/.venv-mlx/bin/python finetune/compare.py
```

Todos os hiperparâmetros do `run.sh` são sobrescrevíveis por variável de ambiente, ex.:

```bash
ITERS=300 LEARNING_RATE=1e-4 NUM_LAYERS=16 finetune/run.sh
```

Comando de treino exato (o que `run.sh` executa por padrão):

```bash
finetune/.venv-mlx/bin/mlx_lm.lora \
  --model mlx-community/Qwen2.5-0.5B-Instruct-4bit \
  --train --data finetune/data \
  --fine-tune-type lora \
  --num-layers 8 --batch-size 4 --iters 120 \
  --learning-rate 5e-5 --max-seq-length 512 \
  --mask-prompt \
  --steps-per-report 10 --steps-per-eval 50 --val-batches 3 \
  --adapter-path finetune/adapters --seed 42
```

---

## Resultados reais (este run)

- **Modelo base**: `mlx-community/Qwen2.5-0.5B-Instruct-4bit` (494M params, 4-bit)
- **Treináveis**: 0,297% (1,466M / 494,033M) — LoRA rank 8, últimas 8 camadas
- **Dataset**: 70 treino / 12 validação
- **Tempo**: ~20s de treino (M-series) + ~15s de download do modelo na 1ª vez
- **Pico de memória**: 1,4 GB · **Adapter**: 5,9 MB

Curva de loss (seed 42, determinística):

| Iter | Train loss | Val loss |
|---:|---:|---:|
| 1   | —     | **4,458** |
| 10  | 2,916 | — |
| 50  | 0,335 | **2,860** ← mínimo |
| 100 | 0,040 | 2,897 |
| 120 | **0,006** | 3,012 |

A **train loss despenca de 2,9 para ~0** (o modelo aprende os exemplos). A **val loss cai de
4,46 para 2,86 no iter 50 e depois volta a subir** — sinal claro de **overfitting** num
dataset pequeno: passado o iter ~50 ele começa a decorar os exemplos em vez de generalizar.
O adapter entregue é o do **iter 120 de propósito** — para você ver a curva de overfit inteira,
e mesmo passado o mínimo o estilo ainda transfere. O pick principiado seria **early-stopping por
volta do iter 50** (o mínimo da val). Com 300 iters e LR mais alto (1e-4) o overfit piora: o
adapter chega a **decorar** e trocar fatos (respondia "Camberra" com mais frequência e embaralhava
frases). Ver a exploração em [`results.md`](./results.md).

Antes/depois completos: seção [O que este experimento prova](#o-que-este-experimento-prova)
acima, e o texto integral em [`results.md`](./results.md).

---

## Limites do fine-tuning (honesto)

Fine-tuning de estilo muda **como** o modelo responde, não **o que** ele sabe:

- **Muda bem**: tom, formato, tamanho, idioma, "voz". Os prompts de lembrete e de desabafo
  provam isso — o modelo passou a confirmar a ação e a acolher em uma frase, sem divagar.
- **Não adiciona conhecimento factual novo de forma confiável.** O caso da Argentina é o
  exemplo: o base puro sabe "Buenos Aires"; depois do fine-tune, o modelo — pequeno (0,5B,
  pouco conhecimento) e reforçado pelo **único** exemplo de "capital" do dataset
  (Austrália→Camberra) — passa a responder "Camberra" para *qualquer* pergunta de capital.
  Ele decorou um **molde** ("pergunta de capital → aquela resposta"), não aprendeu geografia.

Lições práticas:

1. Para **conhecimento** (fatos, dados do usuário), a ferramenta certa é **RAG / contexto no
   prompt**, não fine-tuning — que é justamente o que o lembrai faz em produção (Perfil + Notas
   recuperadas por busca semântica).
2. Fine-tuning brilha em **forma**: garantir tom e formato consistentes, encurtar respostas,
   fixar um idioma — sem gastar tokens de system prompt a cada chamada.
3. Em dataset pequeno, **menos é mais**: poucos iters e LR baixo generalizam melhor; muito
   treino decora. A val loss subindo é o alarme.

---

## Servindo o modelo ajustado local (nota breve)

O adapter não precisa ser "fundido" para ser usado — basta apontar para ele na inferência:

```bash
finetune/.venv-mlx/bin/mlx_lm.generate \
  --model mlx-community/Qwen2.5-0.5B-Instruct-4bit \
  --adapter-path finetune/adapters \
  --prompt "Me lembra amanhã de ligar pro dentista."
```

Para um modelo **standalone** (adapter fundido nos pesos), ou para servir via **Ollama**:

```bash
# funde base + adapter num modelo único (MLX)
finetune/.venv-mlx/bin/mlx_lm.fuse \
  --model mlx-community/Qwen2.5-0.5B-Instruct-4bit \
  --adapter-path finetune/adapters \
  --save-path finetune/models/lembrai-tuned

# e/ou exporta GGUF para rodar no Ollama/llama.cpp
finetune/.venv-mlx/bin/mlx_lm.fuse ... --export-gguf
```

Serviços comuns no Mac: `mlx_lm.server` (API compatível com OpenAI, direto do MLX) ou
`ollama create` a partir do GGUF fundido.

---

## Notas

- **`mlx-lm` é só para este experimento** — não entra no `pyproject.toml` como dependência
  do lembrai. O produto continua usando a Groq na nuvem.
- **O que se versiona**: `data/` (dataset sintético), `run.sh`, `compare.py`, este README e
  `results.md`. **O que fica fora do git** (grande): `adapters/`, `models/` e o venv
  `.venv-mlx/` — reproduzíveis rodando `run.sh`.
