"""Test program-name extraction from the Module 8 dataset."""

import re

import pandas as pd


DATA_PATH = "../module_8/cleaned_applicant_data.csv"

MONTHS = (
    "Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec"
)


def extract_program(row: pd.Series) -> str:
    """Extract the program name from a raw Grad Café listing."""
    raw_listing = str(row["raw_listing"]).strip()
    university = str(row["university"]).strip()
    degree = re.escape(str(row["degree"]).strip())

    if raw_listing.startswith(university):
        remaining_text = raw_listing[len(university):].strip()
    else:
        remaining_text = raw_listing

    pattern = (
        rf"\s+{degree}\s+"
        rf"(?:{MONTHS})\s+\d{{1,2}},\s+\d{{4}}"
    )

    program_name = re.split(
        pattern,
        remaining_text,
        maxsplit=1,
    )[0]

    return program_name.strip()


dataframe = pd.read_csv(DATA_PATH)

dataframe = dataframe.loc[
    dataframe["degree"].notna()
    & dataframe["raw_listing"].notna()
].copy()

dataframe["extracted_program"] = dataframe.apply(
    extract_program,
    axis=1,
)

print(f"Valid rows: {len(dataframe):,}")
print(
    "Unique extracted programs:",
    f"{dataframe['extracted_program'].nunique():,}",
)

print(
    dataframe[
        [
            "university",
            "extracted_program",
            "degree",
        ]
    ]
    .head(30)
    .to_string(index=False)
)

computer_science_matches = dataframe[
    dataframe["extracted_program"].str.contains(
        "computer science",
        case=False,
        na=False,
    )
]

philosophy_matches = dataframe[
    dataframe["extracted_program"].str.contains(
        "philosophy",
        case=False,
        na=False,
    )
]

print(
    "\nComputer Science matches:",
    len(computer_science_matches),
)

print(
    "Philosophy matches:",
    len(philosophy_matches),
)