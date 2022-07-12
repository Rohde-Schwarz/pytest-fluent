import json
import os


def log_args_as_json(file_name: str, call_args: dict):
    with open(os.path.join(os.path.dirname(__file__), file_name), "w") as fid:
        to_log = [a.args[2] for a in call_args]
        json.dump(to_log, fid)
