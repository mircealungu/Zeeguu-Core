#@IgnoreInspection BashAddShebang
export PYTHONWARNINGS="ignore"

python -m unittest discover -v
return_value=$?
export PYTHONWARNINGS="default"
exit $return_value