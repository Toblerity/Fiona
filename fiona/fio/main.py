#!/usr/bin/env python
# main: loader of all the command entry points.


from pkg_resources import iter_entry_points

from fiona.fio.cli import cli


# Find and load all entry points in the fiona.rio_commands group.
# This includes the standard commands included with Fiona as well
# as commands provided by other packages.
#
# At a mimimum, commands must use the fiona.fio.cli.cli command
# group decorator like so:
#
#   from fiona.fio.cli import cli
#
#   @cli.command()
#   def foo(...):
#       ...

for entry_point in iter_entry_points('fiona.fio_commands'):
    entry_point.load()
