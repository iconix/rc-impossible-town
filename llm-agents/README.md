A multi-agent simulation with LLM-powered agents interacting in a virtual world.

# Installation

## Dependencies

This project uses [uv](https://github.com/astral-sh/uv) for Python package management. Make sure it's installed on your system.

## Ollama (Optional)

If you want to run models locally instead of using Together AI, you'll need to install Ollama:

1. Visit [Ollama's official website](https://ollama.com/download)
2. Download and install the version for your operating system (Windows, macOS, or Linux)
3. After installation, you can pull models using:
   ```bash
   ollama pull llama3.2
   ```
4. Verify installation with:
   ```bash
   ollama list
   ```

# Run Simulation

### Basic Usage

```bash
$ uv run run_simulation.py
```

This will run the simulation with default settings using the [Together AI](https://www.together.ai/) LLM provider and a graphical user interface.

### Useful Command Line Options

#### LLM Provider Options

```bash
# Use Ollama with a specific local model
$ uv run run_simulation.py --llm-provider ollama --llm-model llama3.2
# Use Together AI with your API key
$ uv run run_simulation.py --llm-provider together --api-key YOUR_API_KEY
```


#### Simulation Modes

```bash
# Run a simpler version with fewer locations
$ uv run run_simulation.py --basic-simulation
# Run in console mode (no GUI)
$ uv run run_simulation.py --console-mode
# Run with notepad mode (agents use notepad instead of knowledge)
$ uv run run_simulation.py --use-notepad
```


#### Testing

```bash
# Run in test mode with predefined sample actions
$ uv run run_simulation.py --test-mode
```


### Available Options

- `--llm-provider`: Choose the LLM provider (`ollama` or `together`). Default: `together`
- `--llm-model`: Specify which model to use. Default: `meta-llama/Llama-3.3-70B-Instruct-Turbo-Free`
- `--api-key`: Provide API key for providers that require authentication
- `--basic-simulation`: Use a simplified simulation with fewer locations
- `--console-mode`: Run without the graphical user interface
- `--use-notepad`: Use notepad instead of knowledge in agent prompts
- `--test-mode`: Run in test mode with sample actions

# Development

## Code Formatting and Linting

This project uses [Ruff](https://docs.astral.sh/ruff/) for both code formatting and linting.

### Format code with Ruff

```bash
# Format all Python files
$ uv run ruff format

# Format a specific file
$ uv run ruff format path/to/file.py
```

### Lint code with Ruff

```bash
# Run Ruff linter on all Python files
$ uv run ruff check

# Run Ruff with automatic fixing
$ uv run ruff check --fix

# Run Ruff on a specific file
$ uv run ruff check path/to/file.py
```

Run these tools before submitting changes to ensure consistent code style and quality.
