  /usr/bin/vdr-dbus-send /Remote remote.Enable ||: &> /dev/null
  /usr/bin/vdr-dbus-send /Plugins/softhddevice plugin.SVDRPCommand string:'ATTA' string:"-d $DISPLAY" ||: &> /dev/null
