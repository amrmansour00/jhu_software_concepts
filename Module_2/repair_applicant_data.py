"""Repair malformed Module 2 GradCafe applicant records.

The original scraper produced a repeated two-row pattern:

1. A primary result row containing:
   - university
   - program
   - degree
   - decision/status information
   - unique /result/<id> URL

2. A following detail fragment containing:
   - start term
   - student type
   - GPA
   - GRE
   - GRE verbal
   - GRE analytical writing

This script merges those paired fragments into one applicant record,
reconstructs the program name and degree from the raw listing, validates
the repaired dataset, and saves the result without overwriting the
original source file.
"""

import json
import re
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

INPUT_FILE = BASE_DIR / "applicant_data.json"
OUTPUT_FILE = BASE_DIR / "applicant_data_repaired.json"


# =========================================================
# PATTERNS
# =========================================================

RESULT_URL_RE = re.compile(
    r"https://www\.thegradcafe\.com/result/\d+"
)

DATE_RE = re.compile(
    r"\b[A-Z][a-z]{2}\s+\d{1,2},\s+\d{4}\b"
)

DEGREE_BEFORE_DATE_RE = re.compile(
    r"\b("
    r"PhD|Ph\.D\.?|"
    r"Masters?|Master'?s?|"
    r"MFA|PsyD|JD|"
    r"MS|MA|"
    r"Other"
    r")\b"
    r"(?=\s+[A-Z][a-z]{2}\s+\d{1,2},\s+\d{4}\b)",
    re.IGNORECASE,
)


# =========================================================
# FILE OPERATIONS
# =========================================================

def load_records():
    """Load the original malformed applicant dataset."""

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input dataset not found: {INPUT_FILE}"
        )

    with INPUT_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def save_records(records):
    """Save repaired applicant records."""

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            records,
            file,
            indent=4,
            ensure_ascii=False,
        )


# =========================================================
# BASIC CLEANING
# =========================================================

def clean_text(value):
    """Normalize whitespace while preserving original wording."""

    if value is None:
        return None

    text = re.sub(
        r"\s+",
        " ",
        str(value),
    ).strip()

    return text or None


def is_primary_record(record):
    """Identify records containing a real GradCafe result URL."""

    entry_url = clean_text(
        record.get(
            "entry_url"
        )
    )

    if not entry_url:
        return False

    return bool(
        RESULT_URL_RE.fullmatch(
            entry_url
        )
    )


# =========================================================
# DEGREE HANDLING
# =========================================================

def normalize_degree(value):
    """Normalize supported degree categories."""

    if not value:
        return None

    text = str(
        value
    ).strip()

    lowered = text.casefold()

    if lowered in {
        "phd",
        "ph.d",
        "ph.d.",
    }:
        return "PhD"

    if lowered in {
        "master",
        "masters",
        "master's",
        "ms",
        "ma",
    }:
        return "Masters"

    if lowered == "mfa":
        return "MFA"

    if lowered == "psyd":
        return "PsyD"

    if lowered == "jd":
        return "JD"

    if lowered == "other":
        return "Other"

    return text


def extract_degree(primary):
    """Extract the degree token immediately before the record date."""

    raw = clean_text(
        primary.get(
            "raw_listing"
        )
    )

    if raw:
        match = DEGREE_BEFORE_DATE_RE.search(
            raw
        )

        if match:
            return normalize_degree(
                match.group(1)
            )

    return normalize_degree(
        primary.get(
            "degree"
        )
    )


# =========================================================
# PROGRAM EXTRACTION
# =========================================================

def extract_program_name(primary):
    """Extract the real program name from a primary raw listing.

    The original raw listing typically follows:

    University Program Degree Mon DD, YYYY Status ...

    Program names can themselves contain words such as:
    - Master
    - Masters
    - PhD
    - MA
    - JD

    Therefore, the parser identifies the actual degree by finding
    the degree token immediately before the record date.
    """

    raw = clean_text(
        primary.get(
            "raw_listing"
        )
    )

    university = clean_text(
        primary.get(
            "university"
        )
    )

    if not raw:
        return clean_text(
            primary.get(
                "program_name"
            )
        )

    remainder = raw

    # -----------------------------------------------------
    # Remove university prefix
    # -----------------------------------------------------

    if (
        university
        and remainder.casefold().startswith(
            university.casefold()
        )
    ):
        remainder = remainder[
            len(university):
        ].strip()

    # -----------------------------------------------------
    # Identify actual degree immediately before date
    # -----------------------------------------------------

    degree_match = DEGREE_BEFORE_DATE_RE.search(
        remainder
    )

    if degree_match:
        program = remainder[
            :degree_match.start()
        ].strip()

        return program or None

    # -----------------------------------------------------
    # Fallback: remove everything beginning with date
    # -----------------------------------------------------

    date_match = DATE_RE.search(
        remainder
    )

    if date_match:
        program = remainder[
            :date_match.start()
        ].strip()

        # Remove a trailing degree-like value if possible.
        trailing_degree = re.search(
            r"\s+("
            r"PhD|Ph\.D\.?|"
            r"Masters?|Master'?s?|"
            r"MFA|PsyD|JD|"
            r"MS|MA|Other"
            r")$",
            program,
            re.IGNORECASE,
        )

        if trailing_degree:
            program = program[
                :trailing_degree.start()
            ].strip()

        return program or None

    # -----------------------------------------------------
    # Last-resort cleanup
    # -----------------------------------------------------

    program = re.split(
        r"\b("
        r"Accepted|Rejected|"
        r"Wait listed|Waitlisted"
        r")\b",
        remainder,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0].strip()

    return program or None


# =========================================================
# DATE HANDLING
# =========================================================

def extract_date_added(primary):
    """Extract the Mon DD, YYYY date from the primary listing."""

    raw = clean_text(
        primary.get(
            "raw_listing"
        )
    )

    if raw:
        match = DATE_RE.search(
            raw
        )

        if match:
            return match.group(0)

    return clean_text(
        primary.get(
            "date_added"
        )
    )


# =========================================================
# MERGING
# =========================================================

def choose_detail_value(
    primary,
    detail,
    field,
):
    """Prefer the detail-row value when available."""

    if detail:
        detail_value = detail.get(
            field
        )

        if detail_value not in {
            None,
            "",
        }:
            return detail_value

    return primary.get(
        field
    )


def merge_pair(
    primary,
    detail,
):
    """Merge a primary result row with its following detail row."""

    return {
        "program_name":
            extract_program_name(
                primary
            ),

        "university":
            clean_text(
                primary.get(
                    "university"
                )
            ),

        "comments":
            clean_text(
                primary.get(
                    "comments"
                )
            ),

        "date_added":
            extract_date_added(
                primary
            ),

        "entry_url":
            clean_text(
                primary.get(
                    "entry_url"
                )
            ),

        "applicant_status":
            clean_text(
                primary.get(
                    "applicant_status"
                )
            ),

        "acceptance_date":
            clean_text(
                primary.get(
                    "acceptance_date"
                )
            ),

        "rejection_date":
            clean_text(
                primary.get(
                    "rejection_date"
                )
            ),

        "start_term":
            clean_text(
                choose_detail_value(
                    primary,
                    detail,
                    "start_term",
                )
            ),

        "student_type":
            clean_text(
                choose_detail_value(
                    primary,
                    detail,
                    "student_type",
                )
            ),

        "gre_score":
            choose_detail_value(
                primary,
                detail,
                "gre_score",
            ),

        "gre_v_score":
            choose_detail_value(
                primary,
                detail,
                "gre_v_score",
            ),

        "degree":
            extract_degree(
                primary
            ),

        "gpa":
            choose_detail_value(
                primary,
                detail,
                "gpa",
            ),

        "gre_aw":
            choose_detail_value(
                primary,
                detail,
                "gre_aw",
            ),

        "raw_listing":
            clean_text(
                primary.get(
                    "raw_listing"
                )
            ),

        "detail_raw_listing":
            (
                clean_text(
                    detail.get(
                        "raw_listing"
                    )
                )
                if detail
                else None
            ),

        "source_page":
            clean_text(
                primary.get(
                    "source_page"
                )
            ),
    }


# =========================================================
# DATASET REPAIR
# =========================================================

def repair_records(records):
    """Repair the full malformed dataset."""

    repaired = []

    index = 0

    skipped_fragments = 0
    unpaired_primary = 0

    while index < len(
        records
    ):
        current = records[
            index
        ]

        # -------------------------------------------------
        # Ignore orphan fragment rows
        # -------------------------------------------------

        if not is_primary_record(
            current
        ):
            skipped_fragments += 1
            index += 1
            continue

        detail = None

        # -------------------------------------------------
        # Pair primary row with immediate detail fragment
        # -------------------------------------------------

        if index + 1 < len(
            records
        ):
            candidate = records[
                index + 1
            ]

            same_page = (
                clean_text(
                    candidate.get(
                        "source_page"
                    )
                )
                ==
                clean_text(
                    current.get(
                        "source_page"
                    )
                )
            )

            if (
                not is_primary_record(
                    candidate
                )
                and same_page
            ):
                detail = candidate
                index += 2

            else:
                unpaired_primary += 1
                index += 1

        else:
            unpaired_primary += 1
            index += 1

        repaired.append(
            merge_pair(
                current,
                detail,
            )
        )

    return (
        repaired,
        skipped_fragments,
        unpaired_primary,
    )


# =========================================================
# VALIDATION
# =========================================================

def validation_statistics(
    records,
):
    """Calculate validation statistics."""

    total = len(
        records
    )

    missing_program = sum(
        not record.get(
            "program_name"
        )
        for record
        in records
    )

    missing_university = sum(
        not record.get(
            "university"
        )
        for record
        in records
    )

    missing_degree = sum(
        not record.get(
            "degree"
        )
        for record
        in records
    )

    missing_status = sum(
        not record.get(
            "applicant_status"
        )
        for record
        in records
    )

    missing_term = sum(
        not record.get(
            "start_term"
        )
        for record
        in records
    )

    unique_urls = {
        record.get(
            "entry_url"
        )
        for record
        in records
        if record.get(
            "entry_url"
        )
    }

    duplicate_urls = (
        total
        - len(
            unique_urls
        )
    )

    suspicious_programs = sum(
        bool(
            re.search(
                r"\b("
                r"Accepted|Rejected|"
                r"Wait listed|Waitlisted"
                r")\b",
                record.get(
                    "program_name"
                )
                or "",
                re.IGNORECASE,
            )
        )
        for record
        in records
    )

    return {
        "total":
            total,

        "missing_program":
            missing_program,

        "missing_university":
            missing_university,

        "missing_degree":
            missing_degree,

        "missing_status":
            missing_status,

        "missing_term":
            missing_term,

        "duplicate_urls":
            duplicate_urls,

        "suspicious_programs":
            suspicious_programs,
    }


def print_validation(
    records,
):
    """Print the validation summary."""

    stats = validation_statistics(
        records
    )

    print()
    print(
        "VALIDATION SUMMARY"
    )

    print(
        "=" * 70
    )

    print(
        f"Repaired applicant records: "
        f"{stats['total']:,}"
    )

    print(
        f"Missing program names: "
        f"{stats['missing_program']:,}"
    )

    print(
        f"Missing universities: "
        f"{stats['missing_university']:,}"
    )

    print(
        f"Missing degrees: "
        f"{stats['missing_degree']:,}"
    )

    print(
        f"Missing applicant status: "
        f"{stats['missing_status']:,}"
    )

    print(
        f"Missing start term: "
        f"{stats['missing_term']:,}"
    )

    print(
        f"Duplicate entry URLs: "
        f"{stats['duplicate_urls']:,}"
    )

    print(
        f"Suspicious program names containing "
        f"decision text: "
        f"{stats['suspicious_programs']:,}"
    )


# =========================================================
# SAMPLE OUTPUT
# =========================================================

def print_samples(
    records,
    count=10,
):
    """Print sample repaired records."""

    print()
    print(
        "REPAIRED SAMPLE"
    )

    print(
        "=" * 70
    )

    for (
        number,
        record,
    ) in enumerate(
        records[:count],
        start=1,
    ):
        print()
        print(
            f"Applicant {number}"
        )

        print(
            "University:",
            record.get(
                "university"
            ),
        )

        print(
            "Program:",
            record.get(
                "program_name"
            ),
        )

        print(
            "Degree:",
            record.get(
                "degree"
            ),
        )

        print(
            "Status:",
            record.get(
                "applicant_status"
            ),
        )

        print(
            "Date added:",
            record.get(
                "date_added"
            ),
        )

        print(
            "Term:",
            record.get(
                "start_term"
            ),
        )

        print(
            "Student type:",
            record.get(
                "student_type"
            ),
        )

        print(
            "GPA:",
            record.get(
                "gpa"
            ),
        )

        print(
            "GRE:",
            record.get(
                "gre_score"
            ),
        )

        print(
            "GRE Verbal:",
            record.get(
                "gre_v_score"
            ),
        )

        print(
            "GRE AW:",
            record.get(
                "gre_aw"
            ),
        )

        print(
            "Entry URL:",
            record.get(
                "entry_url"
            ),
        )


# =========================================================
# MAIN
# =========================================================

def main():
    """Run the complete repair workflow."""

    print(
        "Loading malformed "
        "applicant_data.json..."
    )

    records = load_records()

    print(
        f"Original rows: "
        f"{len(records):,}"
    )

    (
        repaired,
        skipped_fragments,
        unpaired_primary,
    ) = repair_records(
        records
    )

    print(
        f"Standalone fragments skipped: "
        f"{skipped_fragments:,}"
    )

    print(
        f"Primary records without paired detail: "
        f"{unpaired_primary:,}"
    )

    print_validation(
        repaired
    )

    print_samples(
        repaired,
        count=10,
    )

    save_records(
        repaired
    )

    print()
    print(
        f"Saved repaired dataset to: "
        f"{OUTPUT_FILE.name}"
    )


if __name__ == "__main__":
    main()