#!/bin/bash

# Initialize git repository
git init

# Add all files except .env and any other sensitive files
git add .
git reset -- .env*
git reset -- venv

# Create first commit
git commit -m "Initial commit: TerminatorIDE project structure"

# Configure user info if needed
echo "Enter your git username (leave blank to skip):"
read GIT_USERNAME
if [ ! -z "$GIT_USERNAME" ]; then
    git config user.name "$GIT_USERNAME"
fi

echo "Enter your git email (leave blank to skip):"
read GIT_EMAIL
if [ ! -z "$GIT_EMAIL" ]; then
    git config user.email "$GIT_EMAIL"
fi

echo "Git repository initialized successfully!"
chmod +x init_git.sh
