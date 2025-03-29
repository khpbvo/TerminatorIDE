# TerminatorIDE

An AI-powered terminal-based IDE that integrates OpenAI's Agent SDK for assisted development.

## Overview

TerminatorIDE is a powerful, terminal-based integrated development environment that leverages AI to help developers write, understand, and improve code. Built with Textual and the OpenAI Agent SDK, it provides a seamless development experience with intelligent features.

## Features

- **Three-panel interface**: File explorer, text editor, and AI agent interface
- **Git integration**: Version control at your fingertips
- **Remote editing**: Edit files over SSH
- **AI assistance**: Code completion, explanation, refactoring, and more
- **Terminal-based**: Light and fast, runs in any terminal

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/TerminatorIDE.git
   cd TerminatorIDE
   ```

2. Set up a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the package in development mode:
   ```
   pip install -e .
   ```

4. Configure your OpenAI API key:
   ```
   export OPENAI_API_KEY=your_api_key_here
   ```

## Usage

Run the application:
```
python -m terminatoride.app
```

## Development

### Running Tests

To run all tests:
```
make test
```

Run unit tests only:
```
make test-unit
```

Run tests with coverage report:
```
make test-coverage
```

### Code Quality

Format code:
```
make format
```

Run linting:
```
make lint
```

## License

[MIT License](LICENSE)
