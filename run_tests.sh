#@IgnoreInspection BashAddShebang
export PYTHONWARNINGS="ignore"

python -m pytest 1>/dev/null 2>/dev/null || (pip install pytest && python -m pytest)

export PYTHONWARNINGS="default"
