# AI Code Quality Assistant

## Overview

AI Code Quality Assistant is an AI-powered platform designed to improve software development workflows through automated code analysis, documentation generation, project restructuring, and architecture visualization.

This project was developed as part of a software engineering project conducted in partnership with Safran during my Financial Engineering curriculum at ESILV.

The objective was to create a tool capable of analyzing Python projects, improving code quality, generating documentation, and producing a cleaner and more maintainable project structure.

---

## Features

* Python project analysis
* Automated code formatting
* AI-powered documentation generation
* README generation
* Project restructuring and organization
* Dependency detection and requirements generation
* GitHub repository integration
* Interactive Streamlit interface
* Architecture visualization

---

## Technologies

* Python
* Streamlit
* AST (Abstract Syntax Trees)
* Ollama
* GitHub API
* Black
* HTML / CSS / JavaScript

---

## How It Works

The platform processes a Python project through a multi-step pipeline:

1. Project import from ZIP archive or GitHub repository
2. Code restructuring and architecture improvement
3. Automated code formatting
4. Documentation and README generation
5. Architecture analysis and visualization
6. Export of the transformed project

---

## Project Structure

```text
app.py                    # Streamlit interface
pipeline.py               # Processing pipeline
analysis.py               # Static analysis tools
github_integration.py     # GitHub integration
ollama_client.py          # AI model interaction
parsers.py                # Parsing utilities
utils.py                  # Helper functions
config.py                 # Configuration
```

---

## Installation

```bash
git clone https://github.com/HENRIDVX/AI-Code-Quality-Assistant.git
cd AI-Code-Quality-Assistant
pip install -r requirements.txt
```

---

## Usage

```bash
streamlit run app.py
```

Upload a Python project or provide a GitHub repository URL, then launch the processing pipeline through the web interface
Financial Engineering Student – ESILV

Project developed in collaboration with Safran.
