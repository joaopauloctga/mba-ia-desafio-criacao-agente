from app.repo.areas import repo_lista_areas


async def lista_areas_condominio() -> list[dict]:
    """"
        Lista as areas comumns do condominio.

        Returns:
            list[dict]: {"id": int, "nome": str, "taxa": float}
    """
    areas = await repo_lista_areas()
    return [{"id": a.id, "nome": a.nome, "taxa": a.taxa} for a in areas]
