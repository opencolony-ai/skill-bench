import sys

if sys.version_info < (3, 9):
    from typing import Dict as dict_t
else:
    dict_t = dict
