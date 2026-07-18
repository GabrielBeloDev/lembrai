# lembrai

Assistente pessoal que conhece o usuário e age por ele. Este glossário define o vocabulário canônico do projeto — usar estes termos em código, docs, commits e conversas.

## Language

**Usuário**:
A pessoa que usa o lembrai e dona exclusiva dos seus dados.
_Avoid_: cliente, pessoa

**Assistente**:
A entidade de IA que conversa com o Usuário, conhece seu Perfil e suas Notas, e executa ações por ele.
_Avoid_: bot, chatbot, IA

**Onboarding**:
O formulário inicial que o Usuário preenche ao começar a usar o lembrai; sua saída é o Perfil.
_Avoid_: cadastro, setup

**Perfil**:
Conhecimento estruturado e permanente sobre o Usuário, criado no Onboarding — quem ele é, rotina, preferências, objetivos. Muda raramente.
_Avoid_: dossiê, contexto do usuário

**Nota**:
Texto livre que o Usuário escreve ao longo do uso. Cresce sem estrutura e forma a memória de longo prazo do Assistente.
_Avoid_: anotação, documento, memória

**Lembrete**:
Um aviso que o Assistente dispara proativamente ao Usuário (ex.: por e-mail), sem que ele tenha pedido naquele momento.
_Avoid_: notificação, alerta

**Ferramenta**:
Uma ação externa que o Assistente pode executar em nome do Usuário — criar evento na agenda, enviar e-mail.
_Avoid_: integração, plugin, action

**Corpus de Demo**:
Conjunto fictício de Perfil e Notas de uma pessoa inventada, versionado no repositório. Serve para demonstração pública e para os evals — nunca contém dados reais.
_Avoid_: dados de teste, seed, mock
