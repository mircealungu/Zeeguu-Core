#@IgnoreInspection BashAddShebang
export PYTHONWARNINGS="ignore"

python3 -m pytest --version 1>/dev/null 2>/dev/null || (echo "installing pytest..." && pip3 install pytest) && python -m pytest
ret_code=$?

export PYTHONWARNINGS="default"

exit $ret_code
