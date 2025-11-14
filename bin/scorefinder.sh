#!/bin/bash
if [ -z $SFHOME ];
then
    echo "Please run install.sh first."
    exit 1
fi
python $SFHOME/main.py "$@"
pyexit=$?
exit $pyexit