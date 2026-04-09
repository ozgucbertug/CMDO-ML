# CMDO-ML

Teaching repository for the **Computational Methods for Design Optimization** ML module.

## Repository Layout

- `classical_examples/`: self-contained reference notebooks using public datasets
- `inclass_examples/notebooks/`: course notebooks for the CMDO exercises
- `inclass_examples/data/scalar/`: scalar CSV datasets
- `inclass_examples/artifacts/`: saved model artifacts (model weights, scalars, metadata)
- `gh_scripts/`: Grasshopper scripts

## Environment Setup

### Conda

**Recommended:** create and activate the `cmdo-ml` environment from `environment.yml`:

```bash
conda env create -f environment.yml
conda activate cmdo-ml
```

If the environment already exists:

```bash
conda env update -f environment.yml --prune
```

**Alternative:** create a conda env, then install from `requirements.txt`:

```bash
conda create -n cmdo-ml python=3.9.10 -y
conda activate cmdo-ml
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Windows Notes

1. Run conda commands from **Anaconda Prompt** or a terminal where conda is initialized.
2. If `conda activate cmdo-ml` fails in PowerShell, run:

```powershell
conda init powershell
```

3. Close and reopen the terminal, then run:

```powershell
conda activate cmdo-ml
```

If you use Command Prompt (`cmd`) instead of PowerShell, initialize once with:

```bat
conda init cmd.exe
```

### VS Code Setup

1. Open this project folder in VS Code:
   - VS Code UI: **File > Open Folder...** and select `CMDO-ML` folder.
   - Terminal (optional): from repo root run `code .`.
2. Install the **Python** and **Jupyter** extensions (Microsoft).
3. Open Command Palette:
   - macOS: `Cmd+Shift+P`
   - Windows: `Ctrl+Shift+P`
4. Run `Python: Select Interpreter` and choose `cmdo-ml`.
5. Open any `.ipynb` notebook and select the `cmdo-ml` kernel when prompted.
   - You can also use the kernel picker in the notebook toolbar (top-right).
