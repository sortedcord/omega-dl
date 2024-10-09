
def store_to_comic_names(catalog:list) -> list:
    """
    Returns all the names of comic titles present in the catalog.
    """

    comic_names = []
    for comic in catalog:
        comic_names.append(comic["name"].lower())

def get_comic_by_name(catalog:list, query:str) -> dict:
    """
    Search comics by name
    """
    query = query.lower().replace(" ", "")

    # TODO: Improve name matching.
    for comic in catalog:
        _s_title = comic["name"].lower().replace(" ", "")

        if query in _s_title or query in _s_title or query == _s_title:
            return comic
