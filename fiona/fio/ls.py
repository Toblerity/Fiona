"""$ fiona ls"""


import json

import click
from cligj import indent_opt

import fiona


@click.command()
@click.argument('input', type=click.Path(exists=True))
@indent_opt
@click.pass_context
def ls(ctx, input, indent):

    """
    List layers in a datasource.
    """

    verbosity = (ctx.obj and ctx.obj['verbosity']) or 2

    with fiona.drivers(CPL_DEBUG=verbosity > 2):
        result = fiona.listlayers(input)
        click.echo(json.dumps(result, indent=indent))
