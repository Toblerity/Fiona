"""$ fiona ls"""


import json

import click
from cligj import indent_opt

import fiona


@click.command()
@click.argument('input', required=True)
@indent_opt
@click.pass_context
def ls(ctx, input, indent):

    """
    List layers in a datasource.
    """

    with ctx.obj['env']:
        result = fiona.listlayers(input)
        click.echo(json.dumps(result, indent=indent))
