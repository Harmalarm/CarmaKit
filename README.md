# CarmaKit

Carmageddon model toolkit for Blender - A Blender addon for importing and exporting Carmageddon 1 & 2 model files.

## Features

- **Import** ACT (actor), DAT (model), and MAT (material) files
- **Export** to Carmageddon-compatible formats
- Supports the big-endian binary format used by Carmageddon games
- Full hierarchy and transformation matrix support

## Supported File Formats

| Format | Extension | Description |
|--------|-----------|-------------|
| ACT | `.act` | Actor files - contain hierarchy, transforms, and model references |
| DAT | `.dat` | Model files - contain vertices, faces, UV coordinates |
| MAT | `.mat` | Material files - contain material properties and texture references |

## Installation

### As a Blender Addon

1. Download the `carmakit_addon` folder
2. In Blender: Edit → Preferences → Add-ons → Install
3. Navigate to the addon folder and install
4. Enable "CarmaKit" in the addon list

### Development Setup

```bash
# Clone the repository
git clone https://github.com/Harmalarm/CarmaKit.git
cd CarmaKit

# Create a Python 3.11 virtual environment (required for bpy module)
python -m venv .venv311

# Activate the environment
# Windows:
.venv311\Scripts\activate
# Linux/macOS:
source .venv311/bin/activate

# Install dependencies (includes headless Blender bpy module)
pip install -r requirements.txt
```

## Testing

### Test Environment

This project uses **headless Blender** for testing via the `bpy` module. This allows running Blender Python scripts without launching the Blender GUI, enabling automated testing in CI/CD pipelines.

**Key points:**
- Tests run using Python 3.11 with the `bpy` module from Blender's PyPI repository
- The virtual environment `.venv311` is configured with the bpy package
- No Blender GUI installation is required for running tests

### Running Tests

```bash
# Activate the virtual environment
# Windows:
.venv311\Scripts\activate

# Run all tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ --cov=src/carmakit_addon --cov-report=html

# Run a specific test file
pytest tests/test_parsers.py -v

# Run a specific test
pytest tests/test_parsers.py::TestActParser::test_parse_eagle3_act -v
```

### Test Structure

```
tests/
├── conftest.py          # Pytest fixtures and configuration
├── test_binary_io.py    # Binary read/write function tests
├── test_constants.py    # Constants and magic number tests
├── test_data_structures.py  # Data class tests
├── test_parsers.py      # File parsing tests
└── test_writers.py      # File writing tests
```

### Test Data

Sample Carmageddon files are located in `src/static/eagle3/`:
- `EAGLE3.ACT` - Actor file with full hierarchy
- `EAGLENEW.DAT` - Model file with geometry
- `Eagle3.mat` - Material definitions
- `simple_eagle3.act/mat` - Simplified test files

## Project Structure

```
CarmaKit/
├── src/
│   ├── carmakit_addon/      # Main addon package
│   │   ├── __init__.py      # Addon registration
│   │   ├── binary_io.py     # Binary read/write utilities
│   │   ├── constants.py     # File format constants
│   │   ├── data_structures.py  # Data classes
│   │   ├── exporter.py      # Blender export operators
│   │   ├── importer.py      # Blender import operators
│   │   ├── operators.py     # Blender operators
│   │   ├── panels.py        # Blender UI panels
│   │   ├── parsers.py       # File format parsers
│   │   ├── preferences.py   # Addon preferences
│   │   └── writers.py       # File format writers
│   └── static/              # Test data and format docs
│       ├── eagle3/          # Sample Carmageddon files
│       └── format/          # Format documentation
├── tests/                   # Test suite
├── pyproject.toml          # Project configuration
├── requirements.txt        # Dependencies
└── README.md
```

## Development Notes

### For AI Agent Sessions

When working on this project, keep these points in mind:

1. **Python Environment**: Always use the `.venv311` virtual environment with Python 3.11
   ```bash
   # Windows
   E:/Repos/CarmaKit/.venv311/Scripts/python.exe <script>
   ```

2. **Running Tests**: Use pytest through the venv:
   ```bash
   .venv311/Scripts/python.exe -m pytest tests/ -v
   ```

3. **File Format Details**: 
   - All Carmageddon files use **big-endian** byte order
   - Record structure: 4-byte type + 4-byte length + data
   - See `src/static/format/C2FORMAT.TXT` for format documentation

4. **Key Constants** (in `constants.py`):
   - `FILE_TYPE_ACT = 0x01`
   - `FILE_TYPE_DAT = 0xFACE`
   - `FILE_TYPE_MAT = 0x05`

5. **Common Issues**:
   - ACT `MATERIAL_NAMES` records don't have a count prefix (unlike DAT format)
   - Null-terminated strings in records - don't read past record length
   - Always check for null markers (8 zero bytes) at end of files/sections

6. **Quick Test Script** (`test_act_parser.py`):
   ```python
   import sys
   sys.path.insert(0, 'src')
   from carmakit_addon.parsers import parse_act_file
   
   act = parse_act_file('src/static/eagle3/EAGLE3.ACT')
   print('Root:', act.root.name if act.root else None)
   ```

### Code Style

- Follow PEP 8 guidelines
- Use type hints for all function parameters and returns
- Write docstrings in reStructuredText format (PEP 287)
- Maximum line length: 79 characters

## Format Documentation

Detailed file format documentation is available in `src/static/format/`:
- `C2FORMAT.TXT` - Comprehensive Carmageddon 2 file format specification
- `C2MATRIX.TXT` - Transformation matrix documentation

## License

MIT License - see [LICENSE](LICENSE) for details.
