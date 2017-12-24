# -*- encoding: utf-8 -*-
""" Event / Signal definition. Signals are used to hook methods
to some defined event within EsiPy for the user to be able to do
specific actions at some times """
import logging
import sys

LOGGER = logging.getLogger(__name__)


class Signal(object):
    """ Signal class. This class allows subscribers to hook to some specific
    event and be notified when something happen """

    def __init__(self):
        """ Alarm constructor. """
        self.event_receivers = []

    def add_receiver(self, receiver):
        """ Add a receiver to the list of receivers.

        :param receiver: a callable variable
        """
        if not callable(receiver):
            raise TypeError("receiver must be callable")
        self.event_receivers.append(receiver)

    def remove_receiver(self, receiver):
        """ Remove a receiver to the list of receivers.

        :param receiver: a callable variable
        """
        if receiver in self.event_receivers:
            self.event_receivers.remove(receiver)

    def send(self, **kwargs):
        """ Trigger all receiver and pass them the parameters
        If an exception is raised, it will stop the process and all receivers
        may not be triggered at this moment.

        :param kwargs: all arguments from the event.
        """
        for receiver in self.event_receivers:
            receiver(**kwargs)

    def send_robust(self, **kwargs):
        """ Trigger all receiver and pass them the parameters
        If an exception is raised it will be catched and displayed as error
        in the logger (if defined).

        :param kwargs: all arguments from the event.
        """
        for receiver in self.event_receivers:
            try:
                receiver(**kwargs)
            except Exception as err:  # pylint: disable=W0703
                if not hasattr(err, '__traceback__'):
                    LOGGER.error(sys.exc_info()[2])
                else:
                    LOGGER.error(getattr(err, '__traceback__'))


# define required alarms
AFTER_TOKEN_REFRESH = Signal()
API_CALL_STATS = Signal()
