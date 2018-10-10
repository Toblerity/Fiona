"""
Main click group for the CLI.  Needs to be isolated for entry-point loading.
"""


import logging
from pkg_resources import iter_entry_points
import sys

import click
from click_plugins import with_plugins
from cligj import verbose_opt, quiet_opt

import fiona
from fiona import __version__ as fio_version
from fiona.session import AWSSession, DummySession


def configure_logging(verbosity):
    log_level = max(10, 30 - 10 * verbosity)
    logging.basicConfig(stream=sys.stderr, level=log_level)


@with_plugins(ep for ep in list(iter_entry_points('fiona.fio_commands')) +
              list(iter_entry_points('fiona.fio_plugins')))
@click.group()
@verbose_opt
@quiet_opt
@click.option(
    "--aws-profile",
    help="Select a profile from the AWS credentials file")
@click.option(
    "--aws-no-sign-requests",
    is_flag=True,
    help="Make requests anonymously")
@click.option(
    "--aws-requester-pays",
    is_flag=True,
    help="Requester pays data transfer costs")
@click.version_option(fio_version)
@click.version_option(fiona.__gdal_version__, '--gdal-version',
                      prog_name='GDAL')
@click.version_option(sys.version, '--python-version', prog_name='Python')
@click.pass_context
def main_group(
        ctx, verbose, quiet, aws_profile, aws_no_sign_requests,
        aws_requester_pays):
    """Fiona command line interface.
    """
    verbosity = verbose - quiet
    configure_logging(verbosity)
    ctx.obj = {}
    ctx.obj["verbosity"] = verbosity
    ctx.obj["aws_profile"] = aws_profile
    envopts = {"CPL_DEBUG": (verbosity > 2)}
    if aws_profile or aws_no_sign_requests:
        session = AWSSession(
            profile_name=aws_profile,
            aws_unsigned=aws_no_sign_requests,
            requester_pays=aws_requester_pays,
        )
    else:
        session = DummySession()
    ctx.obj["env"] = fiona.Env(session=session, **envopts)
