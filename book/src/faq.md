# FAQ & Troubleshooting

## 1. Virtual environment not auto-activated after `uv sync --dev`

**Issue**:\
After running `uv sync --dev`, the virtual environment (`.venv`) is created but not automatically activated.

**Solution**:\
Manually activate the environment:

```bash
source .venv/bin/activate
```
