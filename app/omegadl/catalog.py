from pathlib import Path
from datetime import datetime
import json

from omegadl.objects import Comic, dict_to_comic, ComicStatus


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
    Dumps the comic catalog at a given output directory
    """
    catalog_json = output_dir / "catalog.json"

    comic_list = [comic.encode() for comic in comic_list]

    with open(catalog_json, "w") as f:
        f.write(json.dumps({
            "meta": {
                "fetched": str(datetime.now())
            },
            "data": comic_list
        }, default=vars))


def store_to_comic_names(catalog:list) -> list:
    """
    Returns all the names of comic titles present in the catalog.
    """

    comic_names = []
    for comic in catalog:
        comic_names.append(comic["name"].lower())

def get_comic_by_name(catalog:list[Comic], query:str) -> dict:
    """
    Search comics by name
    """
    query = query.lower().replace(" ", "")

    # TODO: Improve name matching.
    for comic in catalog:
        _s_title = comic.name.lower().replace(" ", "")

        if query in _s_title or query in _s_title or query == _s_title:
            return comic

def get_comic_by_id(catalog:list[Comic], search_id:str) -> Comic:
    """
    Search comics by id
    """
    for comic in catalog:
        if comic.id == search_id:
            return comic


def search_comics(catalog, query) -> list[Comic]:
    queries = query.split(",")
    filtered_comics = []

    # TODO: Add proper filters
    # Make it so that it splits the query string with ? then it 
    # splits the filters string with & then processes it.
    for query in queries:
        if "?status=" in query:
            status_filter = query.split("?status=")[-1]
            filtered_catalog = []
            for _comic in catalog:
                if _comic.status == ComicStatus(status_filter):
                    filtered_catalog.append(_comic)
            catalog = filtered_catalog

        query = query.split("?")[0]

        # If all comics need to be filtered through
        if query == ":all":
            return catalog
        
        # If only subscribed comics need to be filtered
        if query == ":subscribed":
            for comic in catalog:
                if comic.is_subscribed:
                    filtered_comics.append(comic)
            continue

        try:
            query = int(query)
        except:
            filtered_comics.append(get_comic_by_name(catalog, query))
        else:
            filtered_comics.append(get_comic_by_id(catalog, query))
    
    return filtered_comics
