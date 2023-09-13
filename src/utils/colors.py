# This module implements color-related helper functions for command-line tools.
#
#   Connor Shugg

# Imports
import os
import sys
import stat

# Global color controller
use_color = True



# ============================== Color Toggling ============================== #
def color_enable():
    """
    Enables color printing.
    """
    global use_color
    use_color = True

def color_disable():
    """
    Disables color printing.
    """
    global use_color
    use_color = False

def color_init():
    """
    Initializes the color module. Adjusts the global `use_color` variable
    depending on where stdout is going.
    """
    global use_color
    use_color = True

    # stat stdout and disable color if writing to a file
    outstat = os.fstat(sys.stdout.fileno())
    if stat.S_ISFIFO(outstat.st_mode):  # PIPE
        use_color = False
    elif stat.S_ISREG(outstat.st_mode): # FILE
        use_color = False


# ============================= Color Functions ============================== #
def color_hash(s):
    """
    Takes in a string and uses it to generate a pseudo-random, deterministic,
    color escape sequence.
    """
    s = str(s)
    if len(s) == 0 or s.lower() == "none":
        return "\033[38;2;128;128;128m"

    # simple helper function for quickly hashing a string
    def color_hash_helper(txt):
        result = 0
        for c in txt:
            result = ((result * 1237) ^ (ord(c) * 593)) & 0xffffffff
        return result

    # split the string into (roughly) thirds, then use each to generate a random
    # 0-255 value (for red, green, and blue)
    third = int(len(s) / 3)
    red = (color_hash_helper(s[0:third]) % 128) + 128
    green = (color_hash_helper(s[third:(third * 2)]) % 128) + 128
    blue = (color_hash_helper(s[(third * 2):len(s)]) % 128) + 128
    return "\033[38;2;%d;%d;%dm" % (red, green, blue)

def color_rgb(r: int, g: int, b: int):
    """
    Takes in R, G, and B values (0-255) and uses it to generate and return a
    color escape sequence.
    """
    r = max(0, min(255, r))
    g = max(0, min(255, g))
    b = max(0, min(255, b))
    return "\033[38;2;%d;%d;%dm" % (r, g, b)

def color(s: str):
    """
    Takes in a color name or random string and either returns the color with the
    matching name or generates a random color, depending on the global setting.
    """
    # if colors are disabled, return a blank string
    if not use_color:
        return ""

    # search for a match and return, or just generate a random color unique to
    # the given string
    if s in colors:
        return colors[s]
    return color_hash(s)

def color_file_size(size: int):
    """
    Takes in a size (an integer) an returns an appropriate color.
    This is intended to be used for file sizes.
    """
    sizes = [
        {"size": 1000000000, "color": "red"},
        {"size": 1000000, "color": "yellow"},
        {"size": 1000, "color": "green"},
    ]
    for sz in sizes:
        if size >= sz["size"]:
            return color(sz["color"])
    return color("none")


# ========================= Global Color Definitions ========================= #
# Array of known color values
colors = {
    "none":                 "\033[0m",
    "red":                  color_rgb(230, 30,  30),
    "green":                color_rgb(30,  230, 30),
    "lime":                 color_rgb(125, 230, 30),
    "yellow":               color_rgb(225, 255, 30),
    "blue":                 color_rgb(115, 115, 255),
    "purple":               color_rgb(175, 115, 200),
    "gray":                 color_rgb(150, 150, 150),
    "dkgray":               color_rgb(110, 110, 110),

    # number colors
    "0":                    color_rgb(125, 125, 125),

    # program-specific colors
    "config_field_name":    color_rgb(150, 255, 255),
    "config_field_req":     color_rgb(255, 255, 100),
    "env_name":             color_rgb(150, 255, 255),
    "dbg":                  color_rgb(125, 100, 150),
    "project":              color_rgb(115, 115, 225),
    "repo":                 color_rgb(255, 140, 50),
    "branch":               color_rgb(225, 210, 200),
    "pullreq_id":           color_rgb(175, 225, 225),
    "pullreq_owner":        "\033[0m",
    "pullreq_branch_src":   color_rgb(150, 135, 125),
    "pullreq_branch_dst":   color_rgb(135, 150, 125),
    "team":                 color_rgb(225, 225, 100),
    "team_id":              color_rgb(125, 150, 50),
    "url":                  color_rgb(200, 200, 255)
}


