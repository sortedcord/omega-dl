import click
import os
import logging

from rich.logging import RichHandler
from rich.console import Console
from rich.progress import Progress

from omegadl.catalog import load_catalog, dump_catalog, get_comic_by_id
from omegadl.fetch import get_comic_list, get_chapters, update_comic_metadata
from omegadl.objects import Comic, ComicStatus, Config

FORMAT = "%(message)s"
logging.basicConfig(
    level=logging.INFO, format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)
log = logging.getLogger("rich")
console = Console()


@click.group()
@click.pass_context
def catalog(ctx):
    """
    Commands related to the catalog stored by omegadl.
    """


@catalog.command(name="info")
@click.pass_context
def show_catalog_info(ctx):
    """
    Prints information about the comic catalog.
    """
    config:Config = ctx.obj['config']

    log.info(f"Loading catalog from {config.output_path}/catalog.json")
    catalog, sync_time = load_catalog(output_dir=config.output_path)

    click.echo(f"Catalog last synced at: {sync_time}")
    click.echo(f"Indexed {len(catalog)} titles.")


@catalog.command(name="generate")
@click.pass_context
@click.option("--disable-overwrite", help="Do not generate a new catalog if it already exists.", is_flag=True)
def generate_catalog(ctx, disable_overwrite:bool):
    """
    Generates a fresh comic catalog.
    """

    config:Config = ctx.obj['config']
    if disable_overwrite is not None:
        config.overwrite_catalog = not(disable_overwrite)

    catalog_path = config.output_path / "catalog.json"

    if config.overwrite_catalog == False and os.path.exists(catalog_path):
        log.info("Catalog already generated, skipping overwrite...")
        return

    with console.status("[bold green]Fetching comic list...") as status:
        comic_list = get_comic_list(output_dir=config.output_path)
        log.info(f"Fetched {len(comic_list)} comic titles")

    comics = []
    with Progress() as progress:
        fetch_comics_task = progress.add_task("[red]Downloading Comics Data...", total=len(comic_list))

        for i,comic in enumerate(comic_list):
            progress.update(fetch_comics_task, description=f"[red][{i+1}/{len(comic_list)}] Downloading {comic.name}...")
            comic.chapters = get_chapters(config.output_path, comic, update=False)
            if comic.volume_breakpoints == {}:
                comic.volume_breakpoints = {comic.chapters[-1].slug: "1"}
            comics.append(comic)
            progress.update(fetch_comics_task, advance=1)
            dump_catalog(config.output_path, comics)      
    

@catalog.command(name="update")
@click.pass_context
@click.option("--generate", help="Generate a new config if it does not exist", is_flag=True)
def update_catalog_command(ctx, generate):
    """
    Selectively updates parts of the comic catalog if it already exists.
    """
    
    config:Config = ctx.obj["config"]
    catalog_path = config.output_path / "catalog.json"

    if not os.path.exists(catalog_path):
        if generate:
            generate_catalog(ctx)
        else:
            log.error(f"Catalog cannot be found at {catalog_path}. Exiting...")
        return
    
    update_catalog(config)



def update_catalog(config:Config, filter_list:list[int]=None) -> list[Comic]:
    # filter_list is a list of comic IDs that you can use to selectively update comics.
    # Mainly used for quick updating subscription list titles. Leave none to include all.    
    origin_catalog,_ = load_catalog(config.output_path)

    with console.status("[bold green]Fetching comic list...") as status:
        remote_catalog = get_comic_list(output_dir=config.output_path, cache=config.cache)
        log.info(f"Fetched {len(remote_catalog)} comic titles")
    
        updated_catalog_list = []
        process_queue = [] 
        # Contains (Comic, bool) pair where bool tells if the comic needs to be updated or not.
        # If the bool is false, then all chapters will be fetched, if it is true then only selected chapters
        # will be fetched.


        # Compare Titles and Update
    with console.status("[bold green]Comparing local and remote catalog...") as status:
        for remote_comic in remote_catalog:
            local_comic = get_comic_by_id(origin_catalog, remote_comic.id)
                
            if local_comic is None:
                log.debug(f"{remote_comic.name} not present in local catalog. Adding to fetch list.")
                process_queue.append((remote_comic, False))
                continue

            if filter_list is not None:
                if remote_comic.id not in filter_list:
                    continue

            local_comic:Comic = update_comic_metadata(local_comic, remote_comic)

            if local_comic.status == ComicStatus.ONGOING and remote_comic.status == ComicStatus.ONGOING:
                process_queue.append((local_comic, True))

            elif local_comic.status == ComicStatus.ONGOING and remote_comic.status != ComicStatus.ONGOING:
                log.debug(f"Adding {local_comic.name} to fetch list. Local status ongoing but remote status not ongoing")
                process_queue.append((local_comic, True))

            elif local_comic.status == ComicStatus.HIATUS and remote_comic.status != ComicStatus.HIATUS:
                log.debug(f"Adding {local_comic.name} to fetch list. Local status hiatus but remote status not hiatus")
                process_queue.append((local_comic, True))

            else:
                # If the comic doesn't need to be updated
                updated_catalog_list.append(local_comic)
    
    # Remove comics from process_queue if not in filter_list (if specified)
    _process_queue = process_queue
    if filter_list is not None:
        for i in _process_queue:
            print("HELLO")
            _comic = i[0]
            if _comic.id not in filter_list:
                updated_catalog_list.append(_comic)
                process_queue.remove(i)


    with Progress() as progress:
        update_comics_task = progress.add_task("[red]Downloading Comics...", total=len(process_queue))

        for i in process_queue:
            comic = i[0]
            progress.update(update_comics_task, description=f"[red]Updating {comic.name}...")
            comic.chapters = get_chapters(config.output_path, comic, update=i[1], cache=config.cache)
            if comic.volume_breakpoints == {}:
                comic.volume_breakpoints = {comic.chapters[-1].slug: "1"}
            updated_catalog_list.append(comic)
            log.info(f"Updated '{comic.name}' in catalog.")
            progress.update(update_comics_task, advance=1)

    dump_catalog(config.output_path, updated_catalog_list)

    return updated_catalog_list


