
# Installation Guide

This toolkit supports multiple Python package management options for maximum compatibility.

## Prerequisites

- Python 3.12+ (recommended: Python 3.13.0rc2)
- Git (for cloning the repository)

## Installation Options

### Option 1: UV (Recommended - Fast & Modern)

**Install UV if needed:**
    pip install uv

**Create virtual environment:**
    uv venv

**Activate environment:**
    # Linux/Mac:
    source .venv/bin/activate
    # Windows:
    .venv\Scripts\activate

**Install dependencies:**
    uv pip install -e .
    # OR from requirements:
    uv pip install -r requirements.txt

**Run application:**
    python PatchReader.py

### Option 2: Standard venv + pip (Universal)

**Check venv availability (usually pre-installed):**
    python -m venv --help

**If venv is missing:**
    # Ubuntu/Debian:
    sudo apt install python3-venv
    
    # CentOS/RHEL/Fedora:
    sudo yum install python3-venv
    # or newer systems:
    sudo dnf install python3-venv
    
    # Arch Linux:
    sudo pacman -S python-venv
    
    # macOS (if somehow missing):
    brew install python
    # or
    pip install virtualenv
    
    # Windows (if somehow missing):
    pip install virtualenv
    
    # Universal solution for any OS:
    pip install virtualenv

**Create virtual environment:**
    python -m venv venv

**Activate environment:**
    # Linux/Mac:
    source venv/bin/activate
    # Windows:
    venv\Scripts\activate

**Install dependencies:**
    pip install -e .
    # OR from requirements:
    pip install -r requirements.txt

**Run application:**
    python PatchReader.py

### Option 3: Poetry (For Poetry Users)

**Install Poetry if needed:**
    # Official installer (recommended):
    curl -sSL https://install.python-poetry.org | python3 -
    # Or via pip:
    pip install poetry

**Create new project (if starting fresh):**
    poetry new film-toolkit
    cd film-toolkit

**Or initialize existing project:**
    poetry init

**Install dependencies:**
    poetry install

**Add new dependencies:**
    poetry add package-name
    poetry add --group dev pytest black flake8

**Run application:**
    poetry run python PatchReader.py

**Activate shell:**
    poetry shell
    python PatchReader.py

### Option 4: Conda/Mamba (Data Science)

**Install Conda/Mamba if needed:**
    # Miniconda (recommended):
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
    bash Miniconda3-latest-Linux-x86_64.sh
    
    # Or install mamba (faster):
    conda install mamba -n base -c conda-forge

**Create environment:**
    conda create -n film-toolkit python=3.13
    # OR with mamba:
    mamba create -n film-toolkit python=3.13

**Activate environment:**
    conda activate film-toolkit

**Install dependencies:**
    conda install pip
    pip install -e .
    # OR from requirements:
    pip install -r requirements.txt

**Run application:**
    python PatchReader.py

## Quick Start

1. **Clone repository:**
    git clone <your-repo-url>
    cd film-toolkit

2. **Choose your preferred method above**
3. **Run the application:**
    python PatchReader.py

## Troubleshooting

**Permission errors on Linux/Mac:**
    # Add to PATH if needed:
    export PATH="$HOME/.local/bin:$PATH"

**Python version issues:**
    # Check version:
    python --version
    # Use specific version:
    python3.13 -m venv venv