import requests
import json
import random
import os
from omegadl.utils import slugify
from pathlib import Path
import logging
from rich.logging import RichHandler
from omegadl.objects import Comic, dict_to_chapter, dict_to_comic, Chapter


FORMAT = "%(message)s"
logging.basicConfig(
    level="INFO", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
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


def update_comic_metadata(local:Comic, remote:Comic) -> Comic:
    chapters = local.chapters
    remote.chapters = chapters
    return remote


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
    
    if sc == 200:
        try:
            response_dict = json.loads(resp)            
        except json.JSONDecodeError:
            log.error("Failed to decode JSON. The response might not be in JSON format.")
            log.info(search_url)
            log.info(resp)
    else:
        log.error(f"Request failed with status code: {response.status_code}")
        log.debug(f"Response content: \n{resp}")
    

    with open(dump_dir / (slugify(search_url)+".txt"), "w") as f:
        f.write(resp)
    
    return response_dict


def get_chapter_pages(output_dir:Path, comic:dict, chapter:dict, cache:bool) -> list:
    """
    Get all image urls of pages of a particular chapter of a comic.
    #   output_dir: Ouput Directory
    #   comic: 
    #   chapter:
    """

    log.debug(f"Fetching chapter pages for {comic.name} - {chapter.slug}")

    request_url = f"https://api.omegascans.org/chapter/{comic.slug}/{chapter.slug}"
    reponse = _fetch(request_url, dump=cache, output_dir=output_dir)

    try:
        image_urls = reponse['chapter']['chapter_data']['images']
        return image_urls
    except KeyError:
        return 'paywall'


def get_comic_list(output_dir:Path, cache:bool) -> list[Comic]:
    """
    Get all the comics along with their basic metadata from omegascans.
    output_dir: Pass in the output directory for omegadl
    """

    current_page = 1
    last_page = 100
    search_url = f"https://api.omegascans.org/query?adult=true"
    data = []

    
    # Iterate through search results
    while current_page<=last_page:
        response = _fetch(search_url, dump=cache, output_dir=output_dir)
        data.extend(response['data'])

        if current_page==1:
            # print("Total comics found: ", response['meta']['total'])
            last_page = int(response['meta']['last_page'])
        # else:
        #     print("Fetched page ", current_page) 

        current_page +=1
        search_url= search_url.split("&page=")[0] + f"&page={current_page}"
    
    comic_list = []
    
    for comic_dict in data:
        if comic_dict['series_type'] != "Comic":
            continue
        
        comic_list.append(dict_to_comic(comic_dict))
    
    return comic_list

# TODO: Adjust perPage argument according to missing chapters when updating.
def get_chapter_list(output_dir:Path, comic:dict, cache:bool) -> list[Chapter]:
    """
    Returns the list of chapters for a given comic
    #   output_dir: Location of the output directory
    #   comic: The comic dictionary object 
    """

    request_url = f"https://api.omegascans.org/chapter/query?page=1&perPage=1999&series_id={comic.id}"
    response: list = _fetch(request_url, dump=cache, output_dir=output_dir)['data']
    
    chapter_list = []
    for chapter_dict in response:
        chapter_list.append(dict_to_chapter(chapter_dict))
    
    return chapter_list


def get_chapters(output_dir:Path, comic:dict, update:bool, cache:bool) -> list:
    """
    Takes in the local catalog's comic object and then fetches all the chapters 
    of the title that are missing in the case update is true.
    # output_dir:
    # comic:    
    # update: 
    """

    
    chapter_list = get_chapter_list(output_dir, comic, cache)
    page_fetch_queue = []

    page_fetch_queue = chapter_list.copy() # Initially add all chapters to queue

    if update:
        if len(chapter_list) == len(comic.chapters):
            return comic.chapters
        
        # Remove chapter from fetch_queue if in local_catalog
        for remote_chapter in chapter_list:
            for local_chapter in comic.chapters:
                if remote_chapter.id == local_chapter.id:
                    page_fetch_queue.remove(remote_chapter)
    

    ordered_chapter_list = []
    
    # Build an ordered chapter list
    for chapter in chapter_list:

        # If chapter in queue, then download it and update the chapter object 
        # and then add it to the ordered list
        if chapter in page_fetch_queue:
            log.debug(f"Updating chapter {chapter.slug} - {comic.name} from remote catalog.")
            pages = get_chapter_pages(output_dir, comic, chapter, cache)
            if pages == "paywall":
                continue # Skip adding chapter if paywalled.

            chapter.pages = pages
            ordered_chapter_list.append(chapter)
        else:
            # If chapter not in queue, then use the local catalog comic object 
            # and then add it to the ordered list
            for i in comic.chapters:
                if chapter.id == i.id:
                    ordered_chapter_list.append(i)
                    break

    return ordered_chapter_list


def dump_catalog(output_dir:Path, catalog:dict) -> dict:
    catalog_json_path = output_dir / "catalog.json"

    with open(catalog_json_path, "w") as f:
        f.write(json.dumps(catalog, indent=2))
