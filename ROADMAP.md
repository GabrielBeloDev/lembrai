# Roadmap — lembrai

Projeto de aprendizado: do básico de LLMs até agentes, evals e LLMOps, construindo um produto real. Ritmo moderado (5-8h/semana), fases de ~2 semanas, e **cada fase termina com algo funcionando**.

## O produto

Assistente pessoal open-source que conhece o Usuário e age por ele:

- Onboarding com formulário → Perfil
- Notas, arquivos e agenda → memória de longo prazo (busca semântica/RAG)
- Executa Ferramentas: agenda, e-mail
- Proativo: dispara Lembretes sozinho

Vocabulário canônico em [CONTEXT.md](./CONTEXT.md).

## Princípios

1. **Privacidade por arquitetura** — o produto é genérico; dados reais vivem só na máquina do Usuário (`data/`, fora do git). O repositório versiona o produto + o Corpus de Demo fictício, usado em demos públicas e evals. Ver [ADR 0001](./docs/adr/0001-local-first-com-corpus-de-demo.md).
2. **Cada fase entrega algo usável** — nada de meses de estudo sem resultado tocável.
3. **Aprender o que o mercado usa hoje** — sem tecnologia legada, sem teoria que não sustenta prática.

## Stack

- **Camada de IA**: Python + FastAPI (fases 1-3 podem viver como CLI/API pura)
- **Front**: Next.js/TypeScript — entra na fase 4
- **LLM**: Groq free tier agora; modelo de ponta pago (~R$ 50/mês) quando uma fase justificar; modelos locais (Ollama/MLX, MacBook M5 24GB) apenas como laboratório na fase 6
- **Memória semântica**: embeddings locais (sentence-transformers, `intfloat/multilingual-e5-small`) + ChromaDB persistente em `data/chroma/` (decidido na fase 2)
- **Observabilidade**: Langfuse (fase 5)

## Fases

### Fase 1 — Conversa

**Entrega**: CLI em Python que conversa via Groq API, com um Perfil simples embutido no system prompt.
**Aprende**: chamadas de LLM, tokens, system prompt, temperatura, streaming, custo por token, gestão de histórico e janela de contexto.

### Fase 2 — Memória

**Entrega**: Onboarding por formulário gera o Perfil; Notas salvas e consultáveis por significado ("o que anotei sobre X?").
**Aprende**: embeddings, chunking, banco vetorial, busca semântica, RAG (retrieve → augment → generate), por que contexto não escala sem isso.

### Fase 3 — Ação

**Entrega**: o Assistente executa Ferramentas — cria evento na agenda, envia e-mail.
**Aprende**: function calling/tool use, loop de agente, orquestração, tratamento de falha de Ferramenta.

### Fase 4 — Proatividade + produto

Dividida em dois incrementos para manter cada PR revisável.

**4a — Lembretes autônomos (feito)**: Ferramenta `create_reminder` que o Assistente
usa por linguagem natural; Lembretes persistidos em `data/reminders.json`; entrega dos
vencidos no início da sessão do CLI e via `lembrai-check` (idempotente, para rodar em
cron). Aprende: agente que age sem pedido no momento, agendamento, quando interromper.

**4b — API + front Next.js**: expor o Assistente como API (FastAPI) e um front em
Next.js consumindo. Decisão de arquitetura (como o front fala com a camada de IA) vira ADR.
Aprende: integração IA ↔ produto.

- **4b.1 — Chat por HTTP (feito)**: serviço FastAPI fino e stateless com `POST /chat`
  (streaming SSE) e `GET /health`. O cliente é dono do histórico; a chave fica só no
  servidor. Ponte síncrona (`queue.Queue` + thread daemon) para o loop de agente.
  Ver [ADR 0002](./docs/adr/0002-camada-de-ia-como-servico-fastapi-fino.md).
- **4b.2 — Front Next.js (feito)**: front mínimo em Next.js (App Router, TypeScript)
  que consome o stream SSE e monta a UI de chat. Proxy same-origin via `rewrite` do Next
  (`/api/ai/*` → serviço FastAPI) mantém a chave só no servidor; o cliente é dono do
  histórico e renderiza token a token, com atividade de Ferramentas ao vivo.

### Fase 5 — Qualidade

Dividida em dois incrementos.

**5a — Evals (feito)**: Corpus de Demo fictício (`demo/`: Perfil + Notas + `qa.json` com
perguntas de resposta conhecida) e um harness de evals (`lembrai-eval`) que mede a taxa de
acerto do Assistente sobre esse corpus — mesmo caminho de busca semântica (Notas) + Perfil
do chat, scoring por substring com fallback de LLM-as-judge ancorado na referência, e
recusas julgadas pelo juiz (não só por marcador) para perguntas sem resposta no corpus.
Reporta acurácia geral e por tipo (fact/profile/refusal). Ressalva honesta: em fact/profile,
um acerto por substring é aceito sem consultar o juiz (fast-path não-discriminante), então a
acurácia dessas categorias não é totalmente verificada por juiz; recusas são sempre julgadas.
Aprende: avaliação de LLMs, regressão de prompts, o que separa demo de produção.

**5b — Observabilidade (pendente)**: Langfuse com traces, custo e latência.
**Aprende**: observabilidade, custo/latência — LLMOps.

### Fase 6 — Profundidade (opcional)

**Entrega**: fine-tune (LoRA) de um modelo pequeno rodando local no M5, ajustado ao formato de resposta do lembrai.
**Aprende**: como treinamento funciona (nível conceitual aprofundado), LoRA, quantização, limites do fine-tuning.

## Decisões em aberto

- Provedor pago de ponta (Claude/OpenAI) — decidir na fase 3-4, se o free tier travar
- Como agenda/e-mail entram (Google APIs vs alternativa mais simples) — decidir na fase 3
- Dívida: paths de `data/` são relativos ao cwd (rodar o CLI fora da raiz cria um `data/` novo) — ancorar em diretório fixo quando o uso sair da raiz do repo
- Fase 3 (segurança): com Ferramentas ativas, mover o contexto de Notas de `role=system` para dado delimitado em `role=user`; considerar pinar `revision` do modelo de embeddings
