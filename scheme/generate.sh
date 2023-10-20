#!/bin/sh

filenames=("run")
basedir=$(cd $(dirname $0) && pwd)

for f in "${filenames[@]}"; do
    dot -Tsvg "${basedir}/${f}.dot" -o "${basedir}/${f}.svg"
done