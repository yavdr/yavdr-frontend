<?cs set:count = -1?>    Identifier     "Layout0"
<?cs each:display = system.display ?><?cs if:display.active == "1" ?><?cs set:count = count + #1 ?><?cs if:count == #0 ?>
    Screen      <?cs var:count ?>  "Screen <?cs var:count ?>"<?cs else ?>
    Screen      <?cs var:count ?>  "Screen<?cs var:count ?>" RightOf "Screen<?cs var:count -1?>"<?cs /if ?><?cs /if ?><?cs /each ?>

