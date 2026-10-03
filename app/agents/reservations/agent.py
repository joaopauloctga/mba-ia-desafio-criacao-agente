from datetime import date
from pathlib import Path

from google.adk.agents import Agent
from google.adk.agents.readonly_context import ReadonlyContext

from app.tools.areas import lista_areas_condominio
from app.tools.reservations import faz_reserva, reserva_disponivel

REGULAMENTO = (
    Path(__file__).resolve().parents[3] / "dados" / "regulamento.md"
).read_text(encoding="utf-8")


def instrucao_agente_reservas(context: ReadonlyContext) -> str:
    return f"""
        Voce é um agente responsavel por fazer as reservas das areas comuns do condominio.

        DATA ATUAL:
        <DATAATUAL>{date.today().strftime("%d/%m/%Y")}</DATAATUAL>

        - Quando o morador solicitar uma reserva, verifique se a mesma está disponivel e siga as condicoes abaixo:
        -- Se nao esta disponivel: Avise ao morador que nao esta disponivel.
        -- Se esta disponivel e nao tem taxa de reserva: Pergunte ao morador se ele deseja que vc reserve.
        -- Se esta disponivel e tem taxa de reserva: gere uma cobranca e peca confirmacao da reserva para o morador.

        - Areas:
        -- Sempre use o código da area para reservar ou verificar disponibilidade
        -- Se nao souber o código da area lista as areas do condominio
        -- Nome das areas providos pelos moradores podem variar um pouco do nome exato registrado, exemplo: `quero reservar a quadra de futebol`, assuma que é a quadra.

        - Datas:
        -- Se o morador nao mencionar o ano, considere o ano da <DATAATUAL> do system prompt, nao das msg.

        # Regras
        - Somente o morador pode fazer um reserva do apartamento dele
        - Somente o morador pode cancenlar um reserva do apartamento dele
        - Alteracao de reserva depende se a nova reserva esta disponivel
        - Nao faca reserva de imediato, somente apos confirmacao do cliente.
        - Ao fazer reserva com sucesso sua task terminou.
    """


agent_reservartions = Agent(
    name="agente_de_reservas",
    # model=llm,
    model="gemini-3.5-flash",
    description="Especialista em reservas do condominio, responsavel por agendar as reservas dos moradores.",
    instruction=instrucao_agente_reservas,
    mode="task",
    tools=[
        reserva_disponivel,
        faz_reserva,
        lista_areas_condominio
    ],
    output_key="agente_de_reservas"
)
