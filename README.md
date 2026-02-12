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
python -m venv .venv

# Activate the environment
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies (includes headless Blender bpy module)
pip install -r requirements.txt
```

## Format Documentation

Detailed file format documentation is available in `src/static/format/`:
- `C2FORMAT.TXT` - Comprehensive Carmageddon 2 file format specification
- `C2MATRIX.TXT` - Transformation matrix documentation

## License

MIT License - see [LICENSE](LICENSE) for details.
