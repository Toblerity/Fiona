"""$ fiona ls"""


import json

import click
from cligj import indent_opt

import fiona
from fiona.fio import with_context_env


@click.command()
@click.argument('input', required=True)
@indent_opt
@click.pass_context
@with_context_env
def ls(ctx, input, indent):
    """
    List layers in a datasource.
    """
    result = fiona.listlayers(input)
    click.echo(json.dumps(result, indent=indent))
