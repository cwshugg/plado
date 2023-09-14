#!/bin/bash
# Simple wrapper script that invokes plado.

plado_dir="$(dirname $(dirname $0))"
plado_src="$(find ${plado_dir} -name "main.py")"

# make sure the file exists
if [ ! -f "${plado_src}" ]; then
    echo "Error: failed to find plado main source file."
    exit 1
fi

# run it, along with all other command-line arguments
python3 ${plado_src} "$@"

