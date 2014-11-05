#!/usr/bin/python3
from gi.repository import GObject
import logging
from frontends.base import vdrFrontend
import os
import socket
import subprocess
import time


class VDRsxfe(vdrFrontend):
    def __init__(self, main, dbus2vdr, path='/usr/bin/vdr-sxfe',
                 origin='127.0.0.1',
                 port='37890'):
        super().__init__(main, dbus2vdr)
        self.main = main
        self.origin = origin
        self.name = "xineliboutput"
        self.port = port
        self.mode = self.main.settings.get_setting('Xineliboutput',
                                                   'xineliboutput',
                                                   'remote')
        self.main.settings.get_settingb('Xineliboutput', 'autocrop', False)
        os.environ['__GL_SYNC_TO_VBLANK'] = "1"
        os.environ['__GL_SYNC_DISPLAY_DEVICE'] = os.environ['DISPLAY']
        self.cmd = self.main.settings.get_setting(
            "Xineliboutput",
            "xineliboutput_cmd",
            '''/usr/bin/vdr-sxfe --post tvtime:method=use_vo_driver \
            --audio=alsa \
            --syslog xvdr+tcp://{0}:{1}'''.format(origin, port)
        )
        self.proc = None
        self.block = False
        logging.debug('vdr-sxfe command: %s', self.cmd)
        self.state = 0

    def attach(self, options=None):
        if self.mode == 'remote' and self.status() == 0:
            while not self.isOpen():
                time.sleep(1)
            logging.info('starting vdr-sxfe')
            self.proc = subprocess.Popen("exec " + self.cmd, shell=True,
                                         env=os.environ)
            GObject.child_watch_add(self.proc.pid, self.on_exit,
                                    self.proc)  # Add callback on exit
            if self.proc:
                self.block = True
                logging.debug('started vdr-sxfe')
            if self.proc.poll() is not None:
                logging.warning("failed to start vdr-sxfe")
                return False
            else:
                logging.debug('vdr-sxfe is still running')
                self.state = 1
                return True
        elif self.mode == 'local' and self.status() == 0:
            self.main.dbus2vdr.Plugins.SVDRPCommand('xinelibputput', 'LFRO',
                                                    'sxfe')
            self.state = 1
            return True

    def detach(self, active=0):
        if self.mode == 'remote':
            logging.info('stopping vdr-sxfe')
            try:
                self.proc.kill()
                self.proc.wait()
                return True
            except:
                logging.info('vdr-sxfe already terminated')
            finally:
                self.proc = None
            #self.main.dbus2vdr.Remote.Disable()
        elif self.mode == 'local':
            self.main.dbus2vdr.Plugins.SVDRPCommand('xinelibputput', 'LFRO',
                                                    'none')
            self.state = 0
            return True

    def status(self):
        if self.mode == 'remote':
            if self.proc:
                return 1
            else:
                return 0
        elif self.mode == 'local':
            return self.state

    def resume(self):
        if self.mode == 'remote':
            if self.proc:
                pass
            else:
                self.attach()
        elif self.mode == 'local':
            if self.state == 0:
                self.attach()

    def on_exit(self, pid, condition, data):
        logging.debug("called function with pid=%s, condition=%s, data=%s",
                      pid, condition, data)
        self.state = 0
        logging.debug("vdr-sxfe exit code was: %s", condition)
        if condition == 0:
            self.main.detach()
            self.proc = None
        else:
            self.main.attach()

    def isOpen(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((self.origin, int(self.port)))
            s.shutdown(2)
            return True
        except:
            return False
