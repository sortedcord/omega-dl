import requests
import json
import random
import datetime
import os
from utils import slugify
from pathlib import Path
from store import get_comic_by_name
import logging
from rich.logging import RichHandler


FORMAT = "%(message)s"
logging.basicConfig(
    level="NOTSET", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)
log = logging.getLogger("rich")


def read_cookies() -> dict:
    try:
        with open("cookies.json", "r") as f:
            cookies = json.loads(f.read())
    except Exception as a:
        log.error("Could not read cookies")
        raise a
    return cookies


def generate_random_headers():
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59'
    ]
    
    languages = ['en-US,en;q=0.9', 'fr-FR,fr;q=0.8,en-US;q=0.7,en;q=0.6', 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7', 'es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7', 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7']
    
    platforms = ['"Windows"', '"macOS"', '"Linux"', '"iOS"', '"Android"']
        
    ua = random.choice(user_agents)
    lang = random.choice(languages)
    platform = random.choice(platforms)
    origin = "https://omegascans.org"
    
    return {
        'accept': 'application/json, text/plain, */*',
        'accept-language': lang,
        'origin': origin,
        'priority': 'u=1, i',
        'referer': f'{origin}/',
        'sec-ch-ua': f'"Chromium";v="{random.randint(80, 130)}", "Not=A?Brand";v="{random.randint(1, 24)}"',
        'sec-ch-ua-mobile': f'?{random.randint(0, 1)}',
        'sec-ch-ua-platform': platform,
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': ua
    }


def update_comic_metadata(local:dict, remote:dict):
    chapters = local["chapters"]
    local.update(remote)
    local['chapters'] = chapters
    return local


def _fetch(search_url:str, dump:bool, output_dir:Path=None) -> dict:
    dump_dir = output_dir / "cache" / "requests"
    resp = None
    sc = 0

    if dump:
        os.makedirs(dump_dir, exist_ok=True)
        try:
            with open(dump_dir / (slugify(search_url)+".txt"), "r") as f:
                resp = f.read()
                sc = 200
            # log.debug(f"Fetched request cache for: {search_url}")
        except:
            pass

    if resp is None:
        response = requests.get(search_url, headers=generate_random_headers(), cookies=read_cookies())
        sc = response.status_code
        resp = response.text
        if dump:
            with open(dump_dir / (slugify(search_url)+".txt"), "w") as f:
                f.write(resp)
            # log.debug("Dumped request cache")
    
    if sc == 200:
        try:
            response_dict = json.loads(resp)            
        except json.JSONDecodeError:
            log.error("Failed to decode JSON. The response might not be in JSON format.")
    else:
        log.error(f"Request failed with status code: {response.status_code}")
        log.debug(f"Response content: \n{resp}")
    
    return response_dict


def get_chapter_pages(output_dir:Path, comic:dict, chapter:dict) -> list:
    """
    Get all image urls of pages of a particular chapter of a comic.
    #   output_dir: Ouput Directory
    #   comic: 
    #   chapter:
    """

    log.debug(f"Fetching chapter pages for {comic['name']} - {chapter['slug']}")

    request_url = f"https://api.omegascans.org/chapter/{comic['slug']}/{chapter['slug']}"
    reponse = _fetch(request_url, dump=True, output_dir=output_dir)

    try:
        image_urls = reponse['chapter']['chapter_data']['images']
        return image_urls
    except KeyError:
        return 'paywall'
     


def get_comic_list(output_dir:Path) -> list:
    """
    Get all the comics along with their basic metadata from omegascans.
    output_dir: Pass in the output directory for omegadl
    """

    current_page = 1
    last_page = 100
    search_url = f"https://api.omegascans.org/query?adult=true"
    data = []

    log.debug("Fetching comic list")
    
    # Iterate through search results
    while current_page<=last_page:
        response = _fetch(search_url, dump=True, output_dir=output_dir)
        data.extend(response['data'])

        if current_page==1:
            # print("Total comics found: ", response['meta']['total'])
            last_page = int(response['meta']['last_page'])
        # else:
        #     print("Fetched page ", current_page) 

        current_page +=1
        search_url= search_url.split("&page=")[0] + f"&page={current_page}"
    
    comic_list = []
    
    for i in data:
        if i['series_type'] != "Comic":
            continue
        comic_dict = {
                "name": i['title'],
                "id": i['id'],
                "slug": i['series_slug'],
                "thumbnail_url":i['thumbnail'],
                "status":i['status'].lower(),
                "created_at": i['created_at'],
                "updated_at": i['updated_at'],
                "chapters":[]
            }
        
        comic_list.append(comic_dict)
    
    return comic_list

# TODO: Adjust perPage argument according to missing chapters when updating.
def get_chapter_list(output_dir:Path, comic:dict) -> list:
    """
    Returns the list of chapters for a given comic
    #   output_dir: Location of the output directory
    #   comic: The comic dictionary object 
    """
    # log.debug(f"Fetching chapter list for {comic['name']}")

    request_url = f"https://api.omegascans.org/chapter/query?page=1&perPage=1999&series_id={comic['id']}"
    response: list = _fetch(request_url, dump=True, output_dir=output_dir)['data']
    
    chapter_list = []
    for i in response:
        chapter_list.append({
            "id": i['id'],
            "name": i['chapter_name'],
            "thumbnail_url": i['chapter_thumbnail'],
            "slug": i['chapter_slug']
        })
    
    return chapter_list


def get_chapters(output_dir:Path, comic:dict, update:bool) -> list:
    """
    Takes in the local catalog's comic object and then fetches all the chapters 
    of the title that are missing in the case update is true.
    # output_dir:
    # comic:    
    # update: 
    """

    
    chapter_list = get_chapter_list(output_dir, comic)
    page_fetch_queue = []

    page_fetch_queue = chapter_list.copy() # Initially add all chapters to queue

    if update:
        if len(chapter_list) == len(comic['chapters']):
            # log.debug(f"All chapters up to date for {comic['name']}")
            return comic['chapters']
        # Add chapter to fetch_queue if missing in local_catalog

        for remote_chapter in chapter_list:
            for local_chapter in comic['chapters']:
                if remote_chapter['slug'] == local_chapter['slug']:
                    # log.debug(f"Found {remote_chapter['slug']} - {comic['name']} in local catalog.")
                    page_fetch_queue.remove(remote_chapter)
    

    ordered_chapter_list = []
    
    # Build an ordered chapter list
    for chapter in chapter_list:

        # If chapter in queue, then download it and update the chapter object 
        # and then add it to the ordered list
        if chapter in page_fetch_queue:
            log.debug(f"Updating chapter {chapter['slug']} - {comic['name']} from remote catalog.")
            pages = get_chapter_pages(output_dir, comic, chapter)
            if pages == "paywall":
                # log.debug("Skipping chapter as it is paywalled...")
                continue # Skip adding chapter if paywalled.

            chapter['data'] = pages
            ordered_chapter_list.append(chapter)
        else:
            # If chapter not in queue, then use the local catalog comic object 
            # and then add it to the ordered list
            for i in comic['chapters']:
                if chapter['slug'] == i['slug']:
                    ordered_chapter_list.append(i)
                    break

    return ordered_chapter_list


# TODO: Add comic_store updating functions
# TODO: Switch to using objects instead of dictionaries
def get_catalog(output_dir:Path, update:bool=True) -> list:
    """
    Creates a catalog by fetching data from omegascans.
    Updates the catalog if output_dir contains 'catalog.json'
    output_dir: Pass in the output directory for omegadl
    """

    remote = None
    origin = None

    if not os.path.exists(output_dir / "catalog.json"):
        log.error(f"{output_dir / 'catalog.json' } does not exist. Generating a new catalog.")
        update = False

    remote = get_comic_list(output_dir)
    updated_catalog = {"meta":{"fetched": None},"data":[]}
    updated_catalog_data:list = updated_catalog["data"]

    if update:
        origin = load_store(output_dir)["data"]
        new_list = []
        update_list = []

        # Compare Titles and Update
        for remote_comic in remote:
            local_comic = get_comic_by_name(origin, remote_comic['name'])

            if local_comic is None:
                log.debug(f"{remote_comic['name']} not present in local catalog. Adding to fetch list.")
                new_list.append(remote_comic)
                continue

            local_comic = update_comic_metadata(local_comic, remote_comic)

            if local_comic['status'].lower() == "ongoing" and remote_comic['status'].lower() == "ongoing":
                # log.debug(f"Adding {local_comic['name']} to fetch list.")
                update_list.append(local_comic)

            elif local_comic['status'].lower() == "ongoing" and remote_comic['status'].lower() != "ongoing":
                log.debug(f"Adding {local_comic['name']} to fetch list. Local status ongoing but remote status not ongoing")
                update_list.append(local_comic)

            elif local_comic['status'].lower() == "hiatus" and remote_comic['status'].lower() != "hiatus":
                log.debug(f"Adding {local_comic['name']} to fetch list. Local status hiatus but remote status not hiatus")
                update_list.append(local_comic)

            else:
                # If the comic doesn't need to be updated
                # log.debug(f"No changes in {local_comic['name']}, skipping fetch.")
                updated_catalog_data.append(local_comic)
        
        remote = new_list

        for comic in update_list:
            comic["chapters"] = get_chapters(output_dir, comic, update=True)
            updated_catalog_data.append(comic)

    for comic in new_list:
        comic["chapters"] = get_chapters(output_dir, comic, update=False)
        updated_catalog_data.append(comic)

    updated_catalog["meta"]["fetched"] = str(datetime.datetime.now())

    dump_catalog(output_dir, updated_catalog)

    return updated_catalog_data            
   

def dump_catalog(output_dir:Path, catalog:dict) -> dict:
    catalog_json_path = output_dir / "catalog.json"

    with open(catalog_json_path, "w") as f:
        f.write(json.dumps(catalog, indent=2))


def load_store(output_dir:Path) -> dict:
    master_json_path = output_dir / "catalog.json"
    
    with open(master_json_path, "r") as f:
        comic_store = json.loads(f.read())

    return comic_store

