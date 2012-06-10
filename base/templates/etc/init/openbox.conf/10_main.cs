<?cs if:(!?vdr.frontend || vdr.frontend != "disabled") ?>
start on ((filesystem
           and runlevel [!06]
           and started dbus
           and (drm-device-added card0 PRIMARY_DEVICE_FOR_DISPLAY=1
                or stopped udev-fallback-graphics))
          or runlevel PREVLEVEL=S)

stop on runlevel [016]
<?cs /if ?>

emits desktop-session-start
emits desktop-shutdown

respawn

script
  if [ -n "$UPSTART_EVENTS" ]; then
    # Check kernel command-line for inhibitors, unless we are being called
    # manually
    for ARG in $(cat /proc/cmdline); do
      if [ "$ARG" = "text" ]; then
        plymouth quit || :
        stop
        exit 0
      fi
    done

    if [ "$RUNLEVEL" = S -o "$RUNLEVEL" = 1 ]; then
      # Single-user mode
      plymouth quit || :
      exit 0
    fi
  fi

  # stop plymount
  plymouth quit || :

  # D-bus
  if which dbus-launch >/dev/null && test -z "$DBUS_SESSION_BUS_ADDRESS"; then
    eval `dbus-launch --sh-syntax --exit-with-session`
  fi

  if [ -e /etc/default/locale ]; then
    . /etc/default/locale
  fi

  exec xinit /usr/bin/openbox --config-file /etc/openbox/rc.xml --startup "/sbin/initctl emit --no-wait desktop-session-start" -- :0 vt7
end script



post-stop script
  if [ "$UPSTART_STOP_EVENTS" = runlevel ]; then
    initctl emit desktop-shutdown
  fi
end script
