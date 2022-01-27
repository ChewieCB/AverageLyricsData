
HEADER = '\033[95m'
OKBLUE = '\033[94m'
OKCYAN = '\033[96m'
OKGREEN = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'


def wrap_text(input_string: str, colour) -> str:
    """Given a string, wrap the input_string with a header and enc character to produce a formatted header string."""
    return colour + input_string + ENDC


def header(input_string: str) -> str:
    return wrap_text(input_string, HEADER)


def blue(input_string: str) -> str:
    return wrap_text(input_string, OKBLUE)


def cyan(input_string: str) -> str:
    return wrap_text(input_string, OKCYAN)


def green(input_string: str) -> str:
    return wrap_text(input_string, OKGREEN)


def warning(input_string: str) -> str:
    return wrap_text(input_string, WARNING)


def fail(input_string: str) -> str:
    return wrap_text(input_string, FAIL)


def bold(input_string: str) -> str:
    return wrap_text(input_string, BOLD)


def separator(size: int = 128, single: bool = False) -> str:
    if single:
        return "-" * size
    else:
        return "=" * size
