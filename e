#!/bin/bash

FOLDER_TO_SEARCH=zeeguu

echo "Files Found: "
find $FOLDER_TO_SEARCH -name "*$1*.$2" -print

# for distinguishing " ", "\t" from "\n"
IFS=

echo "press ENTER to open the first file in the previous list"
read -n 1 key 
if [ "$key" = "" ]; then
   find $FOLDER_TO_SEARCH -name "*$1*.$2" -exec vi {} +
fi



