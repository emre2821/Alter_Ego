# Configuration

Alter/Ego supports configuration through YAML files and environment variables. Environment variables take precedence over file-based configuration.

## Configuration File

Place a file named `alter_ego_config.yaml` in the package config directory (`src/alter_ego/assets/config/`) to customize settings.

```yaml
# Example alter_ego_config.yaml
persona_root: ./assets/personas
models_dir: ./models
memory_db: ./alter_ego_memory.db
log_path: ./assets/logs/chaos_echo_log.chaos
llm_model_name: your-model-name.gguf
```

## Environment Variables

Copy the `.env.example` file from the repository root to `.env` and customize as needed. All environment variables override their YAML counterparts.

| Variable | Description | Default |
|----------|-------------|---------|
| `GPT4ALL_MODEL_DIR` | Path to GPT4All models directory | `~/.local/share/nomic.ai/GPT4All` |
| `GPT4ALL_MODEL` | Specific model filename to load | None |
| `PERSONA_ROOT` | Directory containing persona definitions | `./assets/personas` |
| `ALTER_EGO_LOG_PATH` | Path to autosave echo log file | `./assets/logs/chaos_echo_log.chaos` |
| `ALTER_EGO_SWITCH_LOG` | Path to persona switch log file | `./alter_switch_log.chaos` |
| `MEMORY_DB` | Path to SQLite memory database | `./alter_ego_memory.db` |
| `ALTER_EGO_DUMMY_ONLY` | Use dummy LLM backend (`auto`, `on`, `off`) | `auto` |
| `GPT4ALL_NO_CUDA` | Disable CUDA acceleration (set to `1`) | Not set |

## Configuration Priority

1. **Environment variables** (highest priority)
2. **YAML configuration file**
3. **Built-in defaults** (lowest priority)

## Path Resolution

Paths can be specified as:
- **Absolute paths**: Used as-is
- **Relative paths**: Resolved relative to the package root
- **Home directory**: `~` expands to user home directory

## Example Setup

```bash
# Copy the example environment file
cp .env.example .env

# Edit with your preferred settings
nano .env

# Or use environment variables directly
export GPT4ALL_MODEL_DIR=/path/to/models
export GPT4ALL_MODEL=mistral-7b-instruct.gguf
```
