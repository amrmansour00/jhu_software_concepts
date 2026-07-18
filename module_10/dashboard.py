"""Run the Module 10 graduate admissions dashboard."""

from pathlib import Path

import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html


DATA_PATH = Path("final_clustered_data.csv")

STATUS_ORDER = [
    "Accepted",
    "Rejected",
    "Waitlisted",
]

DEGREE_ORDER = [
    "Master's",
    "PhD",
]

OUTCOME_COLORS = {
    "Accepted": "#4C78A8",
    "Rejected": "#F58518",
    "Waitlisted": "#54A24B",
}


def normalize_status(value: object) -> str:
    """Convert raw status values into standard outcome categories."""
    text = str(value).strip().lower()

    if "accept" in text:
        return "Accepted"

    if "reject" in text:
        return "Rejected"

    if "wait" in text:
        return "Waitlisted"

    return "Other"


def normalize_degree(value: object) -> str:
    """Convert raw degree values into standard categories."""
    text = str(value).strip().lower()

    if "master" in text:
        return "Master's"

    if "phd" in text or "ph.d" in text or "doctor" in text:
        return "PhD"

    return "Other"


def normalize_student_type(value: object) -> str:
    """Convert student-type values into standard categories."""
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


def load_and_prepare_data(path: Path) -> pd.DataFrame:
    """Load and prepare the graduate admissions dataset."""
    if not path.exists():
        raise FileNotFoundError(
            f"Input dataset was not found: {path.resolve()}"
        )

    dataframe = pd.read_csv(path)

    dataframe["Outcome"] = dataframe[
        "applicant_status"
    ].apply(normalize_status)

    dataframe["Degree"] = dataframe[
        "degree"
    ].apply(normalize_degree)

    dataframe["Student Type"] = dataframe[
        "student_type"
    ].apply(normalize_student_type)

    dataframe["Start Term"] = dataframe[
        "start_term"
    ].apply(clean_start_term)

    dataframe["GPA"] = pd.to_numeric(
        dataframe["gpa"],
        errors="coerce",
    )

    dataframe.loc[
        ~dataframe["GPA"].between(0.0, 4.0),
        "GPA",
    ] = pd.NA

    return dataframe


def create_degree_figure(dataframe: pd.DataFrame):
    """Create an interactive outcome-by-degree grouped bar chart."""
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

    figure = px.bar(
        grouped_data,
        x="Degree",
        y="Percentage",
        color="Outcome",
        barmode="group",
        text_auto=".1f",
        category_orders={
            "Degree": DEGREE_ORDER,
            "Outcome": STATUS_ORDER,
        },
        color_discrete_map=OUTCOME_COLORS,
        title="Graduate Admission Outcomes by Degree Type",
        labels={
            "Degree": "Degree Type",
            "Percentage": "Share of Applications (%)",
            "Outcome": "Admission Outcome",
        },
        hover_data={
            "Applications": ":,",
            "Percentage": ":.1f",
        },
    )

    figure.update_traces(
        texttemplate="%{y:.1f}%",
        textposition="outside",
    )

    figure.update_layout(
        legend_title_text="Admission Outcome",
        margin={
            "l": 60,
            "r": 30,
            "t": 80,
            "b": 60,
        },
        height=500,
    )

    return figure


def create_gpa_figure(dataframe: pd.DataFrame):
    """Create an interactive GPA distribution chart."""
    plot_data = dataframe.loc[
        dataframe["Outcome"].isin(STATUS_ORDER)
        & dataframe["GPA"].notna()
    ].copy()

    figure = px.box(
        plot_data,
        x="Outcome",
        y="GPA",
        color="Outcome",
        category_orders={
            "Outcome": STATUS_ORDER,
        },
        color_discrete_map=OUTCOME_COLORS,
        points="outliers",
        title="Applicant GPA Distribution by Admission Outcome",
        labels={
            "Outcome": "Admission Outcome",
            "GPA": "GPA (4.0 scale)",
        },
        hover_data=[
            "Degree",
            "Student Type",
        ],
    )

    figure.update_layout(
        showlegend=False,
        yaxis_range=[2.0, 4.05],
        margin={
            "l": 60,
            "r": 30,
            "t": 80,
            "b": 60,
        },
        height=500,
    )

    return figure


def create_term_figure(dataframe: pd.DataFrame):
    """Create an interactive outcome-by-term chart."""
    plot_data = dataframe.loc[
        dataframe["Outcome"].isin(STATUS_ORDER)
        & dataframe["Start Term"].ne("Unknown")
    ].copy()

    common_terms = (
        plot_data["Start Term"]
        .value_counts()
        .head(10)
        .index
        .tolist()
    )

    plot_data = plot_data.loc[
        plot_data["Start Term"].isin(common_terms)
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

    figure = px.bar(
        grouped_data,
        x="Start Term",
        y="Applications",
        color="Outcome",
        facet_row="Student Type",
        barmode="stack",
        category_orders={
            "Start Term": common_terms,
            "Outcome": STATUS_ORDER,
            "Student Type": [
                "Domestic",
                "International",
                "Other",
            ],
        },
        color_discrete_map=OUTCOME_COLORS,
        title=(
            "Admission Outcomes by Start Term "
            "and Student Type"
        ),
        labels={
            "Applications": "Number of Applications",
            "Start Term": "Start Term",
            "Outcome": "Admission Outcome",
        },
        hover_data={
            "Applications": ":,",
            "Student Type": True,
        },
    )

    figure.update_layout(
        legend_title_text="Admission Outcome",
        hovermode="x unified",
        margin={
            "l": 70,
            "r": 30,
            "t": 90,
            "b": 100,
        },
        height=850,
    )

    figure.update_xaxes(
        tickangle=-35,
    )

    figure.for_each_annotation(
        lambda annotation: annotation.update(
            text=annotation.text.split("=")[-1]
        )
    )

    return figure


def build_dashboard(dataframe: pd.DataFrame) -> Dash:
    """Create the single-page Dash application."""
    application = Dash(__name__)

    degree_figure = create_degree_figure(dataframe)
    gpa_figure = create_gpa_figure(dataframe)
    term_figure = create_term_figure(dataframe)

    application.layout = html.Div(
        [
            html.Div(
                [
                    html.H1(
                        "What Factors Appear to Influence "
                        "Graduate Admissions Outcomes?",
                        style={
                            "marginBottom": "8px",
                        },
                    ),
                    html.P(
                        "Degree type is strongly associated with "
                        "reported outcomes, while GPA distributions "
                        "overlap substantially across accepted, "
                        "rejected, and waitlisted applicants.",
                        style={
                            "fontSize": "18px",
                            "maxWidth": "1050px",
                            "margin": "0 auto",
                        },
                    ),
                ],
                style={
                    "textAlign": "center",
                    "padding": "28px 24px",
                    "backgroundColor": "#F4F6F8",
                    "borderRadius": "12px",
                    "marginBottom": "24px",
                },
            ),
            html.Div(
                [
                    dcc.Graph(
                        figure=degree_figure,
                        config={
                            "displaylogo": False,
                        },
                    ),
                ],
                style={
                    "backgroundColor": "white",
                    "padding": "12px",
                    "borderRadius": "12px",
                    "boxShadow": (
                        "0 2px 8px rgba(0, 0, 0, 0.08)"
                    ),
                    "marginBottom": "24px",
                },
            ),
            html.Div(
                [
                    html.Div(
                        [
                            dcc.Graph(
                                figure=gpa_figure,
                                config={
                                    "displaylogo": False,
                                },
                            ),
                        ],
                        style={
                            "width": "49%",
                            "backgroundColor": "white",
                            "padding": "12px",
                            "borderRadius": "12px",
                            "boxShadow": (
                                "0 2px 8px "
                                "rgba(0, 0, 0, 0.08)"
                            ),
                        },
                    ),
                    html.Div(
                        [
                            html.H3(
                                "Key Findings",
                                style={
                                    "marginTop": "4px",
                                },
                            ),
                            html.P(
                                "Master's applications show a much "
                                "larger accepted share than PhD "
                                "applications."
                            ),
                            html.P(
                                "Median GPA is similar across all "
                                "three outcomes, so GPA alone does "
                                "not separate outcomes clearly."
                            ),
                            html.P(
                                "Application volume and outcome mix "
                                "vary across terms and student types."
                            ),
                        ],
                        style={
                            "width": "49%",
                            "backgroundColor": "#F9FAFB",
                            "padding": "28px",
                            "borderRadius": "12px",
                            "boxShadow": (
                                "0 2px 8px "
                                "rgba(0, 0, 0, 0.08)"
                            ),
                            "fontSize": "18px",
                            "lineHeight": "1.5",
                        },
                    ),
                ],
                style={
                    "display": "flex",
                    "gap": "2%",
                    "alignItems": "stretch",
                    "marginBottom": "24px",
                },
            ),
            html.Div(
                [
                    dcc.Graph(
                        figure=term_figure,
                        config={
                            "displaylogo": False,
                        },
                    ),
                ],
                style={
                    "backgroundColor": "white",
                    "padding": "12px",
                    "borderRadius": "12px",
                    "boxShadow": (
                        "0 2px 8px rgba(0, 0, 0, 0.08)"
                    ),
                },
            ),
        ],
        style={
            "maxWidth": "1450px",
            "margin": "0 auto",
            "padding": "24px",
            "backgroundColor": "#EEF1F5",
            "fontFamily": (
                "Arial, Helvetica, sans-serif"
            ),
        },
    )

    return application


def main() -> None:
    """Load the data and start the Dash server."""
    dataframe = load_and_prepare_data(DATA_PATH)
    application = build_dashboard(dataframe)

    application.run(
        debug=False,
        host="127.0.0.1",
        port=8050,
    )


if __name__ == "__main__":
    main()
