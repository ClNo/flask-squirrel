#!/bin/bash

DNAME="squirrel/eslint"
DTAG="1.0.0"
DFILE="tools/eslint/Dockerfile.eslint"
# ESLINTRC="tools/eslint/airbnb-rules.eslintrc"
ESLINTRC="tools/eslint/eslint-smiliar-airbnb.json"

IMAGE_ID="$(docker image ls -q ${DNAME})"

# go up if startet from the tools dir
if [ $(basename $PWD) == "eslint" ]; then cd ..; fi
if [ $(basename $PWD) == "tools" ]; then cd ..; fi

if [[ -z "${IMAGE_ID}" ]]; then
  echo "* create a new eslint docker image"
  docker build -t "${DNAME}:${DTAG}" -f "${DFILE}" tools/  # tools is the context directory; unused
  echo
  echo
else
  echo "* use existing eslint docker image ${IMAGE_ID}"
fi

JS_SOURCES="$(find examples -iname '*.js' -not -iname 'jquery*')"
echo
echo 'checking following sources with prefix "/code/":'
for s in ${JS_SOURCES}; do
  if [[ $(basename "$s") == "dropzone.js" ]]; then
    # skip
    :
  elif [[ $s == *"DataTable"* ]]; then
    # skip
    :
  elif [[ $s == *"Datatable"* ]]; then
    # skip
    :
  else
    JS_SOURCES_DOCKER="${JS_SOURCES_DOCKER} /code/${s} "
    echo "$s"
  fi
done

# append --fix for letting eslint fix the code as far as possible
docker run -it --rm -v ${PWD}:/code "${DNAME}:${DTAG}" -c "/code/${ESLINTRC}" --fix $JS_SOURCES_DOCKER

# for loggin in as root:
# docker run -it --rm -v ${PWD}:/code --entrypoint /bin/sh "${DNAME}:${DTAG}"
