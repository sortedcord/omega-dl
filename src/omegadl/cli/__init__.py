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
    # set_verbose("DEBUG" if verbose else "INFO")


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
