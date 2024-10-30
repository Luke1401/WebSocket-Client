"""A simple library for some console magic."""
import sys


def print_above_prompt(*args, **kwargs):
    """The same as print(), but _should_ print above the cursor's current line.

    Useful if you want to keep a user prompt at the bottom and insert messages
    above.
    
    Courtesy of Carson Thompson
    https://stackoverflow.com/questions/14300245/python-console-application-output-above-input-line
    """
    kwargs['end'] = ""
    print("\u001B[s", end="")     # Save current cursor position
    print("\u001B[S", end="")     # Scroll up/pan window down 1 line
    print("\u001B[A", end="")     # Move cursor up one line
    print("\u001B[L", end="")     # Insert new line
    print("\u001B[999D", end="")  # Move cursor to beginning of line
    print(*args, **kwargs)     # print output status msg
    print("\u001B[u", end="")     # Jump back to saved cursor position
    sys.stdout.flush()
    
def remove_above_prompt():
    """Removes the console line above the prompt. (An anti-print() if you will.)"""
    print("\u001B[s", end="")     # Save current cursor position
    print("\u001B[A", end="")     # Move cursor up one line
    print("\u001B[999D", end="")  # Move cursor to beginning of line
    print("\u001B[J", end="")     # Clear to EoL
    print("\u001B[T", end="")     # Scroll down/pan window up 1 line
    print("\u001B[u", end="")     # Jump back to saved cursor position
    sys.stdout.flush()

def clear_line():
    print("\u001B[999D", end="")  # Move cursor to beginning of line
    print("\u001B[J", end="")     # Clear to EoL
