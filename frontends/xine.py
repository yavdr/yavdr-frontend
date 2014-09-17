#!/usr/bin/python3
import dbus
from dbus.mainloop.glib import DBusGMainLoop
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
from gi.repository import GObject
import logging
from frontends.base import *
import os
import subprocess

class Xine():
    def __init__(self, main, name):
        self.main = main
        self.name = name
        if self.main.settings.get_settingb('Xine', 'autocrop', False):
            autocrop = "--post autocrop:enable_autodetect=1,enable_subs_detect=1,soft_start=1,stabilize=1"
        else:
            autocrop = ""
        if self.main.settings.get_settingb('Xine', 'anamorphic', False):
            aspectratio = "--aspect-ratio=%s"%(self.main.settings.get_setting(
                                                'xine', 'aspect_ratio', '16:9')
            )
        else:
            aspectratio = ""
        os.environ['__GL_SYNC_TI_VBLANK']="1"
        # TODO Display config:
        os.environ['__GL_SYNC_DISPLAY_DEVICE'] = os.environ['DISPLAY']

        self.cmd = self.main.settings.get_setting("Xine",
                                                  "xine_cmd",
            '''/usr/bin/xine --post tvtime:method=use_vo_driver \
            --config /etc/xine/config \
            --keymap=file:/etc/xine/keymap \
            --post vdr --post vdr_video --post vdr_audio --verbose=2 \
            --no-gui --no-logo --no-splash --deinterlace -pq \
            -A pulseaudio \
            {autocrop} {aspectratio} \
            vdr:/tmp/vdr-xine/stream#demux:mpeg_pes'''.format(autocrop=autocrop, aspectratio=aspectratio)
            )
        self.proc = None
        self.environ = os.environ

    def attach(self, options=None):
        logging.debug('starting xine')
        logging.debug('self.cmd')
        self.proc = subprocess.Popen("exec " + self.cmd,
                                     shell=True, env=os.environ)
        GObject.child_watch_add(self.proc.pid,self.on_exit,self.proc) # Add callback on exit
        logging.debug('started xine')

    def detach(self, active=0):
        logging.debug('stopping xine')
        try:
            self.proc.kill()
            return True
        except Exception as e:
            logging.exception(e)
            logging.debug('xine already terminated')
        self.proc = None

    def status(self):
        if self.proc: return 1
        else: return 0

    def resume(self):
        if self.proc: pass
        else: self.attach()

    def on_exit(self,pid, condition, data):
        logging.debug("called function with pid=%s, condition=%s, data=%s",pid, condition,data)
        self.proc = None
        logging.debug("xine exit code was:", condition)
        if condition == 0:
            self.proc = None
            return
        else:
            self.main.attach()
