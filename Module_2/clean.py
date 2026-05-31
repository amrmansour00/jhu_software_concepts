import json
from pathlib import Path
from rapidfuzz import process, fuzz

BASE_DIR = Path(__file__).parent
LLM_DIR = BASE_DIR / "llm_hosting" / "llm_hosting-1"


def load_data(filename):
    path = BASE_DIR / filename

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_data(data, filename):
    path = BASE_DIR / filename

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def load_canonical_list(filename):
    path = LLM_DIR / filename

    with open(path, "r", encoding="utf-8") as file:
        return [
            line.strip()
            for line in file.readlines()
            if line.strip()
        ]


def standardize_value(value, canonical_values):
    if not value:
        return None

    match = process.extractOne(
        value,
        canonical_values,
        scorer=fuzz.WRatio
    )

    if match and match[1] >= 80:
        return match[0]

    return value


def clean_data(records):

    canonical_programs = load_canonical_list(
        "canon_programs.txt"
    )

    canonical_universities = load_canonical_list(
        "canon_universities.txt"
    )

    cleaned_records = []

    for record in records:

        original_program = record.get("program_name")
        original_university = record.get("university")

        record["standardized_program_name"] = (
            standardize_value(
                original_program,
                canonical_programs
            )
        )

        record["standardized_university"] = (
            standardize_value(
                original_university,
                canonical_universities
            )
        )

        cleaned_records.append(record)

    return cleaned_records


if __name__ == "__main__":

    print("Loading applicant_data.json...")

    records = load_data(
        "applicant_data.json"
    )

    print(f"Loaded {len(records)} records.")

    cleaned = clean_data(records)

    print("Saving llm_extend_applicant_data.json...")

    save_data(
        cleaned,
        "llm_extend_applicant_data.json"
    )

    print(f"Saved {len(cleaned)} cleaned records.")