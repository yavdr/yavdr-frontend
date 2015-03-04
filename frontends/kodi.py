#!/usr/bin/python3
#import dbus
#from dbus.mainloop.glib import DBusGMainLoop
#dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
from gi.repository import GObject
import logging
import os
import shlex
import subprocess
import time


class KODI():
    def __init__(self, main):
        self.main = main
        self.name = 'kodi'
        os.environ['__GL_SYNC_TO_VBLANK'] = "1"
        # TODO Display config:
        os.environ['__GL_SYNC_DISPLAY_DEVICE'] = os.environ['DISPLAY']
        cmd = self.main.settings.get_setting(
            'KODI', 'kodi',
            '/usr/lib/kodi/kodi.bin --standalone --lircdev /var/run/lirc/lircd'
        )
        self.shutdown_inhibitor = self.main.settings.get_setting(
            'KODI', 'shutdown_inhibitor', False)
        ae_sink = self.main.settings.get_setting('KODI', 'AE_SINK', "ALSA")
        os.environ['AE_SINK'] = ae_sink
        self.cmd = shlex.split(cmd)
        self.proc = None
        self.block = False
        logging.debug('kodi command: %s', self.cmd)

    def attach(self, options=None):
        logging.info('starting kodi')
        self.main.expect_stop = False
        if self.status() == 1:
            return
        if self.shutdown_inhibitor:
            try:
                # Shutdown inhibitor
                self.inhibitor = self.main.inhibit(
                    what="shutdown:sleep:idle",
                    who="frontend",
                    why="kodi running",
                    mode="block"
                )
            except:
                logging.warning("could not set shutdown-inhobitor")
        try:
            self.proc = subprocess.Popen(self.cmd, env=os.environ)
            if self.proc:
                self.block = True
            if self.proc.poll() is not None:
                logging.warning("failed to start kodi")
                self.main.switchFrontend()
            # Add callback on exit
            GObject.child_watch_add(self.proc.pid, self.on_exit, self.proc)
            logging.debug('started kodi')
        except:
            logging.exception('could not start kodi')
            return False
        return True

    def kill_kodi(self):
        logging.debug("trying to kill kodi")
        try:
            self.proc.kill()
            return False
        except:
            logging.exception("could not kill kodi")

    def on_exit(self, pid, condition, data):
        logging.debug("called function with pid=%s, condition=%s, data=%s",
                      pid, condition, data)
        snd_free = False
        while not snd_free:
            logging.debug("check if kodi has freed sound device")
            fuser_pid = subprocess.Popen(['fuser', '-v',
                                          '/dev/snd/*p'],
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE, shell=True)
            fuser_pid.wait()
            stdout, stderr = fuser_pid.communicate()
            if "kodi" in str(stderr):
                snd_free = False
                time.sleep(0.25)
            else:
                snd_free = True
                logging.debug('kodi has freed sound device')
        self.block = False
        if not self.main.external:
            if condition == 0:
                logging.info("normal kodi exit")
                if self.main.current == 'kodi':
                    logging.debug("normal KODI exit")
                    if not self.main.external and not self.main.expect_stop:
                        self.main.switchFrontend()
                        self.main.completeFrontendSwitch()
                else:
                    logging.debug("call completeFrontendSwitch")
                    self.main.completeFrontendSwitch()
            elif condition < 16384:
                logging.warn("abnormal exit: %s", condition)
                if (self.main.current == "kodi" and
                        self.main.settings.frontend == "kodi"):
                    logging.debug("resume kodi after crash")
                    self.main.frontends[self.main.current].resume()
                elif self.main.current == "kodi":
                    logging.debug("switch frontend after crash")
                    self.main.switchFrontend()
                else:
                    logging.debug("complete switch to other frontend")
                    self.main.completeFrontendSwitch()
            elif condition == 16384:
                logging.info("KODI want's a shutdown")
                self.main.switchFrontend()
                #TODO: Remote handling
                self.main.wants_shutdown = True
                self.main.dbus2vdr.Remote.HitKey("Power")
            elif condition == 16896:
                logging.info("KODI wants a reboot")
                #logging.info(self.main.powermanager.restart())
                # TODO: Reboot implementation via logind?
            else:
                logging.warn("abnormal exit: %s", condition)
                if (self.main.current == "kodi" and
                        self.main.settings.frontend == "kodi"):
                    logging.debug("resume kodi after crash")
                    self.main.frontends[self.main.current].resume()
                elif self.main.current == "kodi":
                    logging.debug("switch frontend after crash")
                    self.main.switchFrontend()
                else:
                    logging.debug("complete switch to other frontend")
                    self.main.completeFrontendSwitch()
                self.main.switchFrontend()
        try:
            os.close(self.inhibitor.take())
        except:
            pass
        try:
            GObject.source_remove(self.killtimer)
        except:
            pass
        self.kiltimer = None

    def detach(self, active=0):
        logging.info('stopping kodi')
        try:
            self.proc.terminate()
            logging.debug('sending terminate signal')
            self.proc.wait()
        except:
            logging.info('kodi already terminated')
        self.killtimer = GObject.timeout_add(2000, self.kill_kodi)

    def status(self):
        try:
            logging.debug("kodi status is %s, self.block is %s" %
                          (self.proc.poll(), self.block))
        except:
            logging.debug("kodi not running, self.block is %s", self.block)
        if self.proc is None:
            return 0
        elif not self.block:
            return 0
        elif self.block:
            logging.debug("self.block is True: kodi is running")
            return 1
        else:
            logging.debug("self.block is False: kodi is not running")
            return 0

    def resume(self):
        if self.proc and self.proc.poll() is None:
            logging.debug("kodi already running")
        else:
            self.attach()
