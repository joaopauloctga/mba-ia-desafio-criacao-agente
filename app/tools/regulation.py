import re
import unicodedata
from pathlib import Path
from typing import NamedTuple

REGULAMENTO_PATH = Path(__file__).resolve().parents[2] / "dados" / "regulamento.md"
NIVEL_CAPITULO = 2

TITULO_MARKDOWN = re.compile(r"^(#+)\s+(.+?)\s*$")
NUMERAL_CAPITULO = re.compile(r"^(?:capitulo\s+)?([ivxlcdm]+)\b")


class Titulo(NamedTuple):
    linha: int
    nivel: int
    texto: str


def _normaliza(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return sem_acento.lower().strip()


def _extrai_titulos(linhas: list[str]) -> list[Titulo]:
    titulos = []
    for i, linha in enumerate(linhas):
        match = TITULO_MARKDOWN.match(linha)
        if match:
            titulos.append(Titulo(i, len(match.group(1)), match.group(2)))
    return titulos


LINHAS = REGULAMENTO_PATH.read_text(encoding="utf-8").splitlines()
TITULOS = _extrai_titulos(LINHAS)
CAPITULOS = [t for t in TITULOS if t.nivel == NIVEL_CAPITULO]


def _numeral(texto: str) -> str | None:
    match = NUMERAL_CAPITULO.match(_normaliza(texto))
    return match.group(1) if match else None


def _encontra_capitulo(capitulo: str) -> Titulo | None:
    numeral = _numeral(capitulo)
    for titulo in CAPITULOS:
        if numeral and numeral == _numeral(titulo.texto):
            return titulo

    busca = _normaliza(capitulo)
    for titulo in CAPITULOS:
        if busca in _normaliza(titulo.texto):
            return titulo
    return None


def _recorta_secao(titulo: Titulo) -> str:
    fim = len(LINHAS)
    for proximo in TITULOS:
        if proximo.linha > titulo.linha and proximo.nivel <= titulo.nivel:
            fim = proximo.linha
            break
    return "\n".join(LINHAS[titulo.linha:fim]).strip()


async def lista_capitulos_regulamento() -> list[str]:
    """
        Lista os titulos dos capitulos do regulamento interno do condominio (somente o indice, sem o conteudo).

        Returns:
            list[str]: titulos dos capitulos, ex: "Capítulo IV: Piscina"
    """
    return [c.texto for c in CAPITULOS]


async def consulta_capitulo_regulamento(capitulo: str) -> dict:
    """
        Retorna o texto completo de um capitulo do regulamento interno do condominio.

        Args:
            capitulo: titulo do capitulo como devolvido por lista_capitulos_regulamento,
                o numeral romano ("IV") ou parte do titulo ("piscina").

        Returns:
            dict: {"titulo": str, "conteudo": str}
                ou {"erro": str, "capitulos_disponiveis": list[str]} quando o capitulo nao existe.
    """
    titulo = _encontra_capitulo(capitulo)
    if titulo is None:
        return {
            "erro": f"Capitulo '{capitulo}' nao encontrado no regulamento.",
            "capitulos_disponiveis": [c.texto for c in CAPITULOS],
        }
    return {"titulo": titulo.texto, "conteudo": _recorta_secao(titulo)}
