  /usr/bin/vdr-dbus-send /Remote remote.Disable ||: &> /dev/null
  /usr/bin/vdr-dbus-send /Plugins/softhddevice plugin.SVDRPCommand string:'DETA' ||: &> /dev/null
