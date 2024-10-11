import click
from pathlib import Path
import os
import shutil
import logging

from rich.logging import RichHandler
from rich.console import Console
from rich.progress import Progress
from rich.table import Table


from catalog import load_catalog, dump_catalog, search_comics, get_comic_by_id
from fetch import get_comic_list, get_chapters, update_comic_metadata
from objects import Comic, ComicStatus
from downloader import download_chapter

FORMAT = "%(message)s"
logging.basicConfig(
    level=logging.INFO, format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)
log = logging.getLogger("rich")
console = Console()

# FIXME: Fix explicit verbose level configuration
def set_verbose(level):
    global log
    FORMAT = "%(message)s"
    logging.basicConfig(
        level=level, format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
    )
    log = logging.getLogger("rich")
    log.debug(f"Set verbose level to {level}")

@click.group()
@click.pass_context
@click.option("--library", default="./", help="Set the directory for saving comics.")
@click.option("--output", default="./", help="Set the output directory for omegadl. This is where the cache and catalog files are stored.")
@click.option("--disable-cache", default=False, help="Disable request cachine. This will make omegadl always fetch from the server.")
@click.option("--verbose", help="Sets verbose level to DEBUG for the logger.", default=False, is_flag=True)
def cli(ctx, output, disable_cache, library=None, verbose=False):
    ctx.ensure_object(dict)
    ctx.obj['output'] = Path(output) / "mdlout"
    ctx.obj['disable_cache'] = disable_cache
    if library is None:
        ctx.obj['library'] = output
    else:
        ctx.obj['library'] = Path(library)
    set_verbose("DEBUG" if verbose else "INFO")


@cli.group()
@click.pass_context
def catalog(ctx):
    """
    Commands related to the catalog stored by omegadl.
    """


@catalog.command()
@click.pass_context
def info(ctx):
    """
    Prints information about the comic catalog.
    """
    output=Path(ctx.obj['output'])

    log.info(f"Loading catalog from {output}/mdlout/catalog.json")
    catalog, sync_time = load_catalog(output_dir=output)

    click.echo(f"Catalog last synced at: {sync_time}")
    click.echo(f"Indexed {len(catalog)} titles.")


@catalog.command()
@click.pass_context
@click.option("--skip-overwrite", help="Do not generate a new catalog if it already exists.", is_flag=True, default=False)
def generate(ctx, skip_overwrite:bool=False):
    """
    Generates a fresh comic catalog.
    """
    output = ctx.obj['output']
    catalog_path = output / "catalog.json"

    if skip_overwrite and os.path.exists(catalog_path):
        log.info("Catalog already generated, skipping overwrite...")
        return

    with console.status("[bold green]Fetching comic list...") as status:
        comic_list = get_comic_list(output_dir=output)
        log.info(f"Fetched {len(comic_list)} comic titles")

    comics = []
    with Progress() as progress:
        fetch_comics_task = progress.add_task("[red]Downloading Comics Data...", total=len(comic_list))

        for comic in comic_list:
            progress.update(fetch_comics_task, description=f"[red]Downloading {comic.name}...")
            comic.chapters = get_chapters(output, comic, update=False)
            if comic.volume_breakpoints == {}:
                comic.volume_breakpoints = {comic.chapters[-1].slug: "1"}
            comics.append(comic)
            progress.update(fetch_comics_task, advance=1)
    
    dump_catalog(comics)      


@catalog.command()
@click.pass_context
@click.option("--generate-missing", help="Generate a new config if it does not exist", is_flag=True, default=False)
def update(ctx, generate_missing):
    """
    Selectively updates parts of the comic catalog if it already exists.
    """
    output = ctx.obj["output"]
    catalog_path = output / "catalog.json"

    if not os.path.exists(catalog_path):
        if generate_missing:
            generate(ctx)
        else:
            log.error(f"Catalog cannot be found at {catalog_path}. Exiting...")
        return
    
    origin_catalog,_ = load_catalog(output)

    with console.status("[bold green]Fetching comic list...") as status:
        remote_catalog = get_comic_list(output_dir=output)
        log.info(f"Fetched {len(remote_catalog)} comic titles")
    
    updated_catalog_list = []
    process_queue = [] 
    # Contains (Comic, bool) pair where bool tells if the comic needs to be updated or not.
    # If the bool is false, then all chapters will be fetched, if it is true then only selected chapters
    # will be fetched.

    # Compare Titles and Update
    for remote_comic in remote_catalog:
        local_comic = get_comic_by_id(origin_catalog, remote_comic.id)

        if local_comic is None:
            log.debug(f"{remote_comic.name} not present in local catalog. Adding to fetch list.")
            process_queue.append((remote_comic, False))
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
    
    with Progress() as progress:
        update_comics_task = progress.add_task("[red]Downloading Comics...", total=len(process_queue))

        for i in process_queue:
            comic = i[0]
            progress.update(update_comics_task, description=f"[red]Updating {comic.name}...")
            comic.chapters = get_chapters(output, comic, update=i[1])
            if comic.volume_breakpoints == {}:
                comic.volume_breakpoints = {comic.chapters[-1].slug: "1"}
            updated_catalog_list.append(comic)
            log.info(f"Updated '{comic.name}' in catalog.")
            progress.update(update_comics_task, advance=1)


    dump_catalog(output, updated_catalog_list)


@cli.group()
@click.pass_context
@click.argument("query")
def comics(ctx, query):
    """
    Commands related to comics. Require a catalog.
    """
    ctx.obj["query"] = query

def list_comics(catalog:list[Comic], library):
    table = Table(title="Indexed Comic Titles")

    table.add_column("Comic ID", justify="left", style="cyan", no_wrap=True)
    table.add_column("Title", style="magenta")
    table.add_column("Comic Status", justify="left", style="green")
    table.add_column("Comic Subscribed", justify="left", style="green")
    table.add_column("Latest Chapter", justify="left", style="green")
    table.add_column("Downloaded")

    for comic in catalog:
        if comic is None:
            continue

        last_downloaded_chapter = comic.get_last_downloaded_chapter(library)

        latest_chapter = comic.chapters[0].name

        if last_downloaded_chapter is None:
            last_downloaded_chapter = "[red]Not downloaded[/red]"
        else:
            last_downloaded_chapter = last_downloaded_chapter.name
        
        if latest_chapter == last_downloaded_chapter:
            last_downloaded_chapter = "[green][bold]Up-to-date[/bold][/green]"

        table.add_row(str(comic.id), comic.name[0:70], comic.status.name, 
                      str(comic.is_subscribed), latest_chapter, last_downloaded_chapter)

    console.print(table)

@comics.command()
@click.pass_context
def list(ctx):
    """
    Search for comics. You can search via comic id or comic name.
    """
    output = ctx.obj["output"]
    query = ctx.obj["query"]
    library = ctx.obj['library']

    catalog,_ = load_catalog(output)
    
    list_comics(search_comics(catalog, query), library)

@comics.command()
@click.pass_context
@click.option("--chapters", help="Specifiy the chapter slugs (separated by comma) you want to download. List Slicing works as well")
def download(ctx, chapters=None):
    """
    Downloads the missing chapters of a comic. Requires the chapter(s) as an option.
    """
    chapters_query = chapters
    output = ctx.obj["output"]
    query = ctx.obj["query"]
    library = ctx.obj['library']

    catalog,_ = load_catalog(output)
    comic = search_comics(catalog, query)[0]

    # Get chapters:
    download_queue = []

    # Fetch Missing Chapters
    if chapters_query is None:
        for chapter in comic.chapters:
            if not chapter.is_downloaded(comic, library):
                download_queue.append(chapter)


    # TODO: Add ability to select chapter using chapter IDs and chapter slugs both.
    else:
        download_queue = []
        for range in chapters_query.split(","):
            if ":" in range:
                # Splice range
                start,end = range.split(":")[0], range.split(":")[1]
                queue_add = False
                for chapter in comic.chapters:
                    if chapter.slug == start:
                        queue_add = True
                    elif chapter.slug == end:
                        queue_add = False
                        break
                    if queue_add:
                        download_queue.append(chapter)
            else:
                for chapter in comic.chapters:
                    if chapter.slug == range:
                        download_queue.append(chapter)
    
    with Progress() as progress:
        download_chapter_task = progress.add_task("[red]Downloading Chapters...", total=len(download_queue))

        for i,chapter in enumerate(download_queue):
            progress.update(download_chapter_task, 
                            description=f"[red][{i}/{len(download_queue)}] Downloading {chapter.name} - {comic.name[0:40]}...")
            download_chapter(comic, chapter, output, library)
            log.info(f"Downloaded {chapter.name} - {comic.name[0:40]}...")
            progress.update(download_chapter_task, advance=1)


@click.command()
@click.option("--output", default="./", help="Set the output directory for omegadl. This is where the cache and catalog files are stored.")
def clear_cache(output:str):
    """
    Clears the requests cache stored in mdlout/cache directory.
    """
    cache_dir = Path(output) / "mdlout" / "cache"

    if not os.path.exists(cache_dir):
        log.error("Cache directory does not exist in the given location.")
        return
    
    shutil.rmtree(cache_dir)
    log.info("Cleared omegadl cache.")
cli.add_command(clear_cache)


@click.command()
def version():
    """
    Displays the version of omegadl
    """
    click.echo(f"omegadl Version 0.1")
    click.echo(f"View project on Github: https://github.com/sortedcord/omegadl")
cli.add_command(version)


if __name__ == '__main__':
    cli()