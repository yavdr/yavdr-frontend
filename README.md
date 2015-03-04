arch-frontend
=============

Manage vdr-frontends and KODI from within a user session

To stop the script (there are still some signal handling issues) use

```
frontend-dbus-send /frontend quit
```

requires dbus2vdr-plugin and https://github.com/seahawk1986/pydbus2vdr
