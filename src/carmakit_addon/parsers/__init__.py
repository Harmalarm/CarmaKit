"""
File format parsers for Carmageddon files.

This package contains parsers for reading DAT, ACT, and MAT files
in their native big-endian binary format.
"""

# Re-export ParseError from parser_utils.
from .utils import ParseError, find_related_files

# Re-export individual parsers.
from .act_parser import parse_act_file
from .dat_parser import parse_dat_file
from .mat_parser import parse_mat_file

# Export all public symbols.
__all__ = [
    'ParseError',
    'parse_act_file',
    'parse_dat_file',
    'parse_mat_file',
    'find_related_files',
]
