# TerminatorIDE Developer Guide

This guide is for developers who want to contribute to TerminatorIDE or build their own features on top of it.

## Contents

- [Architecture Overview](architecture.md)
- [Setting Up Development Environment](dev_environment.md)
- [Project Structure](project_structure.md)
- [OpenAI Agent SDK Integration](agent_sdk.md)
- [Textual UI Framework](textual_ui.md)
- [Creating New Panels](panels.md)
- [Adding Tools for the AI Agent](agent_tools.md)
- [Testing Guidelines](testing.md)
- [Contribution Workflow](contributing.md)

## Architecture

TerminatorIDE follows a modular architecture with these main components:

1. **UI Layer**: Built with Textual, providing a terminal-based interface with three main panels.
2. **Agent Layer**: Integration with OpenAI's Agent SDK for AI capabilities.
3. **Editor Layer**: Integration with terminal-based editors (vim, nano, etc.)
4. **Integration Layer**: Git and SSH functionalities.

## Contribution Workflow

1. Fork the repository
2. Create a new branch for your feature
3. Implement and test your changes
4. Submit a pull request with a clear description of your changes

For more detailed information, see [Contribution Workflow](contributing.md).
