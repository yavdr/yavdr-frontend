#!/usr/bin/python3
# vim: set fileencoding=utf-8 :
# Alexander Grothe 2012

from gi.repository import GObject
import logging
import socket
#import string
import time
from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)


class lircConnection():
    def __init__(self, main):
        self.main = main
        self.main.timer = None
        self.socket_path = self.main.settings.get_setting('Frontend',
                                                          'lirc_socket',
                                                          None)
        self.delta_t = self.main.settings.get_settingf('Frontend',
                                                       'lirc_repeat', 0.300)
        logging.debug("lirc_socket is {0}".format(self.socket_path))
        if self.socket_path is None:
            return
        self.try_connection()
        self.callback = None
        logging.debug("lirc_toggle = {0}".format(
            self.main.settings.get_setting("Frontend", "lirc_toggle", None)))
        logging.debug("lirc_switch = {0}".format(
            self.main.settings.get_setting("Frontend", "lirc_switch", None)))
        logging.debug("lirc_power = {0}".format(
            self.main.settings.get_setting("Frontend", "lirc_power", None)))
        self.last_key = None
        self.last_ts = time.time()
        self.min_delta = 0.300

    def connect_lircd(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(self.socket_path)
        self.callback = GObject.io_add_watch(self.sock, GObject.IO_IN,
                                             self.handler)

    def try_connection(self):
        logging.debug("try_connection")
        try:
            self.connect_lircd()
            logging.info("conntected to Lirc-Socket on %s" % (self.socket_path)
                         )
            return False
        except:
            GObject.timeout_add(1000, self.try_connection)
            try:
                if self.callback:
                    GObject.source_remove(self.callback)
            except:
                logging.exception(
                    "vdr-frontend could not connect to lircd socket")
                pass
            return False

    def handler(self, sock, *args):
        '''callback function for activity on lircd socket'''
        try:
            buf = sock.recv(1024)
            if not buf:
                self.sock.close()
                try:
                    if self.callback:
                        logging.debug("remove callback for lircd socket")
                        GObject.source_remove(self.callback)
                except:
                    pass
                logging.error("Error reading from lircd socket")
                self.try_connection()
                return False
        except:
            sock.close()
            try:
                GObject.source_remove(self.callback)
            except:
                pass
            logging.exception('retry lirc connection')
            self.try_connection()
            return True
        lines = buf.decode().split("    n")
        for line in lines:
            logging.debug("got a key press")
            try:
                code, count, cmd, device = line.split(" ")[:4]
                timestamp = self.last_ts
                previous_key = self.last_key
                self.last_key = cmd
                self.last_ts = time.time()
                if count != "0":
                    logging.debug('repeated keypress')
                    return True
                elif (self.last_ts - timestamp < self.delta_t and
                      self.last_key == previous_key):
                    logging.debug('ignoring keypress within min_delta')
                    return True
                else:
                    try:
                        logging.debug("remove main.timer")
                        GObject.source_remove(self.main.timer)
                    except:
                        #pass
                        logging.debug("could not remove timer")
            except:
                logging.exception(line)
                return True
            logging.debug('Key press: %s', cmd)
            logging.debug("current frontend: %s", self.main.current)
            if self.main.current == 'vdr':
                logging.debug("keypress for vdr")
                if cmd == self.main.settings.get_setting("Frontend",
                                                         "lirc_toggle", None):
                    if self.main.status() == 1:
                        self.main.detach()
                    else:
                        self.main.frontends[self.main.current].resume()
                    return True
                elif cmd == self.main.settings.get_setting("Frontend",
                                                           'lirc_switch',
                                                           None):
                    logging.debug("lirc.py: switchFrontend")
                    self.main.switchFrontend()
                    return True

                elif cmd == self.main.settings.get_setting("Frontend",
                                                           'lirc_power', None):
                    if self.main.status() == 1:
                        if self.main.current == 'xbmc':
                            self.main.init_shutdown()
                        else:
                            self.main.timer = GObject.timeout_add(
                            15000, self.main.soft_detach)
                    else:
                        self.main.send_shutdown()
                elif self.main.status != 1:
                    self.main.resume()
            elif self.main.current == 'xbmc':
                logging.debug("keypress for xbmc")
                if cmd == self.main.settings.get_setting("Frontend",
                                                         'lirc_switch',
                                                         None):
                    logging.info('stop XBMC via remote lirc_xbmc')
                    self.main.switchFrontend()
                    return True
                elif cmd == self.main.settings.get_setting("Frontend",
                                                           'lirc_power',
                                                           None):
                    if self.main.status() == 1:
                        self.main.wants_shutdown = True
                        self.main.timer = GObject.timeout_add(
                            15000, self.main.soft_detach)
        return True
