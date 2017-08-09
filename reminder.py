from kivy.utils import platform

from jnius import autoclass


def remind():
    if platform != 'android':
        raise NotImplementedError('Setting calendar reminders is only supported on Android')
    # noinspection PyPep8Naming
    Reminder = autoclass('edu.sepsis.cse.soft162.Reminder')
    success = Reminder.remind()
    if not success:
        raise NotImplementedError('Unable to find phone app')
