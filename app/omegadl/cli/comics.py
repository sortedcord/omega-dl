import json
import click
import shutil
import logging

from rich.progress import Progress
from rich.table import Table
from rich.logging import RichHandler
from rich.syntax import Syntax
from rich.console import Console

from catalog import load_catalog, search_comics
from omegadl.objects import Comic, Config
from omegadl.downloader import download_chapter
from omegadl.cli import cli

FORMAT = "%(message)s"
logging.basicConfig(
    level=logging.INFO, format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)
log = logging.getLogger("rich")
console = Console()

@cli.group()
@click.pass_context
@click.argument("query")
def comics(ctx, query):
    """
    Commands related to comics. Require a catalog.
    """
    ctx.obj["query"] = query

def display_comics_as_table(catalog:list[Comic], library):
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

@comics.command(name="list")
@click.pass_context
def list_comics(ctx):
    """
    Search for comics. You can search via comic id or comic name.
    """
    
    config:Config = ctx.obj["config"]
    query = ctx.obj["query"]

    catalog,_ = load_catalog(config.output_path)
    
    display_comics_as_table(search_comics(catalog, query), config.library_path)

@comics.command(name="json")
@click.pass_context
def view_comic_json(ctx):
    """
    View the json for a given comic.
    """

    query = ctx.obj["query"]
    config:Config = ctx.obj["config"]

    catalog,_ = load_catalog(config.output_path)
    comic = search_comics(catalog, query)[0]

    console.print(Syntax(json.dumps(comic.encode(), indent=2), "json"))


@comics.command(name="download")
@click.pass_context
@click.option("--chapters", help="Specifiy the chapter slugs (separated by comma) you want to download. List Slicing works as well")
def download_comic(ctx, chapters=None):
    """
    Downloads the missing chapters of a comic. Requires the chapter(s) as an option.
    """
    chapters_query = chapters
    query = ctx.obj["query"]
    config:Config = ctx.obj["config"]

    catalog,_ = load_catalog(config.output_path)
    comic = search_comics(catalog, query)[0]

    # Get chapters:
    download_queue = []

    # Fetch Missing Chapters
    if chapters_query is None:
        for chapter in comic.chapters:
            if not chapter.is_downloaded(comic, config.library_path):
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
    
    progress_total = 0
    for chapter in download_queue:
        progress_total += 3
        progress_total += len(chapter.pages)
    
    with Progress() as progress:
        download_chapter_task = progress.add_task("[red]Downloading Chapters...", total=progress_total)

        for i,chapter in enumerate(download_queue):
            progress.update(download_chapter_task, 
                            description=f"[green]Downloading {chapter.name} - {comic.name[0:40]}...")
            if chapter.pages == []:
                log.error(f"No pages found for '{chapter.name} - {comic.name[0:40]}' It might need repairing in the catalog.")
                continue
            download_chapter(comic, chapter, config.output_path, config.library_path, progress, download_chapter_task)
        progress.remove_task(download_chapter_task)
    shutil.rmtree(config.output_path/"comics"/comic.slug)
