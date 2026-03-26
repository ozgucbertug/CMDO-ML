# CMDO-ML

Teaching repository for the **Computational Methods for Design Optimization** ML module.

## Environment Setup

### Conda

Create and activate the `cmdo-ml` environment from `environment.yml`:

```bash
conda env create -f environment.yml
conda activate cmdo-ml
```

If the environment already exists and you want to refresh it:

```bash
conda env update -f environment.yml --prune
```

### VS Code Setup

1. Open this project folder in VS Code:
   - VS Code UI: **File > Open Folder...** and select `CMDO-ML`
   - Terminal (optional): from repo root run `code .`
2. Install the **Python** and **Jupyter** extensions (Microsoft).
3. Open Command Palette:
   - macOS: `Cmd+Shift+P`
   - Windows: `Ctrl+Shift+P`
4. Run `Python: Select Interpreter` and choose `cmdo-ml`.
5. Open any `.ipynb` notebook and select the `cmdo-ml` kernel when prompted.
   - You can also use the kernel picker in the notebook toolbar (top-right).