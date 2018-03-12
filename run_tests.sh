#@IgnoreInspection BashAddShebang
export PYTHONWARNINGS="ignore"

python -m pytest .
return_value=$?
export PYTHONWARNINGS="default"
exit $return_value