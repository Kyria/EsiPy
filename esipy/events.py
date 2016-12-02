# -*- encoding: utf-8 -*-
import logging
import sys

logger = logging.getLogger("esipy.events")


class Signal(object):
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
            except Exception as err:
                if not hasattr(err, '__traceback__'):
                    logger.error(sys.exc_info()[2])
                else:
                    logger.error(err.__traceback__)


# define required alarms
after_token_refresh = Signal()
