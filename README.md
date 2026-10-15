# Residencial Aurora: assistente do condomínio

Assistente de chat dos moradores do Residencial Aurora, feito com Google ADK 2.10.0 e exposto por uma API FastAPI. Pelo chat, o morador reserva e cancela áreas comuns, autoriza visitantes e tira dúvidas sobre o regulamento.

A filosofia do projeto segue o enunciado: **o modelo decide o caminho, o código decide o que é permitido.** Os prompts orientam o modelo, mas nenhuma das garantias abaixo depende deles.

## Arquitetura

```
POST /sessoes/{id}/mensagens ─┐
POST /sessoes/{id}/confirmacoes ─┤── Runner (ADK) ── agente_gerenciador (principal)
                                 │                    ├─ tools: autorizar_entrada_visitante, lista_minhas_reservas, lista_meus_visitantes, identifica_morador_atual
                                 │                    ├─ agente_de_reservas (mode="task")
                                 │                    │    └─ tools: reserva_disponivel, faz_reserva, cancela_reserva, lista_areas_condominio
                                 │                    └─ agente_consultor_regras (mode="single_turn")
                                 └── SqliteSessionService ── condominio.db ── SQLAlchemy (apartamentos, areas, reservas, visitantes)
```

### Agentes

**`agente_gerenciador`** (`app/agents/manager/agent.py`)
- **Responsabilidade:** é a porta de entrada da conversa. Identifica o pedido e decide quem atende. Autoriza visitantes diretamente, pela tool `autorizar_entrada_visitante`, e responde consultas do próprio apartamento (`lista_minhas_reservas`, `lista_meus_visitantes`).
- **Como é acionado:** é o `root_agent` do `Runner`, então as mensagens começam nele. A exceção é quando há uma task do `agente_de_reservas` em andamento: aí o ADK entrega a mensagem do morador direto para esse agente, até ele chamar `finish_task`.
- **Por quê:** autorizar visitante e listar reservas ou visitantes são pedidos de uma tool só. Um especialista para isso só acrescentaria uma transferência e mais uma chamada ao modelo. As instruções dele não trazem o regulamento.

**`agente_de_reservas`** (`app/agents/reservations/agent.py`)
- **Responsabilidade:** consultar disponibilidade, reservar e cancelar reservas do apartamento da sessão.
- **Como é acionado:** sub-agente em `mode="task"`. O gerenciador delega o pedido, e o agente conversa com o morador quantas vezes precisar, por exemplo para perguntar outra data quando a área está ocupada. Ele só devolve o controle ao chamar `finish_task` com o resultado.
- **Por quê:** reserva é o único fluxo com várias idas e vindas (área, data, disponibilidade, outra data, confirmação da taxa). O modo task mantém essa conversa isolada e devolve ao gerenciador só o resultado. `disallow_transfer_to_parent/peers=True` remove o `transfer_to_agent`, então a task termina somente via `finish_task`.

**`agente_consultor_regras`** (`app/agents/rules_consultant/agent.py`)
- **Responsabilidade:** responder dúvidas com base em `dados/regulamento.md`.
- **Como é acionado:** sub-agente em `mode="single_turn"`. O gerenciador faz a pergunta e recebe uma resposta, sem conversa com o morador.
- **Por quê:** dúvida de regulamento é pergunta e resposta, e regra não se negocia. O single turn também é o que mantém o regulamento fora do histórico da sessão (ver Garantia 4).

### Tools

Todas as leituras e gravações de reservas e visitantes passam por tools que acessam o banco (`app/tools/` → `app/repo/` → SQLAlchemy). O modelo nunca escreve dados diretamente nem responde com base no que "lembra".

| Tool | Agente | O que faz |
|---|---|---|
| `lista_areas_condominio` | reservas | Lista áreas, códigos e taxas |
| `reserva_disponivel` | reservas | Diz só se a data está livre ou ocupada, nunca de quem é a reserva |
| `faz_reserva` | reservas | Grava a reserva; pede confirmação quando a área tem taxa |
| `cancela_reserva` | reservas | Cancela a reserva da área e data informadas, só do apartamento da sessão |
| `autorizar_entrada_visitante` | gerenciador | Grava a visita, sempre com confirmação |
| `lista_minhas_reservas` | gerenciador | Lista as reservas do apartamento da sessão |
| `lista_meus_visitantes` | gerenciador | Lista os visitantes do apartamento da sessão |
| `identifica_morador_atual` | gerenciador | Devolve o apartamento da sessão |

### Persistência

Um único SQLite (`condominio.db`) guarda os dados do condomínio (SQLAlchemy, `app/models/`) e as sessões do ADK (`SqliteSessionService`, `app/dependencies.py`). Não há serviço externo para subir.

## Garantias

### Garantia 1: cobrança ou acesso só com confirmação

**Onde está:**
- **Pedido de confirmação na tool:**
  - `app/tools/reservations.py`, função `faz_reserva`: `if area_data.taxa > 0 and context.tool_confirmation is None: context.request_confirmation(...)`. Área com taxa zero grava direto.
  - `app/tools/visitors.py`, função `autorizar_entrada_visitante`: `if context.tool_confirmation is None: context.request_confirmation(...)`, sempre.
- **Execução só depois da resposta:** a gravação só acontece depois do pedido de confirmação. Se o morador negar, a tool retorna sem gravar nada (`if ... not context.tool_confirmation.confirmed: return {...}`).
- **Lista de pendências na API:** `app/shared/sessions.py`, funções `_get_pending_confirmation_ids` e `_get_pending_confirmations`.
  - Uma confirmação pendente é um `adk_request_confirmation` dos eventos da sessão que ainda não tem `FunctionResponse` com o mesmo `id`.
  - O `detalhes` vem do `payload` da tool: área, data e taxa para reservas; nome e data para visitantes.
- **Rota de confirmações:** `app/controllers/sessions.py`, função `confirmations`.
  - Um `id` que não está pendente na sessão, inclusive um já respondido, recebe `409` antes de chamar o Runner.
  - Um `id` pendente vira um `FunctionResponse` `adk_request_confirmation` com `{"confirmed": ...}`, e o Runner retoma a tool que pediu a confirmação.
- **Mensagem com pendência em aberto:** `app/controllers/sessions.py`, função `send_message`. Enquanto houver confirmação pendente, a mensagem de texto não vai para o agente; a API devolve as pendências.
  - Dentro de uma task, o ADK descartaria o texto silenciosamente.
  - Fora dela, o texto abriria uma nova invocação, e o modelo poderia "achar" que está confirmado.

**Por que não depende do modelo:** a decisão de pedir confirmação está no código da tool, e a execução só continua com um `FunctionResponse` que apenas a rota `/confirmacoes` monta. "Já estou confirmando aqui" é texto: não gera `FunctionResponse`, e a mensagem nem chega ao agente enquanto houver pendência.

### Garantia 2: cada sessão pertence a um apartamento

**Onde está:**
- **Origem do apartamento:** `app/controllers/sessions.py`, função `create_session`.
  - Só aceita apartamentos cadastrados (`if ap not in list_apartments()` → `422`).
  - O apartamento vai para o `state` da sessão uma única vez (`state={"apartamento": ap, ...}`), e nenhuma rota altera esse valor depois.
- **Uso nas tools:** todas leem o apartamento com `context.state.get("apartamento")`:
  - `app/tools/reservations.py`: `faz_reserva`, `cancela_reserva` e `lista_minhas_reservas`;
  - `app/tools/visitors.py`: `autorizar_entrada_visitante`, `lista_meus_visitantes` e `identifica_morador_atual`.
- **Parâmetros:** nenhuma tool recebe o apartamento como parâmetro. O modelo não tem como escolher outro apartamento.
- **Cancelamento:** `app/repo/reservations.py`, função `_remove_reserva`. Filtra por `codigo` e `apartamento_numero`, então nunca remove reserva de outro apartamento.
- **Disponibilidade:** `reserva_disponivel` devolve só "disponivel/indisponivel". As tools de listagem só enxergam o apartamento da sessão, então nenhuma tool traz reservas ou visitantes de outro apartamento.

**Por que não depende do modelo:** mesmo que o morador diga "sou do 302" e o modelo acredite, as tools continuam usando o apartamento gravado no state na criação da sessão. Os prompts do gerenciador e do agente de reservas também mostram o apartamento da sessão e recusam pedidos para outro apartamento, mas isso só melhora a resposta; a proteção está no código.

### Garantia 3: nada se perde no reinício

**Onde está:**
- **Sessões:** `app/dependencies.py`, função `get_session_service`. Usa `SqliteSessionService(db_path=str(DB_PATH))`, então eventos e state das sessões ficam no `condominio.db`.
- **Dados do condomínio:** `app/models/database.py` grava reservas e visitantes no mesmo arquivo, via SQLAlchemy.
- **Retomada depois de reiniciar:** `app/shared/sessions.py`, função `_get_session`, recarrega a sessão do banco a cada requisição. Por isso uma confirmação pedida antes do reinício pode ser aprovada depois dele.

**Por que não depende do modelo:** é persistência em disco. O Runner é recriado a cada requisição, e todo o estado vem do banco.

### Garantia 4: o regulamento é consultado, não carregado

**Onde está:**
- **Leitura do regulamento:** `app/agents/rules_consultant/agent.py`, constante `REGULAMENTO`. Só esse agente lê `dados/regulamento.md`, e ele vai nas instruções (`<REGULAMENTO>{REGULAMENTO}</REGULAMENTO>`) do `agente_consultor_regras`.
- **Agente principal:** `app/agents/manager/agent.py`, função `instrucao_agente_gerenciador`. As instruções do gerenciador não contêm o regulamento.
- **Agente de reservas:** também não o lê.
- **Resposta restrita ao assunto:** `app/agents/rules_consultant/agent.py`, seção `## Como responder` da instrução. O consultor cita só o artigo do assunto perguntado.

**Por que não depende do modelo:**
- No ADK, as instruções de um agente vão na requisição ao modelo (`system_instruction`) e não são gravadas como evento da sessão.
- O regulamento só é enviado quando o gerenciador aciona o consultor.
- Em `single_turn`, a sessão grava só a pergunta que o gerenciador enviou ao consultor e a resposta dele (eventos do branch `agente_consultor_regras@...`). O texto do regulamento nunca vira evento.
- Uma pergunta sobre a piscina não faz capítulos de outros assuntos entrarem nos eventos. As mensagens seguintes também não carregam o regulamento.
- O conteúdo da resposta é a única parte que vem do modelo, e a instrução `## Como responder` a limita ao assunto perguntado.

### Garantia 5: dois moradores, uma reserva

**Onde está:**
- **Constraint no banco:** `app/models/reserva.py`: `UniqueConstraint("area_id", "data", name="uq_reserva_area_data")`.
- **Gravação:** `app/repo/reservations.py`, função `_grava_reserva`.
  - Antes de gravar, consulta se a área está livre, só para dar uma resposta amigável.
  - A garantia está no `session.commit()`: se outra reserva entrou nesse meio tempo, o banco recusa com `IntegrityError`.
  - O código converte esse erro em `ReservationNotAvailable`, e a tool responde "a área já foi reservada por outro morador" (resposta normal, `200`).
- **Fora do event loop:** `app/repo/reservations.py`, função `repo_faz_reserva`, grava com `asyncio.to_thread`.
  - O `SqliteSessionService` grava eventos no mesmo arquivo e precisa do event loop livre para concluir a transação dele.
  - Se o `INSERT` esperasse o lock dentro do loop, as duas escritas se travariam até `database is locked` (erro `500`).
  - A gravação de visitante usa o mesmo cuidado (`app/tools/visitors.py`, `_grava_visitante`).
- **Restauração:** `scripts/seed.py` recria as tabelas da aplicação, então a constraint vale também num banco que já existia.

**Por que não depende do modelo nem da conferência prévia:** a exclusividade é imposta pelo SQLite no instante da gravação. Duas aprovações simultâneas para a mesma área e data resultam em uma reserva gravada e uma recusa, as duas com `200`.

## Como rodar

### Pré-requisitos

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)
- Chave do [Google AI Studio](https://aistudio.google.com/apikey)

### Variáveis do `.env`

```bash
cp .env.example .env
```

| Variável | Obrigatória | Descrição |
|---|---|---|
| `GEMINI_API_KEY` | sim (provider `gemini`) | Chave do Google AI Studio |
| `MODEL_PROVIDER` | não | `gemini` (padrão), `ollama` ou `openroute` |
| `MODEL_NAME` | não | Modelo usado pelos agentes. Padrão: `gemini-3.8-flash` |
| `OLLAMA_HOST` | só com `ollama` | Ex.: `http://localhost:11434` |
| `OPENROUTER_API_KEY` | só com `openroute` | Chave do OpenRouter |

### Subida

```bash
uv sync
uv run python -m scripts.seed    # cria o banco e carrega os dados de dados/
uv run python -m scripts.serve   # API em http://127.0.0.1:8000 (docs em /docs)
```

### Restauração dos dados

```bash
uv run python -m scripts.seed
```

Volta apartamentos, áreas, reservas e visitantes ao estado dos arquivos de `dados/`. As sessões do ADK são mantidas.

Para apagar também as sessões, rode `uv run python -m scripts.reset` antes do seed.

### Rotas

| Rota | Descrição |
|---|---|
| `POST /sessoes` | `{"apartamento": "101"}` → `201 {"session_id": "..."}`, ou `422` se o apartamento não existe |
| `POST /sessoes/{id}/mensagens` | `{"texto": "..."}` → `{"resposta", "confirmacoes_pendentes"}` |
| `POST /sessoes/{id}/confirmacoes` | `{"id": "...", "confirmado": true}` → `{"resposta", "confirmacoes_pendentes"}`, ou `409` |
| `GET /sessoes/{id}/eventos` | Eventos da sessão (`404` se não existir) |
| `GET /apartamentos/{ap}/reservas` | Verificação: reservas do apartamento |
| `GET /apartamentos/{ap}/visitantes` | Verificação: visitantes do apartamento |

Exemplos prontos em `http/*.http` (REST Client) e `postman/`.

### Desenvolvimento

```bash
PYTHONPATH=. uv run adk web app/agents    # agente "manager": inspecionar transferências, tools e confirmações
```
