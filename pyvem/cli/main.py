import logging

import click

from pyvem.cli.containers import container
from pyvem.cli.ve_tools import delete, info, use, install, env_path, update_deps, run
from pyvem.constants import SUCCESS

logging.basicConfig()
logger = logging.getLogger()


@click.group()
@click.option("--debug", is_flag=True, default=False, help="Show debugging logs")
def entry_point(debug: bool):
    if debug:
        logger.setLevel(logging.DEBUG)


entry_point.add_command(container)

entry_point.add_command(delete)
entry_point.add_command(info)
entry_point.add_command(use)
entry_point.add_command(install)
entry_point.add_command(env_path)
entry_point.add_command(update_deps)
entry_point.add_command(run)


if __name__ == "__main__":
    entry_point()
    exit(SUCCESS)
