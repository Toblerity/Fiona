"""$ fio load"""

from functools import partial

import click
import cligj

import fiona
from fiona.fio import options, with_context_env
from fiona.model import Feature, Geometry
from fiona.schema import FIELD_TYPES_MAP_REV
from fiona.transform import transform_geom


def _cb_key_val(ctx, param, value):
    """
    click callback to validate `--opt KEY1=VAL1 --opt KEY2=VAL2` and collect
    in a dictionary like the one below, which is what the CLI function receives.
    If no value or `None` is received then an empty dictionary is returned.

        {
            'KEY1': 'VAL1',
            'KEY2': 'VAL2'
        }

    Note: `==VAL` breaks this as `str.split('=', 1)` is used.

    """
    if not value:
        return {}
    else:
        out = {}
        for pair in value:
            if "=" not in pair:
                raise click.BadParameter(
                    f"Invalid syntax for KEY=VAL arg: {pair}"
                )
            else:
                k, v = pair.split("=", 1)
                k = k.lower()
                v = v.lower()
                out[k] = None if v.lower() in ["none", "null", "nil", "nada"] else v
        return out


@click.command(short_help="Load GeoJSON to a dataset in another format.")
@click.argument("output", required=True)
@click.option("-f", "--format", "--driver", "driver", help="Output format driver name.")
@options.src_crs_opt
@click.option(
    "--dst-crs",
    "--dst_crs",
    help="Destination CRS.  Defaults to --src-crs when not given.",
)
@cligj.features_in_arg
@click.option(
    "--layer",
    metavar="INDEX|NAME",
    callback=options.cb_layer,
    help="Load features into specified layer.  Layers use "
    "zero-based numbering when accessed by index.",
)
@click.option(
    "--co",
    "--profile",
    "creation_options",
    metavar="NAME=VALUE",
    multiple=True,
    callback=_cb_key_val,
    help="Driver specific creation options. See the documentation for the selected output driver for more information.",
)
@click.pass_context
@with_context_env
def load(ctx, output, driver, src_crs, dst_crs, features, layer, creation_options):
    """Load features from JSON to a file in another format.

    The input is a GeoJSON feature collection or optionally a sequence of
    GeoJSON feature objects.

    """
    dst_crs = dst_crs or src_crs

    if src_crs and dst_crs and src_crs != dst_crs:
        transformer = partial(
            transform_geom, src_crs, dst_crs, antimeridian_cutting=True
        )
    else:

        def transformer(x):
            return Geometry.from_dict(**x)

    def feature_gen():
        """Convert stream of JSON to features.

        Yields
        ------
        Feature

        """
        try:
            for feat in features:
                feat["geometry"] = transformer(Geometry.from_dict(**feat["geometry"]))
                yield Feature.from_dict(**feat)
        except TypeError:
            raise click.ClickException("Invalid input.")

    source = feature_gen()

    # Use schema of first feature as a template.
    # TODO: schema specified on command line?
    try:
        first = next(source)
    except TypeError:
        raise click.ClickException("Invalid input.")

    # print(first, first.geometry)
    schema = {"geometry": first.geometry.type}
    schema["properties"] = {
            k: FIELD_TYPES_MAP_REV.get(type(v)) or "str"
            for k, v in first.properties.items()
    }

    with fiona.open(
        output,
        "w",
        driver=driver,
        crs=dst_crs,
        schema=schema,
        layer=layer,
        **creation_options
    ) as dst:
        dst.write(first)
        dst.writerecords(source)
