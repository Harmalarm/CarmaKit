"""
Test configuration and fixtures for CarmaKit.

This module provides pytest fixtures and configuration for testing
the CarmaKit addon's file parsers and data structures.


"""

import os
import sys
from pathlib import Path

import pytest

# Add src directory to path so carmakit_addon package can be imported.
SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

# Path to static test files.
STATIC_DIR = SRC_DIR / "static"
EAGLE3_DIR = STATIC_DIR / "eagle3"


@pytest.fixture
def static_dir() -> Path:
    """
    Return the path to the static test files directory.

    """
    return STATIC_DIR


@pytest.fixture
def eagle3_dir() -> Path:
    """
    Return the path to the Eagle3 test model directory.

    """
    return EAGLE3_DIR


@pytest.fixture
def eagle3_act_path(eagle3_dir: Path) -> Path:
    """
    Return the path to the Eagle3 ACT file.

    """
    return eagle3_dir / "EAGLE3.ACT"


@pytest.fixture
def eagle3_dat_path(eagle3_dir: Path) -> Path:
    """
    Return the path to the Eagle3 DAT file.

    """
    return eagle3_dir / "Eagle3.dat"


@pytest.fixture
def eagle3_mat_path(eagle3_dir: Path) -> Path:
    """
    Return the path to the Eagle3 MAT file.

    """
    return eagle3_dir / "Eagle3.mat"


@pytest.fixture
def simple_eagle3_act_path(eagle3_dir: Path) -> Path:
    """
    Return the path to the simple Eagle3 ACT file.

    """
    return eagle3_dir / "simple_eagle3.act"


@pytest.fixture
def simple_eagle3_dat_path(eagle3_dir: Path) -> Path:
    """
    Return the path to the simple Eagle3 DAT file.

    """
    return eagle3_dir / "simple_eagle3.dat"


@pytest.fixture
def simple_eagle3_mat_path(eagle3_dir: Path) -> Path:
    """
    Return the path to the simple Eagle3 MAT file.

    """
    return eagle3_dir / "simple_eagle3.mat"
