# CMDO-ML

Teaching repository for the **Computational Methods for Design Optimization (CMDO)** machine learning (ML) module.

## Repository Layout

- `classical_examples/`: self-contained reference notebooks using public datasets
- `inclass_examples/notebooks/`: course notebooks for the CMDO exercises
- `inclass_examples/data/scalar/`: scalar Comma-Separated Values (CSV) datasets for tabular ML examples
- `inclass_examples/data/image/`: image datasets and associated CSV metadata
- `inclass_examples/artifacts/`: saved model artifacts, metadata, and preprocessing objects
- `gh_scripts/`: Grasshopper scripts for sampling, logging, encoding, and inference

## Environment Setup

### Create Conda Environment

Create and activate the `cmdo-ml` environment from [environment.yml](environment.yml):

```bash
conda env create -f environment.yml
conda activate cmdo-ml
```

If the environment already exists:

```bash
conda env update -f environment.yml --prune
```

Alternative: create a conda env first, then install from [requirements.txt](requirements.txt):

```bash
conda create -n cmdo-ml python=3.9.10 -y
conda activate cmdo-ml
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Verify Conda Environment

Before opening notebooks, verify that the active environment imports the core stack correctly:

```bash
python -c "import numpy, pandas, statsmodels, tensorflow as tf; print(numpy.__version__); print(pandas.__version__); print(statsmodels.__version__); print(tf.__version__)"
```

If this command fails, fix the environment first before troubleshooting notebook code.

### Setup VS Code

1. Open this project folder in VS Code:
   - VS Code UI: **File > Open Folder...** and select `CMDO-ML`
   - Terminal (optional): from repo root run `code .`
2. Install the **Python** and **Jupyter** extensions (Microsoft).
3. Open Command Palette:
   - macOS: `Cmd+Shift+P`
   - Windows: `Ctrl+Shift+P`
4. Run `Python: Select Interpreter` and choose `cmdo-ml`.
5. Open any `.ipynb` notebook and make sure the selected kernel is `cmdo-ml`.

## Jupyter Notebooks

### Scalar Classification

[mlp_classification_maxDisplacement.ipynb](inclass_examples/notebooks/mlp_classification_maxDisplacement.ipynb) introduces the first end-to-end scalar ML workflow:

- ingesting and cleaning tabular datasets
- simple Exploratory Data Analysis (EDA) using Principal Component Analysis (PCA) and t-distributed Stochastic Neighbor Embedding (t-SNE)
- defining a classification target
- leakage-safe preprocessing for scalar features
- creating and training a dense Multilayer Perceptron (MLP) with `ReLU` hidden activations and a `sigmoid` output activation
- introducing binary cross-entropy loss for classification
- classification evaluation

### Scalar Regression

[mlp_regression_maxDisplacement.ipynb](inclass_examples/notebooks/mlp_regression_maxDisplacement.ipynb) provides the scalar regression teaching example for:

- extending the scalar workflow to continuous targets
- using a dense MLP with `ReLU` hidden activations and a linear output layer
- introducing Mean Squared Error (MSE) loss and Mean Absolute Error (MAE), Root Mean Squared Error (RMSE) regression metrics
- residual analysis
- saving trained artifacts for inference

### Image Regression

[cnn_regression_maxDisplacement.ipynb](inclass_examples/notebooks/cnn_regression_maxDisplacement.ipynb) provides the image regression teaching example for:

- ingesting aligned CSV metadata and image files
- basic image-data quality checks
- image-specific EDA
- image normalization
- Ridge vs Convolutional Neural Network (CNN) comparison
- using `Conv2D + MaxPooling + Dense` layers with `ReLU` activations and a linear output layer
- applying MSE loss in an image-regression setting
- saving trained artifacts for inference

## Grasshopper Scripts

The scripts in `gh_scripts/` are designed to be used for collecting data and running pre-trained model inference within Grasshopper using the Python 3 component.

### Samplers

- [sampler_gridSweep.py](gh_scripts/sampler_gridSweep.py): deterministic parameter sweep
- [sampler_randomUniform.py](gh_scripts/sampler_randomUniform.py): random sampling with a fixed seed

### Loggers and Encoder

- [logger_scalarData.py](gh_scripts/logger_scalarData.py): writes scalar `X/Y` rows to CSV
- [encoder_imageData.py](gh_scripts/encoder_imageData.py): converts geometry into a `2D` grayscale image array
- [logger_imageData.py](gh_scripts/logger_imageData.py): writes an `ImageArray` to disk as a PNG

### Predictors

- [predictor_mlp.py](gh_scripts/predictor_mlp.py): loads the saved MLP regression model and predicts `max_disp`
- [predictor_cnn.py](gh_scripts/predictor_cnn.py): loads the saved CNN regression model and predicts `max_disp`

## Troubleshooting

### Windows ImportError

On some Windows 11 machines, importing libraries may fail with an error like:

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

Important: turning Smart App Control off can be a one-way change unless Windows is reset or reinstalled. Read Microsoft's notes before changing it:

- [App & browser control in Windows Security](https://support.microsoft.com/en-us/windows/app-browser-control-in-the-windows-security-app-8f68fb65-ebb4-3cfb-4bd7-ef0f376f3dc3)
- [Smart App Control FAQ](https://support.microsoft.com/en-us/windows/smart-app-control-frequently-asked-questions-285ea03d-fa88-4d56-882e-6698afdb7003)

If Smart App Control is already off, you can also inspect:

- `Event Viewer > Applications and Services Logs > Microsoft > Windows > CodeIntegrity > Operational`

### Kernel Confusion in VS Code

If a notebook behaves differently from the terminal, the most common cause is the wrong kernel.

Check that:

- the selected notebook kernel is `cmdo-ml`
- the interpreter shown by VS Code is also `cmdo-ml`
- you are not accidentally running in `base`
