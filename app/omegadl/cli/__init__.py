import click
from pathlib import Path
import os
import shutil
import logging

from rich.logging import RichHandler
from rich.console import Console

from omegadl.objects import Config


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
@click.option("--library", help="Set the directory for saving comics.")
@click.option("--output", default="./", help="Set the output directory for omegadl. This is where the cache and catalog files are stored.")
@click.option("--disable-cache", help="Disable request cachine. This will make omegadl always fetch from the server.", is_flag=True)
def cli(ctx, output, disable_cache:bool, library):
    ctx.ensure_object(dict)

    if not output.endswith("mdlout"):
        output = Path(output) / "mdlout"
        os.makedirs(output, exist_ok=True)

    config = Config()

    config.output_path = Path(output)
    if os.path.exists(output / "config.json"):
        console.log(f"Loading config from {output / 'config.json'}")
        config = config.load()

    if disable_cache is not None:
        config.cache = not(disable_cache)

    if library is not None:
        config.library_path = Path(library)

    ctx.obj['config'] = config


@cli.command()
@click.pass_context
def reset_config(ctx):
    """
    Generates a fresh config with default values.
    """

    config:Config = ctx.obj["config"]
    config.save()
    log.info(f"Config defaults saved at {config.output_path}/config.json")


@cli.command()
@click.pass_context
def clear_cache(ctx):
    """
    Clears the requests cache stored in mdlout/cache directory.
    """
    cache_dir = ctx.obj["config"].output_path / "cache"

    if not os.path.exists(cache_dir):
        log.error("Cache directory does not exist in the given location.")
        return
    
    shutil.rmtree(cache_dir)
    log.info("Cleared omegadl cache.")


@cli.command(name="version")
def display_version():
    """
    Displays the version of omegadl
    """
    click.echo(f"omegadl Version 0.1")
    click.echo(f"View project on Github: https://github.com/sortedcord/omegadl")