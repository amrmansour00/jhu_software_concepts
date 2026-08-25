\# Module 11: MLflow K-Means MLOps Pipeline



\## Purpose



This project extends the Module 9 K-Means clustering workflow by adding MLflow experiment tracking.



The pipeline:

\- loads the graduate program dataset

\- creates TF-IDF features

\- reduces dimensionality using PCA

\- trains a K-Means clustering model

\- logs model parameters and inertia to MLflow

\- saves and registers the trained model



\## Required K-Means Parameters



\- `max\_iter = 500`

\- `n\_clusters = 25`

\- `n\_init = 5`

\- `random\_state = 42`



\## Tracked Metric



The model logs:



\- `inertia`



\## MLflow Setup



Create and activate a Python 3.12 virtual environment, then install the dependencies:



```powershell

python -m pip install -r requirements.txt

```



Start the local MLflow tracking server:



```powershell

python -m mlflow server --host 127.0.0.1 --port 8080

```



Open the MLflow UI in a browser:



```text

http://127.0.0.1:8080

```



\## Run the Pipeline



With the MLflow server running, open another terminal and run:



```powershell

python kmeans\_mlops\_pipeline.py

```



\## MLflow Output



Experiment:



```text

Module 11 KMeans Clustering

```



Run:



```text

KMeans 25 Clusters

```



Registered model:



```text

Clustering

```



The MLflow run records the four required K-Means parameters and the model inertia, and logs the trained K-Means model as an MLflow model artifact.



\## Required Screenshots



\- `cluster\_run.png` — successful MLflow training run

\- `cluster\_details.png` — logged K-Means parameters and inertia metric

\- `model\_details.png` — registered Clustering model and Version 1



\## Code Quality



`kmeans\_mlops\_pipeline.py` achieves a Pylint score of:



```text

10.00/10

```

