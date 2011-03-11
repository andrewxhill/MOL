#!/bin/sh
cd mol
rm -rf *.*~
rm -rf ../mol.js
cat mol.util.js mol.control.js mol.event.js mol.api.js mol.view.* mol.activity.* mol.init.js > ../mol.js

