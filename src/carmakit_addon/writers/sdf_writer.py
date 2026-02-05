"""
SDF file writer for Carmageddon Plaything compatibility.

This module contains the writer for creating SDF marker files.
"""


def write_sdf_file(filepath: str) -> None:
    """
    Write an empty SDF file for Plaything compatibility.

    SDF files are empty marker files that enable editing in Plaything.

    :param filepath: Path to the output SDF file.
    :type filepath: str
    :return: None.
    :rtype: None
    """
    # Create an empty file.
    with open(filepath, 'wb') as f:
        pass
