#!/bin/sh
rm -rf *.*~
rm -rf ../static/js/mol.js
cat mol.js mol.app.js mol.events.js mol.ajax.js mol.log.js mol.exceptions.js mol.location.js mol.model.js mol.util.js mol.ui.js mol.ui.ColorSetter.js mol.ui.LayerControl.js mol.ui.LayerList.js mol.ui.Map.js mol.ui.Search.js mol.ui.Metadata.js > ../static/js/mol.js

