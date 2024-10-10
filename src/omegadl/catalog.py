from pathlib import Path
from datetime import datetime
import json

from objects import Comic, dict_to_comic


# TODO: Use catalog as an object
# TODO: Implement subscription list

def load_catalog(output_dir:Path):
    """
    Loads the comic catalog from given output directory
    """
    catalog_json = output_dir / "catalog.json"

    with open(catalog_json, "r") as f:
        comic_store = json.loads(f.read())

    comics = []
    for comic in comic_store["data"]:
        comics.append(dict_to_comic(comic))

    sync_time = comic_store["meta"]["fetched"]

    return comics, sync_time

def dump_catalog(output_dir:Path, comic_list:list[Comic]):
    """
    Loads the comic catalog at a given output directory
    """
    catalog_json = output_dir / "catalog.json"

    with open(catalog_json, "w") as f:
        f.write(json.loads({
            "meta": {
                "fetched": str(datetime.now())
            },
            "data": comic_list
        }))


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

def get_comic_by_id(catalog:list[Comic], search_id:str) -> Comic:
    """
    Search comics by id
    """
    for comic in catalog:
        if comic.id == search_id:
            return comic
