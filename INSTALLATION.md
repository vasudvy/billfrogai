# 🚀 Billfrog Installation Guide

This guide covers installation methods for Billfrog, from end users to developers.

## 📦 For End Users

### Method 1: Install from PyPI (Recommended)

Once published, install Billfrog with a single command:

```bash
pip install billfrog
```

### Method 2: Install from Source

```bash
# Clone the repository
git clone https://github.com/billfrog-dev/billfrog.git
cd billfrog

# Install the package
pip install .
```

### Method 3: Install with pipx (Isolated Installation)

```bash
# Install pipx if you don't have it
pip install pipx

# Install billfrog in an isolated environment
pipx install billfrog
```

## 🛠️ For Developers

### Development Setup

1. **Clone the repository:**
```bash
git clone https://github.com/billfrog-dev/billfrog.git
cd billfrog
```

2. **Create a virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install in development mode:**
```bash
pip install -e ".[dev]"
```

This installs Billfrog with all development dependencies including:
- pytest (testing)
- black (code formatting)
- isort (import sorting)
- flake8 (linting)
- mypy (type checking)

### Testing Your Installation

Verify the installation works:

```bash
# Check version
billfrog --version

# View help
billfrog --help

# Run package structure test
python test_package.py
```

## 🔧 System Requirements

- **Python**: 3.8 or higher
- **Operating System**: Linux, macOS, or Windows
- **Memory**: 50MB+ available
- **Disk Space**: 10MB for the package + space for local database

## 📋 Dependencies

Billfrog requires these main dependencies:

- **typer** - Modern CLI framework
- **rich** - Beautiful terminal output
- **openai** - OpenAI API client
- **supabase** - Supabase client for email delivery
- **jinja2** - Template engine for receipts
- **schedule** - Task scheduling
- **cryptography** - Secure API key storage
- **pydantic** - Data validation

All dependencies are automatically installed with the package.

## 🔗 Post-Installation Setup

After installation, you'll need to:

1. **Set up Supabase for email delivery** (see [Supabase Setup Guide](examples/supabase_setup.md))
2. **Configure Billfrog:**
   ```bash
   billfrog setup
   ```
3. **Add your first AI agent:**
   ```bash
   billfrog agent add --name "my-agent" --provider openai --api-key "sk-..." --email "me@example.com" --schedule weekly
   ```

## 🐛 Troubleshooting

### Common Issues

**Error: "billfrog command not found"**
- Make sure you've activated your virtual environment
- Try running `pip show billfrog` to verify installation
- Check that pip's bin directory is in your PATH

**Error: "No module named 'billfrog'"**
- Reinstall the package: `pip uninstall billfrog && pip install billfrog`
- Check Python version: `python --version` (must be 3.8+)

**Error: "Permission denied"**
- Use a virtual environment instead of system Python
- On macOS/Linux: `python3 -m venv venv && source venv/bin/activate`
- On Windows: `python -m venv venv && venv\Scripts\activate`

**Slow installation**
- Some dependencies (like cryptography) require compilation
- Consider using pre-compiled wheels: `pip install --only-binary=all billfrog`

### Development Issues

**Import errors during development:**
- Make sure you installed with `-e` flag: `pip install -e .`
- Check that all dependencies are installed: `pip install -e ".[dev]"`

**Tests failing:**
- Run the package test: `python test_package.py`
- Check code quality: `black billfrog/ && isort billfrog/ && flake8 billfrog/`

## 🔄 Updating Billfrog

### Update from PyPI
```bash
pip install --upgrade billfrog
```

### Update Development Installation
```bash
git pull origin main
pip install -e ".[dev]"
```

## 🗑️ Uninstalling

To completely remove Billfrog:

```bash
# Uninstall the package
pip uninstall billfrog

# Remove configuration files (optional)
rm -rf ~/.billfrog/
```

## 🌐 Alternative Installation Methods

### Using Conda

```bash
# Create conda environment
conda create -n billfrog python=3.11
conda activate billfrog

# Install from PyPI
pip install billfrog
```

### Using Poetry

```bash
# If you use Poetry for dependency management
poetry add billfrog

# Or for development
poetry add --group dev billfrog
```

### Docker Installation

```bash
# Pull the Docker image (when available)
docker pull billfrog/billfrog:latest

# Run Billfrog in Docker
docker run -it billfrog/billfrog:latest billfrog --help
```

## 📝 Building from Source

For package maintainers:

```bash
# Install build tools
pip install build twine

# Build the package
python -m build

# Upload to PyPI (maintainers only)
twine upload dist/*
```

## 🆘 Getting Help

If you encounter issues:

1. Check the [FAQ](https://github.com/billfrog-dev/billfrog/wiki/FAQ)
2. Search [existing issues](https://github.com/billfrog-dev/billfrog/issues)
3. Create a [new issue](https://github.com/billfrog-dev/billfrog/issues/new)
4. Join our [Discord community](https://discord.gg/billfrog)
5. Email support: support@billfrog.dev

When reporting issues, please include:
- Your operating system and Python version
- The complete error message
- Steps to reproduce the problem
- Output of `billfrog --version` (if available)