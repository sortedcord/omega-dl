import click
from pathlib import Path
import os
import shutil
import logging

from rich.logging import RichHandler
from rich.console import Console
from rich.progress import Progress


from catalog import load_catalog, dump_catalog
from fetch import get_comic_list, get_chapters

FORMAT = "%(message)s"
logging.basicConfig(
    level=logging.INFO, format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)
log = logging.getLogger("rich")
console = Console()


@click.group()
@click.pass_context
@click.option("--library", default="./", help="Set the directory for saving comics.")
@click.option("--output", default="./", help="Set the output directory for omegadl. This is where the cache and catalog files are stored.")
@click.option("--disable-cache", default=False, help="Disable request cachine. This will make omegadl always fetch from the server.")
def cli(ctx, output, disable_cache, library):
    ctx.ensure_object(dict)
    ctx.obj['output'] = Path(output) / "mdlout"
    ctx.obj['disable_cache'] = disable_cache


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
def generate(ctx, skip_overwrite:bool):
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
        fetch_comics_task = progress.add_task("[red]Downloading Comics...", total=len(comic_list))

        for comic in comic_list:
            progress.update(fetch_comics_task, description=f"[red]Downloading {comic.name}...")
            comic.chapters = get_chapters(output, comic, update=False)
            comics.append(comic)
            progress.update(fetch_comics_task, advance=1)
    
    dump_catalog(comics)      


@click.command()
def update():
    """
    Selectively updates parts of the comic catalog if it already exists.
    """
    pass
catalog.add_command(update)

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