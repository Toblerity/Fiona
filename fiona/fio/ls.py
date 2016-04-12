import json

import fiona

import click
from cligj import indent_opt


@click.command()
@click.argument('input', type=click.Path(exists=True))
@indent_opt
def ls(input, indent):

    """
    List layers in a datasource.
    """

    result = fiona.listlayers(input)
    click.echo(json.dumps(result, indent=indent))
