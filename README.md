# Projeto

Desafio pratico do mba Engenharia de Software com AI da Fullcycle

# Setup inicial

Rode os commandos na seguinte ordem para popular os dados e iniciar o servidor.

uv sync
source .venv/bin/activate
export PYTHONPATH=.
python -m scripts.seed
python -m scripts.serve

# Comandos

Inicie o python env

source .venv/bin/activate
export PYTHONPATH=.

- Seed banco de dados com os arquivos json da pasta dados.

python -m scripts.seed

- Resetar banco de dados

python -m scripts.reset

- Subir o servidor da API (FastAPI) em http://127.0.0.1:8000 (docs em /docs)

python -m scripts.serve

# Agents

Foi decidido usar dois agentes além do principal.

- Manager
  Agente principal resposável por gerenciar o atendimento dos moradores

- Reservations
  Agente responsável por atender o pedido de reservas dos moradores.
  mode: Task
  Escolhi o modo task pro agente conseguir iteregir com o morador via chat mas como ele é responsábel somente pelas reservas, quando ele fazer a reserva
  ou terminar o atendimento ele "não é mais útil" pro morador entao sua task é finalizada e é passado o control pro agente principal.

- Rules Consultant
  Agente resposável por auxiliar o gerente a responder sobre as regras do residencial.
  mode: Single turn
  Escolhi o single turn porque na minha visao isso é um tarefa simples onde o morador pode perguntar sobre uma regra espeficica na qual nao deve ter muita iterecao ou discussao sobre a regra, regra é regra e não espaco para duvida, questionamento nesse contexto da aplicacoa, entao basicamente ele responde diretamente pro gerente na qual vai interagir com o morador passando a informacao.
