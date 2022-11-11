import sys


def get_call_arg_args(call_arg):
    if sys.version_info[1] >= 8:
        args = call_arg.args
    else:
        args = call_arg[0]
    return args


def get_call_arg_data(call_arg):
    return get_call_arg_args(call_arg)[2]
