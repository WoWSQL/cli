# PyPI Deployment Guide for WoWSQL CLI

This guide explains how to deploy `wowsql-cli` to PyPI.

## Prerequisites

1. **PyPI Account**: You already have a PyPI account
2. **API Token**: Create an API token at https://pypi.org/manage/account/token/
   - Go to PyPI → Account Settings → API tokens
   - Create a new token with scope: "Entire account" or "wowsql-cli" project
3. **Build Tools**: Install build tools:
   ```bash
   pip install --upgrade build twine
   ```

## Version Management

The package uses semantic versioning (MAJOR.MINOR.PATCH):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

Current version is defined in:
- `setup.py`: `version="0.1.0"`
- `wowsql_cli/__init__.py`: `__version__ = "0.1.0"`

**Important**: Always update both files when releasing a new version!

## Deployment Steps

### 1. Update Version

Before each release, update the version in both files:

```bash
# Edit setup.py and wowsql_cli/__init__.py
# Change version from "0.1.0" to "0.1.1" (or appropriate version)
```

### 2. Clean Previous Builds

```bash
cd cli
rm -rf dist/ build/ *.egg-info/
```

### 3. Build the Package

```bash
# Build source distribution and wheel
python -m build
```

This creates:
- `dist/wowsql-cli-0.1.0.tar.gz` (source distribution)
- `dist/wowsql-cli-0.1.0-py3-none-any.whl` (wheel)

### 4. Check the Package

```bash
# Check for common issues
python -m twine check dist/*
```

### 5. Test Installation Locally (Optional)

```bash
# Install from local build to test
pip install dist/wowsql-cli-0.1.0-py3-none-any.whl

# Test the CLI
wowsql --version

# Uninstall when done testing
pip uninstall wowsql-cli
```

### 6. Upload to TestPyPI (Recommended First)

TestPyPI is a separate test environment. Always test here first:

```bash
# Upload to TestPyPI
python -m twine upload --repository testpypi dist/*

# You'll be prompted for:
# - Username: __token__
# - Password: your-testpypi-api-token (starts with pypi-)
```

Then test installation from TestPyPI:
```bash
pip install --index-url https://test.pypi.org/simple/ wowsql-cli
```

### 7. Upload to Production PyPI

Once tested, upload to production PyPI:

```bash
# Upload to PyPI
python -m twine upload dist/*

# You'll be prompted for:
# - Username: __token__
# - Password: your-pypi-api-token (starts with pypi-)
```

### 8. Verify Installation

After upload, verify the package is available:

```bash
# Wait a few minutes for PyPI to index, then:
pip install wowsql-cli
wowsql --version
```

## Using API Tokens

Instead of entering credentials each time, you can:

### Option 1: Environment Variables

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-your-api-token-here

python -m twine upload dist/*
```

### Option 2: .pypirc File (Not Recommended for API Tokens)

Create `~/.pypirc`:
```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-your-api-token-here

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-your-testpypi-token-here
```

**Note**: API tokens are preferred over passwords. Use `__token__` as username.

## Automated Deployment Script

Create a script `deploy.sh` (or `deploy.ps1` for Windows):

```bash
#!/bin/bash
# deploy.sh

set -e  # Exit on error

VERSION=$(python -c "import sys; sys.path.insert(0, 'wowsql_cli'); from wowsql_cli import __version__; print(__version__)")

echo "Building wowsql-cli version $VERSION..."

# Clean
rm -rf dist/ build/ *.egg-info/

# Build
python -m build

# Check
python -m twine check dist/*

echo "Build complete! Files:"
ls -lh dist/

echo ""
echo "To upload to TestPyPI:"
echo "  python -m twine upload --repository testpypi dist/*"
echo ""
echo "To upload to PyPI:"
echo "  python -m twine upload dist/*"
```

## Version Bumping Workflow

For each new release:

1. **Update version** in `setup.py` and `wowsql_cli/__init__.py`
2. **Update CHANGELOG.md** (if you have one) with new features/fixes
3. **Commit changes**: `git commit -am "Bump version to X.Y.Z"`
4. **Tag the release**: `git tag vX.Y.Z`
5. **Build and upload** to PyPI
6. **Push tags**: `git push origin vX.Y.Z`

## Troubleshooting

### "Package already exists"
- The version already exists on PyPI. Increment the version number.

### "Invalid credentials"
- Check your API token is correct
- Ensure you're using `__token__` as username (not your PyPI username)
- For TestPyPI, use a TestPyPI-specific token

### "File already exists"
- Delete old files in `dist/` directory
- Or use `--skip-existing` flag: `twine upload --skip-existing dist/*`

### "Module not found" during build
- Ensure you're in the `cli/` directory
- Check that `wowsql_cli/__init__.py` exists and has `__version__`

## Best Practices

1. **Always test on TestPyPI first**
2. **Use semantic versioning** consistently
3. **Keep versions in sync** between `setup.py` and `__init__.py`
4. **Tag releases in Git** for version tracking
5. **Update README.md** if installation instructions change
6. **Document breaking changes** in release notes

## Next Steps After Deployment

1. Update documentation to reflect new version
2. Announce the release (if applicable)
3. Monitor for any installation issues
4. Plan next version based on feedback

## Quick Reference

```bash
# Full deployment workflow
cd cli
# 1. Update version in setup.py and wowsql_cli/__init__.py
# 2. Clean and build
rm -rf dist/ build/ *.egg-info/
python -m build
# 3. Check
python -m twine check dist/*
# 4. Upload to TestPyPI (test first)
python -m twine upload --repository testpypi dist/*
# 5. Upload to PyPI
python -m twine upload dist/*
```

