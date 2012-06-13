  logger -t frontend-softhddevice "activate remote"
  vdr-dbus-send /Remote remote.Enable ||: &> /dev/null
  logger -t frontend-softhddevice "activate softhddevice on $DISPLAY"
  vdr-dbus-send /Plugins/softhddevice plugin.SVDRPCommand string:'ATTA' string:"-d $DISPLAY" ||: &> /dev/null
