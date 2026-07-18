"""Create exploratory visualizations for the Module 10 dashboard."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import seaborn as sns


DATA_PATH = Path("final_clustered_data.csv")

ACCEPTANCE_BY_DEGREE_PATH = Path("acceptance_by_degree.png")
GPA_BY_OUTCOME_PATH = Path("gpa_by_outcome.png")
ADMISSIONS_BY_TERM_PATH = Path("admissions_by_term.html")

STATUS_ORDER = [
    "Accepted",
    "Rejected",
    "Waitlisted",
]

DEGREE_ORDER = [
    "Master's",
    "PhD",
]


def load_data(path: Path) -> pd.DataFrame:
    """Load the graduate admissions dataset."""
    if not path.exists():
        raise FileNotFoundError(
            f"Input dataset was not found: {path.resolve()}"
        )

    dataframe = pd.read_csv(path)

    required_columns = {
        "applicant_status",
        "degree",
        "gpa",
        "start_term",
        "student_type",
    }

    missing_columns = required_columns.difference(dataframe.columns)

    if missing_columns:
        raise KeyError(
            "Missing required columns: "
            + ", ".join(sorted(missing_columns))
        )

    return dataframe.copy()


def normalize_status(value: object) -> str:
    """Convert raw applicant status values into standard categories."""
    text = str(value).strip().lower()

    if "accept" in text:
        return "Accepted"

    if "reject" in text:
        return "Rejected"

    if "wait" in text:
        return "Waitlisted"

    return "Other"


def normalize_degree(value: object) -> str:
    """Convert degree values into consistent categories."""
    text = str(value).strip().lower()

    if "master" in text:
        return "Master's"

    if "phd" in text or "ph.d" in text or "doctor" in text:
        return "PhD"

    return "Other"


def normalize_student_type(value: object) -> str:
    """Convert student-type values into consistent categories."""
    text = str(value).strip().lower()

    if "international" in text:
        return "International"

    if "american" in text or "domestic" in text:
        return "Domestic"

    return "Other"


def clean_start_term(value: object) -> str:
    """Standardize application start-term text."""
    if pd.isna(value):
        return "Unknown"

    text = " ".join(str(value).strip().split())

    if not text:
        return "Unknown"

    return text.title()


def prepare_data(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Clean the fields required for exploratory analysis."""
    cleaned_data = dataframe.copy()

    cleaned_data["Outcome"] = cleaned_data[
        "applicant_status"
    ].apply(normalize_status)

    cleaned_data["Degree"] = cleaned_data[
        "degree"
    ].apply(normalize_degree)

    cleaned_data["Student Type"] = cleaned_data[
        "student_type"
    ].apply(normalize_student_type)

    cleaned_data["Start Term"] = cleaned_data[
        "start_term"
    ].apply(clean_start_term)

    cleaned_data["GPA"] = pd.to_numeric(
        cleaned_data["gpa"],
        errors="coerce",
    )

    cleaned_data.loc[
        ~cleaned_data["GPA"].between(0.0, 4.0),
        "GPA",
    ] = np.nan

    return cleaned_data


def create_acceptance_by_degree(
    dataframe: pd.DataFrame,
    output_path: Path,
) -> None:
    """Create a Seaborn chart of admission outcomes by degree."""
    plot_data = dataframe.loc[
        dataframe["Degree"].isin(DEGREE_ORDER)
        & dataframe["Outcome"].isin(STATUS_ORDER)
    ].copy()

    grouped_data = (
        plot_data.groupby(
            ["Degree", "Outcome"],
            observed=True,
        )
        .size()
        .rename("Applications")
        .reset_index()
    )

    degree_totals = grouped_data.groupby(
        "Degree",
        observed=True,
    )["Applications"].transform("sum")

    grouped_data["Percentage"] = (
        grouped_data["Applications"]
        / degree_totals
        * 100
    )

    sns.set_theme(style="whitegrid")

    figure, axis = plt.subplots(figsize=(11, 7))

    sns.barplot(
        data=grouped_data,
        x="Degree",
        y="Percentage",
        hue="Outcome",
        hue_order=STATUS_ORDER,
        order=DEGREE_ORDER,
        ax=axis,
    )

    axis.set_title(
        "Graduate Admission Outcomes by Degree Type",
        fontsize=15,
        pad=15,
    )
    axis.set_xlabel("Degree Type")
    axis.set_ylabel("Share of Applications (%)")
    axis.legend(
        title="Admission Outcome",
        frameon=True,
    )

    for container in axis.containers:
        axis.bar_label(
            container,
            fmt="%.1f%%",
            padding=3,
            fontsize=9,
        )

    figure.tight_layout()
    figure.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight",
    )
    plt.close(figure)


def create_gpa_by_outcome(
    dataframe: pd.DataFrame,
    output_path: Path,
) -> None:
    """Create a Matplotlib boxplot of GPA by admission outcome."""
    plot_data = dataframe.loc[
        dataframe["Outcome"].isin(STATUS_ORDER)
        & dataframe["GPA"].notna()
    ].copy()

    gpa_groups = [
        plot_data.loc[
            plot_data["Outcome"] == outcome,
            "GPA",
        ]
        for outcome in STATUS_ORDER
    ]

    figure, axis = plt.subplots(figsize=(10, 7))

    boxplot = axis.boxplot(
        gpa_groups,
        tick_labels=STATUS_ORDER,
        patch_artist=True,
        showmeans=True,
        medianprops={
            "linewidth": 2,
        },
        meanprops={
            "marker": "D",
            "markeredgecolor": "black",
            "markerfacecolor": "white",
        },
    )

    for patch in boxplot["boxes"]:
        patch.set_alpha(0.65)

    axis.set_title(
        "Applicant GPA Distribution by Admission Outcome",
        fontsize=15,
        pad=15,
    )
    axis.set_xlabel("Admission Outcome")
    axis.set_ylabel("GPA (4.0 scale)")
    axis.set_ylim(2.0, 4.05)
    axis.grid(
        axis="y",
        alpha=0.3,
    )

    axis.plot(
        [],
        [],
        marker="D",
        linestyle="None",
        markeredgecolor="black",
        markerfacecolor="white",
        label="Mean GPA",
    )
    axis.legend(loc="lower right")

    figure.tight_layout()
    figure.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight",
    )
    plt.close(figure)


def create_admissions_by_term(
    dataframe: pd.DataFrame,
    output_path: Path,
) -> None:
    """Create an interactive Plotly chart of outcomes by start term."""
    plot_data = dataframe.loc[
        dataframe["Outcome"].isin(STATUS_ORDER)
        & dataframe["Start Term"].ne("Unknown")
    ].copy()

    most_common_terms = (
        plot_data["Start Term"]
        .value_counts()
        .head(10)
        .index
    )

    plot_data = plot_data.loc[
        plot_data["Start Term"].isin(most_common_terms)
    ].copy()

    grouped_data = (
        plot_data.groupby(
            [
                "Start Term",
                "Outcome",
                "Student Type",
            ],
            observed=True,
        )
        .size()
        .rename("Applications")
        .reset_index()
    )

    term_order = (
        plot_data["Start Term"]
        .value_counts()
        .loc[most_common_terms]
        .index
        .tolist()
    )

    figure = px.bar(
        grouped_data,
        x="Start Term",
        y="Applications",
        color="Outcome",
        facet_row="Student Type",
        category_orders={
            "Start Term": term_order,
            "Outcome": STATUS_ORDER,
            "Student Type": [
                "Domestic",
                "International",
                "Other",
            ],
        },
        title=(
            "Interactive Admission Outcomes by Start Term "
            "and Student Type"
        ),
        labels={
            "Applications": "Number of Applications",
            "Start Term": "Start Term",
            "Outcome": "Admission Outcome",
        },
        hover_data={
            "Student Type": True,
            "Applications": ":,",
        },
    )

    figure.update_layout(
        barmode="stack",
        legend_title_text="Admission Outcome",
        hovermode="x unified",
        height=850,
        margin={
            "l": 70,
            "r": 40,
            "t": 100,
            "b": 100,
        },
    )

    figure.update_xaxes(
        tickangle=-35,
    )

    figure.for_each_annotation(
        lambda annotation: annotation.update(
            text=annotation.text.split("=")[-1]
        )
    )

    figure.write_html(
        output_path,
        include_plotlyjs="cdn",
        full_html=True,
    )


def print_summary(dataframe: pd.DataFrame) -> None:
    """Print basic data-quality and analytical summaries."""
    analyzed_outcomes = dataframe[
        dataframe["Outcome"].isin(STATUS_ORDER)
    ]

    print(f"Rows loaded: {len(dataframe):,}")
    print(
        "Rows with recognized outcomes:",
        f"{len(analyzed_outcomes):,}",
    )
    print(
        "Rows with valid GPA values:",
        f"{dataframe['GPA'].notna().sum():,}",
    )

    print("\nAdmission outcomes:")
    print(
        analyzed_outcomes["Outcome"]
        .value_counts()
        .to_string()
    )

    print("\nMedian GPA by outcome:")
    print(
        analyzed_outcomes.groupby(
            "Outcome",
            observed=True,
        )["GPA"]
        .median()
        .reindex(STATUS_ORDER)
        .round(2)
        .to_string()
    )


def main() -> None:
    """Generate all Module 10 exploratory visualizations."""
    dataframe = load_data(DATA_PATH)
    cleaned_data = prepare_data(dataframe)

    print_summary(cleaned_data)

    create_acceptance_by_degree(
        cleaned_data,
        ACCEPTANCE_BY_DEGREE_PATH,
    )

    create_gpa_by_outcome(
        cleaned_data,
        GPA_BY_OUTCOME_PATH,
    )

    create_admissions_by_term(
        cleaned_data,
        ADMISSIONS_BY_TERM_PATH,
    )

    print("\nVisualization files created:")
    print(f"Saved: {ACCEPTANCE_BY_DEGREE_PATH}")
    print(f"Saved: {GPA_BY_OUTCOME_PATH}")
    print(f"Saved: {ADMISSIONS_BY_TERM_PATH}")


if __name__ == "__main__":
    main()
