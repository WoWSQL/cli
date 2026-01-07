# Quick Deployment Guide

## First Time Setup

1. **Install build tools:**
   ```bash
   pip install --upgrade build twine
   ```

2. **Get PyPI API Token:**
   - Go to https://pypi.org/manage/account/token/
   - Create a new token (scope: "wowsql-cli" project or "Entire account")
   - Copy the token (starts with `pypi-`)

## Deploy to PyPI

### Step 1: Update Version (if needed)

Edit `wowsql_cli/__init__.py`:
```python
__version__ = "0.1.1"  # Increment as needed
```

The version in `setup.py` will be read automatically from `__init__.py`.

### Step 2: Build and Upload

**Windows (PowerShell):**
```powershell
cd cli
.\deploy.ps1 testpypi  # Test first
.\deploy.ps1 pypi     # Then production
```

**Linux/Mac:**
```bash
cd cli
./deploy.sh testpypi  # Test first
./deploy.sh pypi      # Then production
```

**Manual (if scripts don't work):**
```bash
cd cli

# Clean
rm -rf dist/ build/ *.egg-info/

# Build
python -m build

# Check
python -m twine check dist/*

# Upload to TestPyPI (test first)
python -m twine upload --repository testpypi dist/*
# Username: __token__
# Password: your-testpypi-token

# Upload to PyPI (production)
python -m twine upload dist/*
# Username: __token__
# Password: your-pypi-token
```

### Step 3: Verify

```bash
pip install wowsql-cli
wowsql --version
```

## Version Management

- **Current version**: Defined in `wowsql_cli/__init__.py`
- **Version format**: `MAJOR.MINOR.PATCH` (e.g., `0.1.0`, `0.1.1`, `1.0.0`)
- **When to increment:**
  - **PATCH** (0.1.0 → 0.1.1): Bug fixes
  - **MINOR** (0.1.0 → 0.2.0): New features
  - **MAJOR** (0.1.0 → 1.0.0): Breaking changes

## Troubleshooting

- **"Package already exists"**: Version already on PyPI → Increment version
- **"Invalid credentials"**: Use `__token__` as username, not your PyPI username
- **"File already exists"**: Delete `dist/` folder and rebuild

## Next Version Workflow

1. Update `wowsql_cli/__init__.py` version
2. Commit: `git commit -am "Bump version to X.Y.Z"`
3. Tag: `git tag vX.Y.Z`
4. Deploy: `./deploy.sh pypi` (or `.\deploy.ps1 pypi`)
5. Push: `git push origin vX.Y.Z`

