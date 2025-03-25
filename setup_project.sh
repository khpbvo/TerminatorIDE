#!/bin/bash

# Create main directories
mkdir -p src/terminatoride/panels
mkdir -p src/terminatoride/utils
mkdir -p tests
mkdir -p docs
mkdir -p resources

# Create initial Python files
touch src/terminatoride/__init__.py
touch src/terminatoride/app.py
touch src/terminatoride/panels/__init__.py
touch src/terminatoride/panels/left_panel.py
touch src/terminatoride/panels/editor_panel.py
touch src/terminatoride/panels/agent_panel.py
touch src/terminatoride/utils/__init__.py

# Make the script executable
chmod +x setup_project.sh

echo "Project structure created successfully!"
