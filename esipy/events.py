# -*- encoding: utf-8 -*-


class BaseClientEventObserver(object):
    def notify_update(self, access_token, refresh_token, expires_in):
        """ Notify triggered when the token is updated automatically
        by the security object

        :param access_token: the new access_token
        :param refresh_token: the refresh token used
        :param expires_in: the validity of the access token in seconds
        """
        raise NotImplementedError


class Alarm(object):
    def __init__(self, observer_class):
        """ Alarm constructor.

        :param observer_class: the class expected for the observers
        """
        self.event_observers = []

        if not isinstance(observer_class, type):
            raise TypeError("observer_class must be a class")
        self.observer_class = observer_class

    def notify(self, notify_event, **kwargs):
        """ Call the notify_event on all observers and pass them the parameters

        :param notify_event: the notify event method to call
        :param kwargs: all required arguments depending on the notify_event.
        """

        for observer in self.event_observers:
            getattr(observer, notify_event)(**kwargs)

    def append(self, observer):
        """ Add an obserevr to the list of observers.

        :param observer: an instance of BaseObserver
        """
        if not isinstance(observer, self.observer_class):
            raise TypeError("Observer must be an instance of BaseObserver")
        self.event_observers.append(observer)


# define required alarms
client_alarm = Alarm(BaseClientEventObserver)
