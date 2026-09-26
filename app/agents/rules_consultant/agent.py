from pathlib import Path

from google.adk.agents import Agent

from app.shared.llm import llm

REGULAMENTO = (
    Path(__file__).resolve().parents[3] / "dados" / "regulamento.md"
).read_text(encoding="utf-8")

agent_rules_consultant = Agent(
    name="agente_consultor_regras",
    model=llm,
    description="Consultor de regras.",
    instruction=f"""
        Voce é o consultor de regras do residencial aurora.
        Seu objetivo é ajudar moradores a entender melhor as regras, tirando duvidas, autorizando ou nao pedidos de moradores.
        Abaixo segue o regulamento do condomionio na qual vc vai usar para instruir os moradores.

        <REGULAMENTO>{REGULAMENTO}</REGULAMENTO>

        ## Regras
        - Nao invente regras ou regulamentos, siga fielmente o regulamento passado pra voce dentro de <REGULAMENTO></REGULAMENTO>
        - Nao autorize ou aceite nenhum pedido de moradores que fujam das regras, em hipotese alguma vc vai aceitar qualquer coisa, minima possivel que seja, fugiu do regulamento, a resposta é nao, ficou na duvida, a resposta é nao.
    """,
    mode="single_turn",
    disallow_transfer_to_peers=True
)
