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

## Troubleshooting

### Windows ImportError

On some Windows 11 machines, importing libraries may fail to import with an error like:

```text
ImportError: DLL load failed while importing ...:
An Application Control policy has blocked this file.
```

If you see this, a common cause is **Smart App Control** blocking native Python extension files (`.pyd`) inside the conda environment.

To check:

1. Open **Windows Security**.
2. Go to **App & browser control**.
3. Open **Smart App Control** and check whether it is turned on.

If Smart App Control is the cause, turning it off may allow the environment to work correctly.

