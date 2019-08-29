import logging
import sys
import typing
from logging import WARNING, getLevelName
from traceback import format_exc, format_exception
from unittest import TestCase

import filters as f
from filters.base import ExceptionHandler


class ExceptionHandlerTestCase(TestCase):
    def setUp(self):
        super(ExceptionHandlerTestCase, self).setUp()

        self.handler = ExceptionHandler()

    def test_invalid_value(self):
        """
        Sends an invalid value to the handler.
        """
        message = 'Needs more cowbell.'
        context = {
            'key': 'test',
            'value': "(Don't Fear) The Reaper",
        }

        # When ExceptionHandler encounters an invalid value, it raises
        # an exception.
        # The exception always has the same type (FilterError) so that
        # the caller can capture it.
        with self.assertRaises(f.FilterError) as exc:
            self.handler.handle_invalid_value(message, False, context)

        self.assertEqual(str(exc.exception), message)
        self.assertEqual(exc.exception.context, context)

    def test_exception(self):
        """
        Sends an exception to the handler.
        """
        message = 'An exception occurred!'
        context = {
            'key': 'test',
            'value': "(Don't Fear) The Reaper",
        }

        #
        # ExceptionHandler converts any exception it encounters into a
        # FilterError.
        # The exception always has the same type (FilterError) so that
        # the caller can capture it.
        #
        # Note that the FilterError completely replaces the original
        # exception, but it leaves the traceback intact.
        # To make things more convenient, Filters add the exception
        # info to the context dict, but you can still use
        # `sys.exc_info()[2]` to inspect the original exception's
        # stack.
        #
        # :see: importer.core.f.BaseFilter._invalid_value
        #
        try:
            # Raise an exception so that the handler has a traceback to
            # work with.
            # Note that the ValueError's message will get replaced (but
            # it can still be accessed via the traceback).
            exc = ValueError('Needs more cowbell.')
            exc.context = context
            raise exc
        except ValueError as e:
            with self.assertRaises(f.FilterError) as ar_context:
                self.handler.handle_exception(message, e)

            self.assertEqual(str(ar_context.exception), message)
            self.assertEqual(ar_context.exception.context, context)


class MemoryLogHandler(logging.Handler):
    """
    A log handler that retains all of its records in a list in memory,
    so that we can test :py:class:`LogHandler`.

    This class is similar in function (though not in purpose) to
    BufferingHandler.

    References:
      - :py:class:`logging.handlers.BufferingHandler`
    """

    def __init__(self, level: int = logging.NOTSET) -> None:
        super(MemoryLogHandler, self).__init__(level)

        self._records = []  # type: typing.List[logging.LogRecord]
        self.max_level_emitted = logging.NOTSET

    def __getitem__(self, index: int) -> logging.LogRecord:
        """
        Returns the log message at the specified index.
        """
        return self._records[index]

    def __iter__(self) -> typing.Iterator[logging.LogRecord]:
        """
        Creates an iterator for the collected records.
        """
        return iter(self._records)

    def __len__(self):
        """
        Returns the number of log records collected.
        """
        return len(self._records)

    @property
    def records(self) -> typing.List[logging.LogRecord]:
        """
        Returns all log messages that the handler has collected.
        """
        return self._records[:]

    def clear(self):
        """
        Removes all log messages that this handler has collected.
        """
        del self._records[:]

    def emit(self, record: logging.LogRecord) -> None:
        """
        Records the log message.
        """
        # Remove `exc_info` to reclaim memory.
        if record.exc_info:
            if not record.exc_text:
                record.exc_text = ''.join(format_exception(*record.exc_info))

            record.exc_info = None

        self._records.append(record)
        self.max_level_emitted = max(self.max_level_emitted, record.levelno)


class LogHandlerTestCase(TestCase):
    def setUp(self):
        super(LogHandlerTestCase, self).setUp()

        self.logs = MemoryLogHandler()

        logger = logging.getLogger(__name__)
        logger.addHandler(self.logs)
        logger.setLevel(logging.DEBUG)

        self.handler = f.LogHandler(logger, WARNING)

    def test_invalid_value(self):
        """
        Sends an invalid value to the handler.
        """
        message = 'Needs more cowbell.'
        context = {
            'key':   'test',
            'value': "(Don't Fear) The Reaper",
        }

        self.handler.handle_invalid_value(message, False, context)

        self.assertEqual(len(self.logs.records), 1)
        self.assertEqual(self.logs[0].msg, message)
        self.assertEqual(getattr(self.logs[0], 'context'), context)

        # The log message level is set in the handler's initializer.
        self.assertEqual(self.logs[0].levelname, getLevelName(WARNING))

        # No exception info for invalid values (by default).
        self.assertIsNone(self.logs[0].exc_text)

    def test_exception(self):
        """
        Sends an exception to the handler.
        """
        message = 'An exception occurred!'
        context = {
            'key':   'test',
            'value': "(Don't Fear) The Reaper",
        }

        try:
            # Raise an exception so that the handler has a traceback to
            # work with.
            # Note that the ValueError's message will get replaced (but
            # it can still be accessed via the traceback).
            exc = ValueError('Needs more cowbell.')
            exc.context = context
            raise exc
        except ValueError as e:
            original_traceback = format_exc()

            self.handler.handle_exception(message, e)

            self.assertEqual(len(self.logs.records), 1)

            self.assertEqual(len(self.logs.records), 1)
            self.assertEqual(self.logs[0].msg, message)
            self.assertEqual(getattr(self.logs[0], 'context'), context)

            # The log message level is set in the handler's
            # initializer.
            # Note that both invalid values and exceptions have the
            # same log level.
            self.assertEqual(self.logs[0].levelname, getLevelName(WARNING))

            # Traceback is captured for exceptions.
            self.assertEqual(self.logs[0].exc_text, original_traceback)


class MemoryHandlerTestCase(TestCase):
    def setUp(self):
        super(MemoryHandlerTestCase, self).setUp()

        self.handler = f.MemoryHandler()

    def test_invalid_value(self):
        """
        Sends an invalid value to the handler.
        """
        code = 'foo'
        key = 'test'
        message = 'Needs more cowbell.'
        context = {
            'code':  code,
            'key':   key,
            'value': "(Don't Fear) The Reaper",
        }

        self.handler.handle_invalid_value(message, False, context)

        # Add a couple of additional messages, just to make sure the
        # handler stores them correctly.
        self.handler.handle_invalid_value(
            message='Test message 1',
            exc_info=False,
            context={'key': key},
        )
        self.handler.handle_invalid_value('Test message 2', False, {})

        # As filter messages are captured, they are sorted according to
        # their contexts' ``key`` values.
        # If a message doesn't have a ``key`` value, an empty string is
        # used.
        self.assertListEqual(sorted(self.handler.messages.keys()), ['', key])

        filter_message_0 = self.handler.messages[key][0]
        self.assertIsInstance(filter_message_0, f.FilterMessage)
        self.assertEqual(filter_message_0.code, code)
        self.assertEqual(filter_message_0.message, message)
        self.assertEqual(filter_message_0.context, context)
        self.assertIsNone(filter_message_0.exc_info)

        filter_message_1 = self.handler.messages[key][1]
        self.assertIsInstance(filter_message_1, f.FilterMessage)
        self.assertEqual(filter_message_1.code, 'Test message 1')
        self.assertEqual(filter_message_1.message, 'Test message 1')
        self.assertEqual(filter_message_1.context, {'key': key})
        self.assertIsNone(filter_message_1.exc_info)

        filter_message_blank = self.handler.messages[''][0]
        self.assertIsInstance(filter_message_blank, f.FilterMessage)
        self.assertEqual(filter_message_blank.code, 'Test message 2')
        self.assertEqual(filter_message_blank.message, 'Test message 2')
        self.assertEqual(filter_message_blank.context, {})
        self.assertIsNone(filter_message_blank.exc_info)

        self.assertFalse(self.handler.has_exceptions)
        self.assertListEqual(self.handler.exc_info, [])

    def test_exception(self):
        """
        Sends an exception to the handler.
        """
        code = 'error'
        key = 'test'
        message = 'An exception occurred!'
        context = {
            'code':  code,
            'key':   key,
            'value': "(Don't Fear) The Reaper",
        }

        try:
            # Raise an exception so that the handler has a traceback to
            # work with.
            # Note that the ValueError's message will get replaced (but
            # it can still be accessed via the traceback).
            exc = ValueError('Needs more cowbell.')
            exc.context = context
            raise exc
        except ValueError as e:
            original_traceback = format_exc()

            self.handler.handle_exception(message, e)

            self.assertListEqual(list(self.handler.messages.keys()), [key])

            filter_message_0 = self.handler.messages[key][0]
            self.assertIsInstance(filter_message_0, f.FilterMessage)
            self.assertEqual(filter_message_0.code, code)
            self.assertEqual(filter_message_0.message, message)
            self.assertEqual(filter_message_0.context, context)

            # Exception traceback is captured automatically.
            self.assertEqual(filter_message_0.exc_info, original_traceback)

            self.assertTrue(self.handler.has_exceptions)

            # By default, the handler does NOT keep the traceback
            # object.
            # :see: test_capture_exc_info
            self.assertListEqual(self.handler.exc_info, [])

    def test_capture_exc_info(self):
        """
        The handler is configured to capture :py:func:`sys.exc_info` in
        the event of an exception.

        This is generally turned off because the filter already
        captures a formatted traceback in the event of an
        exception, so there is no need to store the raw traceback
        object.

        However, there are a few cases where it is useful to collect
        this, such as when you want to send exceptions to a logger
        that expects `sys.exc_info()`.
        """
        self.handler.capture_exc_info = True

        try:
            # Raise an exception so that the handler has a traceback to
            # work with.
            raise ValueError('I gotta have more cowbell, baby!')
        except ValueError as e:
            self.handler.handle_exception('An exception occurred!', e)

            self.assertTrue(self.handler.has_exceptions)
            self.assertListEqual(self.handler.exc_info, [sys.exc_info()])
