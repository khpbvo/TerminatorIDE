# Getting Started with TerminatorIDE

TerminatorIDE is an AI-powered terminal-based IDE that integrates OpenAI's Agent SDK to provide intelligent development assistance.

## Prerequisites

- Python 3.8+
- pip (Python package installer)
- git (for version control)
- OpenAI API key

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/TerminatorIDE.git
   cd TerminatorIDE
   ```

2. Set up a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure your OpenAI API key:
   ```bash
   cp .env.template .env
   ```
   Edit the `.env` file and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Running TerminatorIDE

Run the application:
```bash
python -m src.terminatoride.app
```

## Basic Usage

TerminatorIDE has a three-panel interface:

1. **Left Panel**: File explorer, Git integration, SSH management
2. **Middle Panel**: Text editor for writing and editing code
3. **Right Panel**: AI agent interface for assistance and code generation

### Keyboard Shortcuts

- `Ctrl+Q`: Quit the application
- `Ctrl+Tab`: Cycle between panels
- `F1`: Open command palette
- More shortcuts are available in the User Guide

## Next Steps

For more detailed information, check out:
- [User Guide](user_guide/README.md)
- [Developer Guide](developer_guide/README.md)
