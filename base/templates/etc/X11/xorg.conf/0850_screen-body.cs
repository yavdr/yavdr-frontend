    Identifier     "Screen<?cs var:count ?>"
    Device         "Device<?cs var:count ?>"
    Monitor        "<?cs alt:display.identifier?>Monitor<?cs var:count ?><?cs /alt ?>"

<?cs if:(display.identifier != "") ?><?cs if:(count == "0") ?>
    Option         "CustomEDID" "<?cs set:count2 = -1 ?><?cs each:display2 = system.display ?><?cs if:display2.active == "1" ?><?cs set:count2 = count2 + #1 ?><?cs if:count2 > #0 ?>;<?cs /if ?><?cs var:display2.identifier?>:/etc/X11/<?cs var:display2.identifier?>.edid<?cs /if ?><?cs /each ?>"
    Option         "ConnectedMonitor" "<?cs set:count2 = -1 ?><?cs each:display2 = system.display ?><?cs if:display2.active == "1" ?><?cs set:count2 = count2 + #1 ?><?cs if:count2 > #0 ?>,<?cs /if ?><?cs var:display2.identifier?><?cs /if ?><?cs /each ?>"<?cs /if ?>
    Option         "UseDisplayDevice" "<?cs var:display.identifier ?>"<?cs /if ?>

    SubSection     "Display"
      Modes        "<?cs var:display.width ?>x<?cs var:display.height ?>_<?cs var:display.rate ?>"
    EndSubSection