"""Module 9 K-Means clustering analysis for Grad Café program data."""

from pathlib import Path
import re

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.feature_extraction.text import TfidfVectorizer


DATA_PATH = Path("../module_8/cleaned_applicant_data.csv")

INITIAL_CLUSTER_PATH = Path("initial_cluster.png")
CLUSTERED_DATAFRAME_PATH = Path("clustered_dataFrame.png")
ELBOW_PATH = Path("elbow.png")
COMPUTER_SCIENCE_PATH = Path("computer_science.png")
PHILOSOPHY_PATH = Path("philosophy.png")
FINAL_DATA_PATH = Path("final_clustered_data.csv")

INITIAL_CLUSTER_COUNT = 50
FINAL_CLUSTER_COUNT = 85
PCA_COMPONENTS = 75
RANDOM_STATE = 42

MONTH_PATTERN = (
    "Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec"
)


def extract_program_name(row: pd.Series) -> str:
    """Extract the graduate program name from the raw listing."""
    raw_listing = str(row.get("raw_listing", "")).strip()
    university = str(row.get("university", "")).strip()
    degree = str(row.get("degree", "")).strip()

    if not raw_listing or not degree:
        return ""

    if university and raw_listing.lower().startswith(university.lower()):
        remaining_text = raw_listing[len(university):].strip()
    else:
        remaining_text = raw_listing

    escaped_degree = re.escape(degree)

    pattern = (
        rf"\s+{escaped_degree}\s+"
        rf"(?:{MONTH_PATTERN})\s+\d{{1,2}},\s+\d{{4}}"
    )

    program_name = re.split(
        pattern,
        remaining_text,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]

    return re.sub(r"\s+", " ", program_name).strip()


def merge_application_rows(source_data: pd.DataFrame) -> pd.DataFrame:
    """
    Merge each program row with the following applicant-details row.

    The Module 8 dataset stores many applications across two rows. The
    first row contains the university, degree, and raw listing, while the
    next row often contains GRE, GPA, status, and student details.
    """
    merged_records = []

    detail_columns = [
        "comments",
        "applicant_status",
        "acceptance_date",
        "rejection_date",
        "start_term",
        "student_type",
        "gre_score",
        "gre_v_score",
        "gpa",
        "gre_aw",
    ]

    for row_number in range(len(source_data)):
        current_row = source_data.iloc[row_number]

        if pd.isna(current_row.get("degree")):
            continue

        if pd.isna(current_row.get("raw_listing")):
            continue

        record = current_row.copy()

        if row_number + 1 < len(source_data):
            next_row = source_data.iloc[row_number + 1]

            if pd.isna(next_row.get("degree")):
                for column in detail_columns:
                    if (
                        column in source_data.columns
                        and pd.notna(next_row.get(column))
                    ):
                        record[column] = next_row[column]

        merged_records.append(record)

    return pd.DataFrame(merged_records).reset_index(drop=True)


def load_data(path: Path) -> pd.DataFrame:
    """Load, merge, extract, and clean the Module 8 dataset."""
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found at: {path.resolve()}"
        )

    source_data = pd.read_csv(path)

    required_columns = {
        "university",
        "degree",
        "raw_listing",
        "gre_score",
        "gre_v_score",
    }

    missing_columns = required_columns.difference(source_data.columns)

    if missing_columns:
        raise KeyError(
            "Missing required columns: "
            + ", ".join(sorted(missing_columns))
        )

    dataframe = merge_application_rows(source_data)

    dataframe["program_name"] = dataframe.apply(
        extract_program_name,
        axis=1,
    )

    invalid_values = {
        "",
        "none",
        "nan",
        "unknown",
    }

    valid_programs = ~(
        dataframe["program_name"]
        .astype(str)
        .str.strip()
        .str.lower()
        .isin(invalid_values)
    )

    dataframe = dataframe.loc[valid_programs].copy()

    dataframe["program_name"] = (
        dataframe["program_name"]
        .astype(str)
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
    )

    dataframe["university"] = (
        dataframe["university"]
        .fillna("Unknown")
        .astype(str)
        .str.strip()
    )

    for score_column in [
        "gre_score",
        "gre_v_score",
        "gpa",
        "gre_aw",
    ]:
        if score_column in dataframe.columns:
            dataframe[score_column] = pd.to_numeric(
                dataframe[score_column],
                errors="coerce",
            )

    return dataframe.reset_index(drop=True)


def create_program_vectors(
    dataframe: pd.DataFrame,
):
    """Convert program names into TF-IDF vectors."""
    vectorizer = TfidfVectorizer(
        stop_words="english",
        max_features=1000,
        lowercase=True,
        strip_accents="unicode",
    )

    vectors = vectorizer.fit_transform(
        dataframe["program_name"].astype(str)
    )

    return vectors


def create_initial_clusters(
    dense_vectors: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Create two-dimensional PCA data and 50 initial clusters."""
    pca = PCA(
        n_components=2,
        random_state=RANDOM_STATE,
    )

    reduced_vectors = pca.fit_transform(dense_vectors)

    model = KMeans(
        n_clusters=INITIAL_CLUSTER_COUNT,
        max_iter=100,
        n_init=5,
        random_state=RANDOM_STATE,
    )

    labels = model.fit_predict(reduced_vectors)

    print(f"Initial PCA shape: {reduced_vectors.shape}")
    print(f"Initial PCA configuration: {pca}")
    print(
        "Initial PCA explained variance:",
        f"{pca.explained_variance_ratio_.sum():.4f}",
    )

    return reduced_vectors, labels


def create_analysis_features(
    dense_vectors: np.ndarray,
) -> np.ndarray:
    """Create 75 PCA components for elbow and final analysis."""
    maximum_components = min(
        PCA_COMPONENTS,
        dense_vectors.shape[0],
        dense_vectors.shape[1],
    )

    pca = PCA(
        n_components=maximum_components,
        svd_solver="randomized",
        random_state=RANDOM_STATE,
    )

    analysis_features = pca.fit_transform(dense_vectors)

    print(f"Analysis PCA shape: {analysis_features.shape}")
    print(f"Analysis PCA configuration: {pca}")
    print(
        "Analysis PCA explained variance:",
        f"{pca.explained_variance_ratio_.sum():.4f}",
    )

    return analysis_features


def save_initial_cluster_plot(
    reduced_vectors: np.ndarray,
    labels: np.ndarray,
    output_path: Path,
) -> None:
    """Save the initial two-dimensional clustering plot."""
    plt.figure(figsize=(12, 8))

    scatter = plt.scatter(
        reduced_vectors[:, 0],
        reduced_vectors[:, 1],
        c=labels,
        cmap="tab20",
        s=10,
        alpha=0.7,
    )

    plt.title("Initial K-Means Clustering of Graduate Programs")
    plt.xlabel("Principal Component 1")
    plt.ylabel("Principal Component 2")
    plt.colorbar(scatter, label="Cluster")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def save_clustered_dataframe(
    dataframe: pd.DataFrame,
    output_path: Path,
) -> None:
    """Save a 100-row preview containing initial cluster labels."""
    preview_columns = [
        "program_name",
        "university",
        "initial_cluster",
    ]

    preview = dataframe[preview_columns].head(100).copy()

    figure, axis = plt.subplots(figsize=(16, 30))
    axis.axis("off")

    table = axis.table(
        cellText=preview.values,
        colLabels=preview.columns,
        loc="center",
        cellLoc="left",
    )

    table.auto_set_font_size(False)
    table.set_fontsize(5)
    table.scale(1, 1.15)

    axis.set_title(
        "100 Graduate Program Records with Initial Cluster Labels",
        pad=20,
    )

    figure.tight_layout()
    figure.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight",
    )
    plt.close(figure)


def create_elbow_plot(
    analysis_features: np.ndarray,
    output_path: Path,
) -> None:
    """Calculate K-Means inertia for k=1 through k=100."""
    cluster_counts = list(range(1, 101))
    inertia_values = []

    print("\nRunning elbow analysis from k=1 to k=100...")

    for cluster_count in cluster_counts:
        model = KMeans(
            n_clusters=cluster_count,
            max_iter=100,
            n_init=5,
            random_state=RANDOM_STATE,
        )

        model.fit(analysis_features)
        inertia_values.append(model.inertia_)

        print(
            f"k={cluster_count:3d}, "
            f"inertia={model.inertia_:,.2f}"
        )

    plt.figure(figsize=(12, 7))

    plt.plot(
        cluster_counts,
        inertia_values,
        marker="o",
        markersize=3,
        linewidth=1.5,
        label="K-Means inertia",
    )

    plt.axvline(
        x=FINAL_CLUSTER_COUNT,
        linestyle="--",
        label=f"Selected k = {FINAL_CLUSTER_COUNT}",
    )

    plt.title("Elbow Method for Graduate Program Clustering")
    plt.xlabel("Number of Clusters (k)")
    plt.ylabel("Inertia")
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def run_final_clustering(
    analysis_features: np.ndarray,
) -> np.ndarray:
    """Run final K-Means using 85 clusters."""
    model = KMeans(
        n_clusters=FINAL_CLUSTER_COUNT,
        max_iter=100,
        n_init=5,
        random_state=RANDOM_STATE,
    )

    labels = model.fit_predict(analysis_features)

    print(
        "\nFinal clustering completed with "
        f"{len(np.unique(labels))} clusters."
    )

    return labels


def identify_cluster(
    dataframe: pd.DataFrame,
    keywords: list[str],
    description: str,
) -> int:
    """Find the cluster containing the most keyword-matched programs."""
    program_names = (
        dataframe["program_name"]
        .fillna("")
        .astype(str)
        .str.lower()
    )

    pattern = "|".join(
        re.escape(keyword.lower())
        for keyword in keywords
    )

    matching_rows = dataframe.loc[
        program_names.str.contains(
            pattern,
            regex=True,
            na=False,
        )
    ]

    if matching_rows.empty:
        raise ValueError(
            f"No program names matched {description}."
        )

    cluster_counts = matching_rows["final_cluster"].value_counts()
    selected_cluster = int(cluster_counts.index[0])
    matched_count = int(cluster_counts.iloc[0])

    print(
        f"\n{description} cluster: {selected_cluster}"
    )
    print(
        f"Keyword-matching records in selected cluster: "
        f"{matched_count}"
    )

    examples = (
        matching_rows.loc[
            matching_rows["final_cluster"] == selected_cluster,
            "program_name",
        ]
        .drop_duplicates()
        .head(12)
        .tolist()
    )

    print(f"Example {description} programs:")

    for program_name in examples:
        print(f"  - {program_name}")

    return selected_cluster


def get_cluster_score_data(
    dataframe: pd.DataFrame,
    cluster_number: int,
) -> pd.DataFrame:
    """Return valid GRE observations from a selected cluster."""
    cluster_data = dataframe.loc[
        dataframe["final_cluster"] == cluster_number,
        [
            "program_name",
            "university",
            "gre_score",
            "gre_v_score",
        ],
    ].copy()

    cluster_data["gre_score"] = pd.to_numeric(
        cluster_data["gre_score"],
        errors="coerce",
    )

    cluster_data["gre_v_score"] = pd.to_numeric(
        cluster_data["gre_v_score"],
        errors="coerce",
    )

    return cluster_data.dropna(
        subset=["gre_score", "gre_v_score"],
        how="all",
    )


def save_gre_boxplot(
    cluster_data: pd.DataFrame,
    description: str,
    output_path: Path,
) -> None:
    """Save GRE and GRE Verbal boxplots for one cluster."""
    gre_scores = cluster_data["gre_score"].dropna()
    gre_verbal_scores = cluster_data["gre_v_score"].dropna()

    if gre_scores.empty and gre_verbal_scores.empty:
        raise ValueError(
            f"No GRE values were available for {description}."
        )

    plot_values = []
    plot_labels = []

    if not gre_scores.empty:
        plot_values.append(gre_scores)
        plot_labels.append("GRE")

    if not gre_verbal_scores.empty:
        plot_values.append(gre_verbal_scores)
        plot_labels.append("GRE Verbal")

    plt.figure(figsize=(10, 7))

    plt.boxplot(
        plot_values,
        tick_labels=plot_labels,
        showmeans=True,
    )

    plt.title(
        f"GRE Score Distribution for {description} Programs"
    )
    plt.xlabel("GRE Component")
    plt.ylabel("Score")
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def print_score_summary(
    cluster_data: pd.DataFrame,
    description: str,
) -> None:
    """Print GRE descriptive statistics for a selected cluster."""
    print(f"\n{description} GRE summary:")
    print(
        cluster_data[
            ["gre_score", "gre_v_score"]
        ]
        .describe()
        .round(2)
    )


def analyze_required_programs(
    dataframe: pd.DataFrame,
) -> None:
    """Analyze Computer Science and Philosophy program clusters."""
    computer_science_cluster = identify_cluster(
        dataframe,
        [
            "computer science",
            "computer science and engineering",
            "computing",
            "software engineering",
            "informatics",
        ],
        "Computer Science",
    )

    philosophy_cluster = identify_cluster(
        dataframe,
        [
            "philosophy",
            "philosophical",
        ],
        "Philosophy",
    )

    computer_science_data = get_cluster_score_data(
        dataframe,
        computer_science_cluster,
    )

    philosophy_data = get_cluster_score_data(
        dataframe,
        philosophy_cluster,
    )

    print(
        "\nComputer Science rows with GRE information:",
        len(computer_science_data),
    )
    print(
        "Philosophy rows with GRE information:",
        len(philosophy_data),
    )

    print_score_summary(
        computer_science_data,
        "Computer Science",
    )

    print_score_summary(
        philosophy_data,
        "Philosophy",
    )

    save_gre_boxplot(
        computer_science_data,
        "Computer Science",
        COMPUTER_SCIENCE_PATH,
    )

    save_gre_boxplot(
        philosophy_data,
        "Philosophy",
        PHILOSOPHY_PATH,
    )

    print(
        "\nInterpretation: The boxplots compare the distributions "
        "of available GRE and GRE Verbal scores for programs grouped "
        "into the Computer Science and Philosophy clusters. Any extreme "
        "values or unexpected score ranges should be treated cautiously "
        "because the original data were entered by users and may require "
        "additional validation and cleaning."
    )


def print_dataset_summary(dataframe: pd.DataFrame) -> None:
    """Print key dataset information required by the assignment."""
    print(f"Valid merged records: {len(dataframe):,}")
    print(
        "Number of Program Input Names:",
        f"{dataframe['program_name'].nunique():,}",
    )
    print(
        "Rows with GRE scores:",
        f"{dataframe['gre_score'].notna().sum():,}",
    )
    print(
        "Rows with GRE Verbal scores:",
        f"{dataframe['gre_v_score'].notna().sum():,}",
    )

    computer_science_count = dataframe[
        "program_name"
    ].str.contains(
        "computer science",
        case=False,
        na=False,
    ).sum()

    philosophy_count = dataframe[
        "program_name"
    ].str.contains(
        "philosophy",
        case=False,
        na=False,
    ).sum()

    print(
        "Computer Science program matches:",
        f"{computer_science_count:,}",
    )
    print(
        "Philosophy program matches:",
        f"{philosophy_count:,}",
    )


def main() -> None:
    """Run the complete Module 9 clustering workflow."""
    dataframe = load_data(DATA_PATH)

    print_dataset_summary(dataframe)

    vectors = create_program_vectors(dataframe)

    print(f"TF-IDF matrix shape: {vectors.shape}")
    print(f"TF-IDF matrix type: {type(vectors)}")

    dense_vectors = vectors.toarray()

    reduced_vectors, initial_labels = create_initial_clusters(
        dense_vectors
    )

    dataframe["initial_cluster"] = initial_labels

    save_initial_cluster_plot(
        reduced_vectors,
        initial_labels,
        INITIAL_CLUSTER_PATH,
    )

    save_clustered_dataframe(
        dataframe,
        CLUSTERED_DATAFRAME_PATH,
    )

    analysis_features = create_analysis_features(
        dense_vectors
    )

    # create_elbow_plot(
    create_elbow_plot(
    #     analysis_features,
        analysis_features,
    #     ELBOW_PATH,
          ELBOW_PATH,
   # )
     )

    final_labels = run_final_clustering(
        analysis_features
    )

    dataframe["final_cluster"] = final_labels

    analyze_required_programs(dataframe)

    dataframe.to_csv(
        FINAL_DATA_PATH,
        index=False,
    )

    print("\nRequired files created:")
    print(f"Saved: {INITIAL_CLUSTER_PATH}")
    print(f"Saved: {CLUSTERED_DATAFRAME_PATH}")
    print(f"Saved: {ELBOW_PATH}")
    print(f"Saved: {COMPUTER_SCIENCE_PATH}")
    print(f"Saved: {PHILOSOPHY_PATH}")
    print(f"Saved: {FINAL_DATA_PATH}")


if __name__ == "__main__":
    main()
