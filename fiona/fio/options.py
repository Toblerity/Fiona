"""Common commandline options for `fio`"""


import os.path

import click


src_crs_opt = click.option('--src-crs', '--src_crs', help="Source CRS.")
dst_crs_opt = click.option('--dst-crs', '--dst_crs', help="Destination CRS.")


def validate_vfs(ctx, param, value):
    """Validate vfs scheme and path"""
    if not value:
        ctx.obj['vfs'] = None
        return value
    try:
        scheme, archive = value.split('://')
        if not scheme in ('tar', 'zip'):
            raise click.BadParameter(
                "'{0}' is not a valid archive scheme".format(scheme))
        if not os.path.exists(archive):
            raise click.BadParameter(
                "no such archive '{0}' ".format(archive))
        ctx.obj['vfs'] = value
        return value
    except ValueError as err:
        raise click.BadParameter("must match 'scheme://path'")

vfs_opt = click.option(
    '--vfs', default=None, callback=validate_vfs, is_eager=True,
    help="Read files within a zip:// or tar:// archive")


def validate_input_path(ctx, param, value):
    if not ctx.obj.get('vfs'):
        if not os.path.exists(value):
            raise click.BadParameter(
                "no such file '{0}' ".format(value))
    return value

input_path_arg = click.argument('input', callback=validate_input_path)
