"""
Module 13 - Section 6
Reload Saved DistilBERT Model and Run Inference

Student: Amr Mansour
JHED ID: amanso8

Demonstrates that the fine-tuned model can be reloaded from disk
and used for inference without retraining.
"""

import json
from pathlib import Path

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


MODEL_DIR = Path("saved_model")
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def load_model():
    """Reload the saved tokenizer, model, and metadata."""

    print("=" * 70)
    print("SECTION 6 - SAVE AND RELOAD THE TRAINED MODEL")
    print("=" * 70)

    required_files = [
        MODEL_DIR / "config.json",
        MODEL_DIR / "model.safetensors",
        MODEL_DIR / "tokenizer.json",
        MODEL_DIR / "tokenizer_config.json",
        MODEL_DIR / "metadata.json",
    ]

    print("\nChecking saved model artifacts:")

    for file_path in required_files:
        if not file_path.exists():
            raise FileNotFoundError(
                f"Required saved artifact not found: {file_path}"
            )

        print(f"- Found: {file_path}")

    with open(
        MODEL_DIR / "metadata.json",
        "r",
        encoding="utf-8",
    ) as file:
        metadata = json.load(file)

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_DIR,
        local_files_only=True,
    )

    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_DIR,
        local_files_only=True,
    )

    model.to(DEVICE)
    model.eval()

    print("\nModel reloaded successfully WITHOUT retraining.")
    print(f"Device: {DEVICE}")
    print(f"Source model: {metadata['source_model']}")
    print(f"Best epoch: {metadata['best_epoch']}")
    print(
        f"Saved best test accuracy: "
        f"{metadata['best_test_accuracy']:.4f}"
    )

    return tokenizer, model, metadata


def create_applicant_text(
    program,
    university,
    degree,
    citizenship,
    gpa,
    gre,
    gre_v,
    gre_aw,
    term,
):
    """
    Construct an inference input using exactly the same template
    used during training.
    """

    return (
        f"Program: {program}. "
        f"University: {university}. "
        f"Degree: {degree}. "
        f"Citizenship: {citizenship}. "
        f"GPA: {gpa}. "
        f"GRE: {gre}. "
        f"GRE Verbal: {gre_v}. "
        f"GRE Analytical Writing: {gre_aw}. "
        f"Term: {term}."
    )


def predict(text, tokenizer, model, metadata):
    """Run inference on one applicant."""

    max_length = metadata.get("max_length", 256)

    encoding = tokenizer(
        text,
        truncation=True,
        padding="max_length",
        max_length=max_length,
        return_tensors="pt",
    )

    encoding = {
        key: value.to(DEVICE)
        for key, value in encoding.items()
    }

    with torch.no_grad():
        outputs = model(**encoding)

        probabilities = torch.softmax(
            outputs.logits,
            dim=1,
        )[0]

    rejected_probability = probabilities[0].item()
    accepted_probability = probabilities[1].item()

    predicted_label = int(
        torch.argmax(probabilities).item()
    )

    predicted_status = (
        "Accepted"
        if predicted_label == 1
        else "Rejected"
    )

    return {
        "predicted_label": predicted_label,
        "predicted_status": predicted_status,
        "rejected_probability": rejected_probability,
        "accepted_probability": accepted_probability,
    }


def main():
    tokenizer, model, metadata = load_model()

    # Two artificial applicants for the required post-reload
    # inference demonstration.
    applicants = [
        create_applicant_text(
            program="Computer Science",
            university="Johns Hopkins University",
            degree="Masters",
            citizenship="American",
            gpa="3.90",
            gre="325",
            gre_v="160",
            gre_aw="4.5",
            term="Fall 2026",
        ),
        create_applicant_text(
            program="Mechanical Engineering",
            university="University of Toronto",
            degree="PhD",
            citizenship="International",
            gpa="3.20",
            gre="Unknown",
            gre_v="Unknown",
            gre_aw="Unknown",
            term="Fall 2026",
        ),
    ]

    print("\n")
    print("=" * 70)
    print("POST-RELOAD INFERENCE EXAMPLES")
    print("=" * 70)

    for index, applicant_text in enumerate(
        applicants,
        start=1,
    ):
        result = predict(
            applicant_text,
            tokenizer,
            model,
            metadata,
        )

        print(f"\nApplicant {index}")
        print("-" * 70)
        print(f"Input: {applicant_text}")
        print(
            f"Rejected probability: "
            f"{result['rejected_probability']:.4f}"
        )
        print(
            f"Accepted probability: "
            f"{result['accepted_probability']:.4f}"
        )
        print(
            f"Predicted label: "
            f"{result['predicted_label']}"
        )
        print(
            f"Predicted status: "
            f"{result['predicted_status']}"
        )

    print("\n")
    print("=" * 70)
    print("SECTION 6 VERIFICATION")
    print("=" * 70)

    print(
        "Saved model weights: verified"
    )
    print(
        "Saved tokenizer: verified"
    )
    print(
        "Saved preprocessing/label metadata: verified"
    )
    print(
        "Model reloaded without retraining: verified"
    )
    print(
        "Post-reload inference on two applicants: verified"
    )

    print("\nSECTION 6 COMPLETED SUCCESSFULLY")


if __name__ == "__main__":
    main()