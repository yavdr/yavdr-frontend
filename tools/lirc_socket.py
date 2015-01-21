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
                    logging.debug("lirc_socket.py: remove callback function")
                    GObject.source_remove(self.callback)
            except:
                logging.exception(
                    "vdr-frontend could not connect to lircd socket")
                pass
            return False

    def read_from_socket(self, sock):
        buf = sock.recv(1024)
        if not buf:
            logging.debug("read_from_socket(): call reset_lirc")
            self.reset_lirc(sock)
        else:
            return buf

    def reset_lirc(self, sock):
        sock.close()
        try:
            GObject.source_remove(self.callback)
        except:
            pass
        logging.exception('retry lirc connection')
        self.try_connection()

    def handler(self, sock, *args):
        '''callback function for activity on lircd socket'''
        try:
            buf = self.read_from_socket(sock)
        except:
            logging.debug("handler: call reset_lirc")
            self.reset_lirc()
        lines = buf.decode().split("\n")
        for line in lines:
            if len(line) > 0:
                try:
                    self.get_key(line)
                except:
                    logging.exception("could not parse: %s" % line)
        return True

    def get_key(self, line):
            logging.debug("got a key press")
            logging.debug("line: %s" % line)
            code, count, cmd, device = line.split(" ")[:4]
            timestamp = self.last_ts
            previous_key = self.last_key
            self.last_key = cmd
            self.last_ts = time.time()
            if count != "0":
                logging.debug('repeated keypress')
                return
            elif (self.last_ts - timestamp < self.delta_t and
                  self.last_key == previous_key):
                logging.debug('ignoring keypress within min_delta')
            else:
                try:
                    logging.debug("remove main.timer")
                    GObject.source_remove(self.main.timer)
                except:
                    logging.debug("could not remove timer")
                logging.debug('Key press: %s', cmd)
                self.key_action(code, count, cmd, device)

    def key_action(self, code, count, cmd, device):
            logging.debug("current frontend: %s", self.main.current)
            if self.main.current == 'vdr':
                self.vdr_key_action(code, count, cmd, device)
            elif self.main.current == 'xbmc':
                self.xbmc_key_action(code, count, cmd, device)
            else:
                logging.debug("keypress for other frontend")
                logging.debug("current frontend is: %s" % self.main.current)
                logging.debug("vdrStatus is: %s" % self.main.vdrStatus)
                logging.debug("frontend status is: %s" % self.main.status())

    def vdr_key_action(self, code, count, cmd, device):
        logging.debug("keypress for vdr")
        if cmd == self.main.settings.get_setting("Frontend",
                                                 "lirc_toggle", None):
            logging.debug("lirc_socket.py: toggleFrontend")
            self.main.toggleFrontend()
        elif cmd == self.main.settings.get_setting("Frontend",
                                                   'lirc_switch', None):
            logging.debug("lirc_socket.py: switchFrontend")
            self.main.switchFrontend()

        elif cmd == self.main.settings.get_setting("Frontend",
                                                   'lirc_power', None):
            if self.main.status() == 1:
                self.main.timer = GObject.timeout_add(15000,
                                                      self.main.soft_detach)
            else:
                self.main.send_shutdown()
        elif self.main.status() != 1:
            logging.debug("main status is: %s" % self.main.status)
            self.main.resume()
        else:
            logging.debug("lic_socket.py: no action necessary")

    def xbmc_key_action(self, code, count, cmd, device):
        logging.debug("keypress for xbmc")
        if cmd == self.main.settings.get_setting("Frontend",
                                                 'lirc_switch',
                                                 None):
            logging.info('lirc_socket.py: switch from XBMC to VDR')
            self.main.switchFrontend()
        elif cmd == self.main.settings.get_setting("Frontend",
                                                   'lirc_power',
                                                   None):
            if self.main.status() == 1:
                self.main.wants_shutdown = True
                self.main.init_shutdown()
                self.main.timer = GObject.timeout_add(
                    15000, self.main.soft_detach)
        return True
