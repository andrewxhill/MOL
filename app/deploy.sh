#!/bin/sh
cd js 
./create-mol-js.sh
cd ..
appcfg.py update -V $1 .


