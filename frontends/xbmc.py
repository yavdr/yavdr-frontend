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


class XBMC():
    def __init__(self, main):
        self.main = main
        self.name = 'xbmc'
        os.environ['__GL_SYNC_TO_VBLANK'] = "1"
        # TODO Display config:
        os.environ['__GL_SYNC_DISPLAY_DEVICE'] = os.environ['DISPLAY']
        cmd = self.main.settings.get_setting(
            'XBMC', 'xbmc',
            '/usr/lib/xbmc/xbmc.bin --standalone --lircdev /var/run/lirc/lircd'
        )
        self.shutdown_inhibitor = self.main.settings.get_setting(
            'XBMC', 'shutdown_inhibitor', False)
        ae_sink = self.main.settings.get_setting('XBMC', 'AE_SINK', "ALSA")
        os.environ['AE_SINK'] = ae_sink
        self.cmd = shlex.split(cmd)
        self.proc = None
        self.block = False
        logging.debug('xbmc command: %s', self.cmd)

    def attach(self, options=None):
        logging.info('starting xbmc')
        self.main.expect_stop = False
        if self.status() == 1:
            return
        if self.shutdown_inhibitor:
            try:
                # Shutdown inhibitor
                self.inhibitor = self.main.inhibit(
                    what="shutdown:sleep:idle",
                    who="frontend",
                    why="xbmc running",
                    mode="block"
                )
            except:
                logging.warning("could not set shutdown-inhobitor")
        try:
            self.proc = subprocess.Popen(self.cmd, env=os.environ)
            if self.proc:
                self.block = True
            if self.proc.poll() is not None:
                logging.warning("failed to start xbmc")
                self.main.switchFrontend()
            # Add callback on exit
            GObject.child_watch_add(self.proc.pid, self.on_exit, self.proc)
            logging.debug('started xbmc')
        except:
            logging.exception('could not start xbmc')
            return False
        return True

    def kill_xbmc(self):
        logging.debug("trying to kill xbmc")
        try:
            self.proc.kill()
            return False
        except:
            logging.exception("could not kill xbmc")

    def on_exit(self, pid, condition, data):
        logging.debug("called function with pid=%s, condition=%s, data=%s",
                      pid, condition, data)
        snd_free = False
        while not snd_free:
            logging.debug("check if xbmc has freed sound device")
            fuser_pid = subprocess.Popen(['fuser', '-v',
                                          '/dev/snd/*p'],
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE, shell=True)
            fuser_pid.wait()
            stdout, stderr = fuser_pid.communicate()
            if "xbmc" in str(stderr):
                snd_free = False
                time.sleep(0.25)
            else:
                snd_free = True
                logging.debug('xbmc has freed sound device')
        self.block = False
        if not self.main.external:
            if condition == 0:
                logging.info("normal xbmc exit")
                if self.main.current == 'xbmc':
                    logging.debug("normal XBMC exit")
                    if not self.main.external and not self.main.expect_stop:
                        self.main.switchFrontend()
                        self.main.completeFrontendSwitch()
                else:
                    logging.debug("call completeFrontendSwitch")
                    self.main.completeFrontendSwitch()
            elif condition < 16384:
                logging.warn("abnormal exit: %s", condition)
                if (self.main.current == "xbmc" and
                        self.main.settings.frontend == "xbmc"):
                    logging.debug("resume xbmc after crash")
                    self.main.frontends[self.main.current].resume()
                elif self.main.current == "xbmc":
                    logging.debug("switch frontend after crash")
                    self.main.switchFrontend()
                else:
                    logging.debug("complete switch to other frontend")
                    self.main.completeFrontendSwitch()
            elif condition == 16384:
                logging.info("XBMC want's a shutdown")
                self.main.switchFrontend()
                #TODO: Remote handling
                self.main.wants_shutdown = True
                self.main.dbus2vdr.Remote.HitKey("Power")
            elif condition == 16896:
                logging.info("XBMC wants a reboot")
                #logging.info(self.main.powermanager.restart())
                # TODO: Reboot implementation via logind?
            else:
                logging.warn("abnormal exit: %s", condition)
                if (self.main.current == "xbmc" and
                        self.main.settings.frontend == "xbmc"):
                    logging.debug("resume xbmc after crash")
                    self.main.frontends[self.main.current].resume()
                elif self.main.current == "xbmc":
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
        logging.info('stopping xbmc')
        try:
            self.proc.terminate()
            logging.debug('sending terminate signal')
            self.proc.wait()
        except:
            logging.info('xbmc already terminated')
        self.killtimer = GObject.timeout_add(2000, self.kill_xbmc)

    def status(self):
        try:
            logging.debug("xbmc status is %s, self.block is %s" %
                          (self.proc.poll(), self.block))
        except:
            logging.debug("xbmc not running, self.block is %s", self.block)
        if self.proc is None:
            return 0
        elif not self.block:
            return 0
        elif self.block:
            logging.debug("self.block is True: xbmc is running")
            return 1
        else:
            logging.debug("self.block is False: xbmc is not running")
            return 0

    def resume(self):
        if self.proc and self.proc.poll() is None:
            logging.debug("xbmc already running")
        else:
            self.attach()
