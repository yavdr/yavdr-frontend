#!/usr/bin/python3
#import dbus
#from dbus.mainloop.glib import DBusGMainLoop
#dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
import logging
from frontends.base import vdrFrontend
import os


class Softhddevice(vdrFrontend):
    def __init__(self, main, dbus2vdr, name="softhddevice"):
        super().__init__(main, dbus2vdr)

    def get_options(self):
        options = self.main.settings.get_setting('Softhddevice',
                                                      'options',
                                                      '-d {DISPLAY}')
        return options.format(DISPLAY=os.environ['DISPLAY'])

    def attach(self, options=None):
        try:
            if self.main.dbus2vdr.Shutdown.ConfirmShutdown()[0] == 901:
                user_active = True
            else:
                user_active = False
            if not options:
                options = self.get_options()
            code, result = self.main.dbus2vdr.Plugins.SVDRPCommand(
                "softhddevice", "atta", options)
            if code == 900 and self.status() == 1:
                logging.debug("softhddevice successfully attached")
                self.state = 1
                if (not user_active and self.main.settings.get_settingb(
                        'Softhddevice', 'keep_inactive', False)):
                    self.main.dbus2vdr.Shutdown.SetUserInactive()
                return True
            else:
                logging.debug(
                    "failed to attach softhddevice: {0}: {1}".format(code,
                                                                     result)
                )
                return False
        except Exception as error:
            logging.exception(error)
            return False

    def detach(self):
        try:
            code, result = self.main.dbus2vdr.Plugins.SVDRPCommand(
                "softhddevice",
                "deta")
            if code == 900 and self.status() == 0:
                logging.debug("softhddevice successfully detached")
                self.state = 0
                return True
            else:
                logging.debug("failed to detach softhddevice")
                return False
            return False
        except Exception as error:
            logging.exception(error)
            return False

    def resume(self):
        state = self.status()
        if state == 1:
            self.state = 1
        elif state == 2:
            try:
                code, result = self.main.dbus2vdr.Plugins.SVDRPCommand(
                    "softhddevice",
                    "resu")
                if code == 900 and self.status() == 1:
                    self.state = 1
                    logging.debug("resumed softhddevice successfully")
                else:
                    logging.debug("failed to resume softhddevice")
            except Exception as error:
                logging.exception(error)
        elif state == 0:
            self.attach()

    def status(self):
        code, result = self.main.dbus2vdr.Plugins.SVDRPCommand("softhddevice",
                                                               "stat")
        if code == 910:
            state = 1
        elif code == 911:
            state = 2
        elif code == 912:
            state = 0
        return state
