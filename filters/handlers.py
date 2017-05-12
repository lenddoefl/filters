# coding=utf-8
from __future__ import absolute_import, division, print_function, \
    unicode_literals

import sys
from collections import OrderedDict
from logging import ERROR, Logger, LoggerAdapter
from traceback import format_exc
from types import TracebackType
from typing import Any, Dict, List, Text, Tuple, Union

from six import iteritems, python_2_unicode_compatible, text_type

from filters.base import BaseFilter, BaseInvalidValueHandler, FilterCompatible

__all__ = [
    'FilterMessage',
    'FilterRunner',
    'LogHandler',
    'MemoryHandler',
]


class LogHandler(BaseInvalidValueHandler):
    """
    Invalid value handler that sends the details to a logger.
    """
    def __init__(self, logger, level=ERROR):
        # type: (Union[Logger, LoggerAdapter], int) -> None
        """
        :param logger: The logger that log messages will get sent to.
        :param level: Level of the logged messages.
        """
        super(LogHandler, self).__init__()

        self.logger = logger
        self.level  = level

    def handle_invalid_value(self, message, exc_info, context):
        self.logger.log(
            level       = self.level,
            msg         = message,
            exc_info    = exc_info,
            extra       = {'context': context}
        )


@python_2_unicode_compatible
class FilterMessage(object):
    """Provides a consistent API for messages sent to MemoryHandler."""
    def __init__(self, message, context, exc_info=None):
        # type: (Text, dict, Text) -> None
        """
        :param exc_info: Exception traceback (if applicable).
        """
        super(FilterMessage, self).__init__()

        self.message    = message
        self.context    = context
        self.code       = context.get('code') or message
        self.exc_info   = exc_info

    def __repr__(self):
        return '{type}({message}, {context})'.format(
            type    = type(self).__name__,
            message = repr(self.message),
            context = repr(self.context),
        )

    def __str__(self):
        return self.message

    def as_dict(self, with_debug_info=False):
        # type: (bool) -> dict
        """
        Returns a dict representation of the FilterMessage.

        :param with_debug_info:
            Whether to include context and exception traceback in the
            result.
        """
        res = {
            'code':     self.code,
            'message':  self.message,
        }

        if with_debug_info:
            res['context']  = self.context
            res['exc_info'] = self.exc_info

        return res


class MemoryHandler(BaseInvalidValueHandler):
    """Invalid value handler that stores messages locally."""
    def __init__(self, capture_exc_info=False):
        # type: (bool) -> None
        """
        :param capture_exc_info:
            Whether to capture `sys.exc_info` when an handling an
            exception.

            This is turned off by default to reduce memory usage, but
            it is useful in certain cases (e.g., if you want to send
            exceptions to a logger that expect exc_info).

            Regardless, you can still check ``self.has_exceptions`` to
            see if an exception occurred.
        """
        super(MemoryHandler, self).__init__()

        self.messages           = OrderedDict() # type: Union[OrderedDict, Dict[Text, List[FilterMessage]]]
        self.has_exceptions     = False
        self.capture_exc_info   = capture_exc_info
        self.exc_info           = [] # type: List[Tuple[type, Exception, TracebackType]]

    def handle_invalid_value(self, message, exc_info, context):
        key = context.get('key', '')
        msg = FilterMessage(
            message     = message,
            context     = context,
            exc_info    = format_exc() if exc_info else None,
        )

        try:
            self.messages[key].append(msg)
        except KeyError:
            self.messages[key] = [msg]

    def handle_exception(self, message, exc):
        self.has_exceptions = True

        if self.capture_exc_info:
            self.exc_info.append(sys.exc_info())

        return super(MemoryHandler, self).handle_exception(message, exc)


@python_2_unicode_compatible
class FilterRunner(object):
    """
    Wrapper for a filter that provides an API similar to what you would
    expect from a Django form (at least, when it comes to methods
    related to data validation).

    Note that FilterRunner is intended to be a "one-shot" tool; once
    initialized, it does not expect the data it is filtering to
    change.
    """
    def __init__(self, starting_filter, incoming_data, capture_exc_info=False):
        # type: (FilterCompatible, Any, bool) -> None
        """
        :param incoming_data: E.g., `request.POST`.

        :param capture_exc_info:
            Whether to capture `sys.exc_info` when an handling an
            exception.

            This is turned off by default to reduce memory usage, but
            it is useful in certain cases (e.g., if you want to send
            exceptions to a logger).

            Regardless, you can still check ``self.has_exceptions`` to
            see if an exception occurred.
        """
        super(FilterRunner, self).__init__()

        self.filter_chain       = BaseFilter.resolve_filter(starting_filter) # type: FilterCompatible
        self.data               = incoming_data
        self.capture_exc_info   = capture_exc_info

        self._cleaned_data  = None
        self._handler       = None # type: MemoryHandler


    def __str__(self):
        return text_type(self.filter_chain)

    @property
    def cleaned_data(self):
        """
        Returns the resulting value after applying the request filter.
        """
        self.full_clean()
        return self._cleaned_data

    @property
    def errors(self):
        # type: () -> Dict[Text, List[Dict[Text, Text]]]
        """
        Returns a dict of error messages generated by the Filter, in a
        format suitable for inclusion in e.g., an API 400 response
        payload.

        E.g.::

            {
                'authToken': [
                    {
                        'code':     'not_found',
                        'message':
                            'No AuthToken found matching this value.',
                    },
                ],

                'data.foobar': [
                    {
                        'code':     'unexpected',
                        'message':  'Unexpected key "foobar".',
                    },
                ],

                # etc.
            }
        """
        return self.get_errors()

    def get_errors(self, with_context=False):
        # type: (bool) -> Dict[Text, List[Dict[Text, Text]]]
        """
        Returns a dict of error messages generated by the Filter, in a
        format suitable for inclusion in e.g., an API 400 response
        payload.

        :param with_context:
            Whether to include the context object in the result (for
            debugging purposes).

            Note: context is usually not safe to expose to end users!
        """
        return {
            key: [m.as_dict(with_context) for m in messages]
                for key, messages in iteritems(self.filter_messages)
        }

    @property
    def error_codes(self):
        # type: () -> Dict[Text, List[Text]]
        """
        Returns a dict of error codes generated by the Filter.
        """
        return {
            key: [m.code for m in messages]
                for key, messages in iteritems(self.filter_messages)
        }

    @property
    def has_exceptions(self):
        # type: () -> bool
        """
        Returns whether any unhandled exceptions occurred while
        filtering the value.
        """
        self.full_clean()
        return self._handler.has_exceptions

    @property
    def exc_info(self):
        # type: () -> List[Tuple[type, Exception, TracebackType]]
        """
        Returns tracebacks from any exceptions that were captured.
        """
        self.full_clean()
        return self._handler.exc_info

    @property
    def filter_messages(self):
        # type: () -> Dict[Text, List[FilterMessage]]
        """
        Returns the raw FilterMessages that were generated by the
        Filter.
        """
        self.full_clean()
        return self._handler.messages

    def is_valid(self):
        # type: () -> bool
        """
        Returns whether the request payload successfully passed the
        filter.
        """
        return not self.filter_messages

    def full_clean(self):
        """Applies the filter to the request data."""
        if self._handler is None:
            self._handler = MemoryHandler(self.capture_exc_info)

            # Inject our own handler (temporarily) while the Filter
            # runs so we can capture error messages.
            prev_handler = self.filter_chain.handler
            self.filter_chain.handler = self._handler
            try:
                self._cleaned_data = self.filter_chain.apply(self.data)
            finally:
                self.filter_chain.handler = prev_handler
