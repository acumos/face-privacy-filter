#!/bin/bash
#------------------------------------------------------------------------
#  run_local.sh - locally starts a face privacy filter instance
#------------------------------------------------------------------------

# infer the project location
MODEL_DIR=$(dirname $( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd ) )
echo "Local run directory '$MODEL_DIR'..."

# inject into python path and run with existing args (for unix-like environments)
PYTHONPATH="$MODEL_DIR:$PYTHONPATH" python $MODEL_DIR/bin/run_face-privacy-filter_reference.py $*
