# -*- encoding: utf-8 -*-
# pylint: skip-file
from esipy.events import Signal

import unittest


class TestSignal(unittest.TestCase):
    EVENT_ARG = "testing"

    def event_receiver(self, example_arg):
        self.assertEqual(example_arg, TestSignal.EVENT_ARG)

    def event_receiver_exception(self):
        raise AssertionError("Triggered")

    def setUp(self):
        self.signal = Signal()

    def test_signal_send(self):
        self.signal.add_receiver(self.event_receiver)
        self.signal.send(example_arg=TestSignal.EVENT_ARG)

    def test_signal_send_exception(self):
        self.signal.add_receiver(self.event_receiver_exception)
        with self.assertRaises(AssertionError):
            self.signal.send()

    def test_signal_send_robust(self):
        self.signal.add_receiver(self.event_receiver)
        self.signal.send_robust(example_arg=TestSignal.EVENT_ARG)

    def test_signal_send_robust_exception(self):
        self.signal.add_receiver(self.event_receiver_exception)
        self.signal.send_robust()

    def test_signal_add_remove_receiver(self):
        self.signal.add_receiver(self.event_receiver_exception)
        self.assertIn(
            self.event_receiver_exception,
            self.signal.event_receivers
        )
        self.signal.remove_receiver(self.event_receiver_exception)
        self.assertNotIn(
            self.event_receiver_exception,
            self.signal.event_receivers
        )

    def test_signal_add_not_callable_receiver(self):
        with self.assertRaises(TypeError):
            self.signal.add_receiver("No callable receiver")
