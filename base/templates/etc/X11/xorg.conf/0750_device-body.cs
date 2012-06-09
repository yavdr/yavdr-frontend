    Identifier     "Device<?cs var:count ?>"
    Screen         <?cs var:count ?><?cs if:(display.driver == "nvidia") ?>
    Driver         "<?cs var:display.driver ?>"<?cs /if ?>
    Option         "DPI" "100x100"
    Option         "NoLogo" "True"
    Option         "UseEvents" "True"
    Option         "TripleBuffer" "False"
    Option         "AddARGBGLXVisuals" "True"
    Option         "TwinView" "0"
    Option         "DynamicTwinView" "0"
    Option         "OnDemandVBlankinterrupts" "on"
    Option         "FlatPanelProperties" "Scaling = Native"
