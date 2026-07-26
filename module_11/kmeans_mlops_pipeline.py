"""Module 11 MLflow tracking pipeline for Grad Café K-Means clustering."""

from pathlib import Path
import re

import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.feature_extraction.text import TfidfVectorizer


DATA_PATH = Path("../module_9/final_clustered_data.csv")

TRACKING_URI = "http://127.0.0.1:8080"
EXPERIMENT_NAME = "Module 11 KMeans Clustering"
RUN_NAME = "KMeans 25 Clusters"

N_CLUSTERS = 25
MAX_ITER = 500
N_INIT = 5
RANDOM_STATE = 42
PCA_COMPONENTS = 75

MODEL_ARTIFACT_NAME = "clustering_model"


def clean_program_name(value: object) -> str:
    """Normalize program-name text for clustering."""
    text = str(value).strip()
    text = re.sub(r"\s+", " ", text)

    if text.lower() in {"", "none", "nan", "unknown"}:
        return ""

    return text


def load_data(path: Path) -> pd.DataFrame:
    """Load the Module 9 clustered dataset and clean program names."""
    if not path.exists():
        raise FileNotFoundError(
            f"Input dataset was not found: {path.resolve()}"
        )

    dataframe = pd.read_csv(path)

    if "program_name" not in dataframe.columns:
        raise KeyError(
            "Expected a 'program_name' column in the input dataset."
        )

    dataframe = dataframe.copy()

    dataframe["program_name"] = dataframe[
        "program_name"
    ].apply(clean_program_name)

    dataframe = dataframe.loc[
        dataframe["program_name"].ne("")
    ].copy()

    dataframe.reset_index(drop=True, inplace=True)

    return dataframe


def create_tfidf_features(
    dataframe: pd.DataFrame,
):
    """Convert program names into TF-IDF feature vectors."""
    vectorizer = TfidfVectorizer(
        stop_words="english",
        lowercase=True,
        strip_accents="unicode",
    )

    vectors = vectorizer.fit_transform(
        dataframe["program_name"].astype(str)
    )

    print(f"TF-IDF shape: {vectors.shape}")

    return vectors


def create_pca_features(
    vectors,
) -> np.ndarray:
    """Reduce TF-IDF features for K-Means training."""
    dense_vectors = vectors.toarray()

    component_count = min(
        PCA_COMPONENTS,
        dense_vectors.shape[0],
        dense_vectors.shape[1],
    )

    pca = PCA(
        n_components=component_count,
        svd_solver="randomized",
        random_state=RANDOM_STATE,
    )

    reduced_features = pca.fit_transform(dense_vectors)

    print(f"PCA output shape: {reduced_features.shape}")

    return reduced_features


def create_kmeans_model() -> KMeans:
    """Create the required K-Means model configuration."""
    return KMeans(
        n_clusters=N_CLUSTERS,
        max_iter=MAX_ITER,
        n_init=N_INIT,
        random_state=RANDOM_STATE,
    )


def configure_mlflow() -> None:
    """Configure MLflow tracking and experiment selection."""
    mlflow.set_tracking_uri(TRACKING_URI)

    mlflow.set_experiment(
        EXPERIMENT_NAME
    )


def train_and_log_model(
    features: np.ndarray,
) -> KMeans:
    """Train K-Means and log parameters, metric, and model to MLflow."""
    params = {
        "n_clusters": N_CLUSTERS,
        "max_iter": MAX_ITER,
        "n_init": N_INIT,
        "random_state": RANDOM_STATE,
    }

    model = create_kmeans_model()

    with mlflow.start_run(
        run_name=RUN_NAME
    ):
        model.fit(features)

        mlflow.log_params(params)

        mlflow.log_metric(
            "inertia",
            float(model.inertia_),
        )

        mlflow.set_tag(
            "model_type",
            "KMeans Clustering",
        )

        mlflow.set_tag(
            "module",
            "Module 11",
        )

        mlflow.sklearn.log_model(
            sk_model=model,
            name=MODEL_ARTIFACT_NAME,
            registered_model_name="Clustering",
        )

        print("\nMLflow run completed successfully.")
        print(f"Tracking URI: {TRACKING_URI}")
        print(f"Experiment: {EXPERIMENT_NAME}")
        print(f"Run name: {RUN_NAME}")
        print(f"Inertia: {model.inertia_:,.4f}")

    return model


def print_model_summary(
    dataframe: pd.DataFrame,
    model: KMeans,
) -> None:
    """Print a concise summary of the completed clustering run."""
    print("\nModel Summary")
    print("-" * 40)
    print(f"Rows used: {len(dataframe):,}")
    print(f"Clusters: {model.n_clusters}")
    print(f"Max iterations: {model.max_iter}")
    print(f"n_init: {model.n_init}")
    print(f"Random state: {model.random_state}")
    print(f"Inertia: {model.inertia_:,.4f}")


def main() -> None:
    """Run the complete Module 11 MLOps clustering workflow."""
    configure_mlflow()

    dataframe = load_data(
        DATA_PATH
    )

    print(f"Rows loaded: {len(dataframe):,}")

    vectors = create_tfidf_features(
        dataframe
    )

    features = create_pca_features(
        vectors
    )

    model = train_and_log_model(
        features
    )

    print_model_summary(
        dataframe,
        model,
    )


if __name__ == "__main__":
    main()
