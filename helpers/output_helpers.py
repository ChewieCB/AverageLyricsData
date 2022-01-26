from sys import stderr
from dataclasses import dataclass

HEADER = '\033[95m'
OKBLUE = '\033[94m'
OKCYAN = '\033[96m'
OKGREEN = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'


def wrap_text(input: str, colour) -> str:
    """Given a string, wrap the input with a header and enc character to produce a formatted header string."""
    return colour + input + ENDC


def header(input: str) -> str:
    return(wrap_text(input, HEADER))


def blue(input: str) -> str:
    return(wrap_text(input, OKBLUE))


def cyan(input: str) -> str:
    return(wrap_text(input, OKCYAN))


def green(input: str) -> str:
    return(wrap_text(input, OKGREEN))


def warning(input: str) -> str:
    return(wrap_text(input, WARNING))


def fail(input: str) -> str:
    return(wrap_text(input, FAIL))


def bold(input: str) -> str:
    return(wrap_text(input, BOLD))


def separator(size: int = 128, single: bool = False) -> str:
    if single:
        return("-" * size)
    else:
        return("=" * size)
