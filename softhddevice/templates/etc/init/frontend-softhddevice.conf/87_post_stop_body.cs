  logger -t frontend-softhddevice "deactivate remote"
  /usr/bin/vdr-dbus-send /Remote remote.Disable ||: &> /dev/null
  logger -t frontend-softhddevice "deactivate softhddevice"
  /usr/bin/vdr-dbus-send /Plugins/softhddevice plugin.SVDRPCommand string:'DETA' ||: &> /dev/null
