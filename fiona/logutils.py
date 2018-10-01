"""Logging helper classes."""

import logging


class FieldSkipLogFilter(logging.Filter):
    """Filter field skip log messges.

    At most, one message per field skipped per loop will be passed.
    """

    def __init__(self, name=''):
        super(FieldSkipLogFilter, self).__init__(name)
        self.seen_msgs = set()

    def filter(self, record):
        """Pass record if not seen."""
        if getattr(record, 'msg', "").startswith("Skipping field"):
            msg = record.getMessage()
            retval = msg not in self.seen_msgs
            self.seen_msgs.add(msg)
            return retval
        else:
            return 1


class LogFiltering(object):

    def __init__(self, logger, filter):
        self.logger = logger
        self.filter = filter

    def __enter__(self):
        self.logger.addFilter(self.filter)

    def __exit__(self, *args, **kwargs):
        self.logger.removeFilter(self.filter)
