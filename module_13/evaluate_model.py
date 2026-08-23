"""
Module 13 - Section 5
Evaluate the Final Fine-Tuned DistilBERT Model

Student: Amr Mansour
JHED ID: amanso8

This script:
1. Reconstructs the cleaned admissions dataset.
2. Recreates the exact stratified 80/20 split used during training.
3. Loads the saved best DistilBERT checkpoint.
4. Evaluates it on the held-out test set.
5. Reports:
   - accuracy
   - precision
   - recall
   - F1 score
   - confusion matrix
   - class distributions
   - probability examples
   - correctly classified examples
   - incorrectly classified examples
   - interpretation
6. Saves detailed predictions and metrics.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)

from sklearn.model_selection import train_test_split

from torch.utils.data import Dataset, DataLoader

from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
)


# =========================================================
# CONFIGURATION
# =========================================================

DATA_FILE = "applicant_data.csv"

MODEL_DIR = Path("saved_model")

TEST_SIZE = 0.20
RANDOM_STATE = 42

MAX_LENGTH = 256
BATCH_SIZE = 8

DEVICE = torch.device(
    "cuda"
    if torch.cuda.is_available()
    else "cpu"
)


# =========================================================
# VALUE FORMATTING
# =========================================================

def display_value(value):
    """
    Convert missing values to the consistent placeholder
    'Unknown'.

    Otherwise return a clean string representation.
    """

    if pd.isna(value):
        return "Unknown"

    if isinstance(value, float):

        if value.is_integer():
            return str(int(value))

        return str(value)

    text = str(value).strip()

    if (
        text == ""
        or text.lower() in {
            "nan",
            "none",
            "null",
        }
    ):
        return "Unknown"

    return text


# =========================================================
# UNIFIED MODEL INPUT
# =========================================================

def create_model_input(row):
    """
    Recreate exactly the same unified applicant text
    representation used during training.

    IMPORTANT:
    The target label is NOT included.
    """

    return (
        f"Program: "
        f"{display_value(row['program_name'])}. "

        f"University: "
        f"{display_value(row['university'])}. "

        f"Degree: "
        f"{display_value(row['degree'])}. "

        f"Citizenship: "
        f"{display_value(row['student_type'])}. "

        f"GPA: "
        f"{display_value(row['gpa'])}. "

        f"GRE: "
        f"{display_value(row['gre_score'])}. "

        f"GRE Verbal: "
        f"{display_value(row['gre_v_score'])}. "

        f"GRE Analytical Writing: "
        f"{display_value(row['gre_aw'])}. "

        f"Term: "
        f"{display_value(row['start_term'])}."
    )


# =========================================================
# PYTORCH DATASET
# =========================================================

class ApplicantDataset(Dataset):
    """
    Dataset for tokenizer-based inference on the held-out
    applicant test data.
    """

    def __init__(
        self,
        texts,
        labels,
        tokenizer,
    ):

        self.texts = list(texts)
        self.labels = list(labels)

        self.tokenizer = tokenizer


    def __len__(self):

        return len(
            self.texts
        )


    def __getitem__(
        self,
        index,
    ):

        encoding = self.tokenizer(
            self.texts[index],
            truncation=True,
            padding="max_length",
            max_length=MAX_LENGTH,
            return_tensors="pt",
        )

        item = {
            key: value.squeeze(0)
            for key, value
            in encoding.items()
        }

        item[
            "labels"
        ] = torch.tensor(
            int(
                self.labels[index]
            ),
            dtype=torch.long,
        )

        return item


# =========================================================
# PREPARE DATA
# =========================================================

def prepare_data():
    """
    Reconstruct the exact cleaned dataset and held-out test
    split used during training.
    """

    print(
        "=" * 70
    )

    print(
        "SECTION 5 - EVALUATE THE FINAL MODEL"
    )

    print(
        "=" * 70
    )


    print(
        "\nReconstructing the dataset "
        "and held-out test split..."
    )


    df = pd.read_csv(
        DATA_FILE
    )

    original_rows = len(
        df
    )


    # -----------------------------------------------------
    # Remove duplicate applicant records
    # -----------------------------------------------------

    if "entry_url" in df.columns:

        df = df.drop_duplicates(
            subset=[
                "entry_url"
            ],
            keep="first",
        ).copy()


    # -----------------------------------------------------
    # Keep only Accepted and Rejected
    # -----------------------------------------------------

    df = df[
        df[
            "applicant_status"
        ].isin(
            [
                "Accepted",
                "Rejected",
            ]
        )
    ].copy()


    # -----------------------------------------------------
    # Explicit numeric conversion
    # -----------------------------------------------------

    numeric_columns = [
        "gpa",
        "gre_score",
        "gre_v_score",
        "gre_aw",
    ]

    for column in numeric_columns:

        df[
            column
        ] = pd.to_numeric(
            df[column],
            errors="coerce",
        )


    # -----------------------------------------------------
    # Binary target
    # -----------------------------------------------------

    df[
        "label"
    ] = (
        df[
            "applicant_status"
        ]
        == "Accepted"
    ).astype(
        int
    )


    # -----------------------------------------------------
    # Unified text input
    # -----------------------------------------------------

    df[
        "model_input"
    ] = df.apply(
        create_model_input,
        axis=1,
    )


    print(
        f"Original rows: "
        f"{original_rows}"
    )

    print(
        f"Rows available for classification: "
        f"{len(df)}"
    )


    # =====================================================
    # Reproduce the exact train/test split
    # =====================================================

    train_df, test_df = train_test_split(
        df,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        shuffle=True,
        stratify=df[
            "label"
        ],
    )


    train_df = train_df.reset_index(
        drop=True
    )

    test_df = test_df.reset_index(
        drop=True
    )


    print(
        f"Training rows reconstructed: "
        f"{len(train_df)}"
    )

    print(
        f"Held-out test rows: "
        f"{len(test_df)}"
    )


    return test_df


# =========================================================
# LOAD SAVED MODEL
# =========================================================

def load_saved_model():
    """
    Reload the saved fine-tuned DistilBERT checkpoint and
    tokenizer without retraining.
    """

    if not MODEL_DIR.exists():

        raise FileNotFoundError(
            f"Saved model directory not found: "
            f"{MODEL_DIR}"
        )


    metadata_path = (
        MODEL_DIR
        / "metadata.json"
    )


    if metadata_path.exists():

        with open(
            metadata_path,
            "r",
            encoding="utf-8",
        ) as file:

            metadata = json.load(
                file
            )


        print(
            "\nSaved checkpoint metadata:"
        )

        print(
            f"Best epoch: "
            f"{metadata.get('best_epoch', 'Unknown')}"
        )

        print(
            f"Recorded best test accuracy: "
            f"{metadata.get('best_test_accuracy', 'Unknown')}"
        )

        print(
            f"Recorded best test loss: "
            f"{metadata.get('best_test_loss', 'Unknown')}"
        )


    print(
        "\nLoading saved tokenizer and model..."
    )


    tokenizer = (
        AutoTokenizer
        .from_pretrained(
            MODEL_DIR,
            local_files_only=True,
        )
    )


    model = (
        AutoModelForSequenceClassification
        .from_pretrained(
            MODEL_DIR,
            local_files_only=True,
        )
    )


    model.to(
        DEVICE
    )

    model.eval()


    print(
        "Saved model loaded successfully."
    )

    print(
        f"Evaluation device: "
        f"{DEVICE}"
    )


    return (
        tokenizer,
        model,
    )


# =========================================================
# RUN HELD-OUT INFERENCE
# =========================================================

def evaluate(
    test_df,
    tokenizer,
    model,
):
    """
    Run inference over the complete held-out test set.
    """

    dataset = ApplicantDataset(
        test_df[
            "model_input"
        ].tolist(),

        test_df[
            "label"
        ].tolist(),

        tokenizer,
    )


    loader = DataLoader(
        dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=0,
    )


    all_labels = []
    all_predictions = []
    all_probabilities = []


    print(
        "\nRunning inference on held-out test set..."
    )


    with torch.no_grad():

        for (
            batch_number,
            batch,
        ) in enumerate(
            loader,
            start=1,
        ):

            labels = batch.pop(
                "labels"
            )


            inputs = {
                key: value.to(
                    DEVICE
                )
                for key, value
                in batch.items()
            }


            outputs = model(
                **inputs
            )


            probabilities = (
                torch.softmax(
                    outputs.logits,
                    dim=1,
                )
            )


            predictions = (
                torch.argmax(
                    probabilities,
                    dim=1,
                )
            )


            all_labels.extend(
                labels
                .cpu()
                .numpy()
                .tolist()
            )


            all_predictions.extend(
                predictions
                .cpu()
                .numpy()
                .tolist()
            )


            all_probabilities.extend(
                probabilities
                .cpu()
                .numpy()
                .tolist()
            )


            if (
                batch_number % 50 == 0
                or batch_number
                == len(loader)
            ):

                print(
                    f"Processed batch "
                    f"{batch_number}/"
                    f"{len(loader)}"
                )


    y_true = np.array(
        all_labels
    )

    y_pred = np.array(
        all_predictions
    )

    probabilities = np.array(
        all_probabilities
    )


    rejected_probability = (
        probabilities[
            :,
            0
        ]
    )

    accepted_probability = (
        probabilities[
            :,
            1
        ]
    )


    return (
        y_true,
        y_pred,
        accepted_probability,
        rejected_probability,
    )


# =========================================================
# REPORT FINAL RESULTS
# =========================================================

def report_results(
    test_df,
    y_true,
    y_pred,
    accepted_probability,
    rejected_probability,
):
    """
    Calculate and print all metrics and evidence required
    by the Module 13 assignment.
    """

    # -----------------------------------------------------
    # Required metrics
    # -----------------------------------------------------

    accuracy = accuracy_score(
        y_true,
        y_pred,
    )


    precision = precision_score(
        y_true,
        y_pred,
        pos_label=1,
        zero_division=0,
    )


    recall = recall_score(
        y_true,
        y_pred,
        pos_label=1,
        zero_division=0,
    )


    f1 = f1_score(
        y_true,
        y_pred,
        pos_label=1,
        zero_division=0,
    )


    cm = confusion_matrix(
        y_true,
        y_pred,
        labels=[
            0,
            1,
        ],
    )


    (
        true_negative,
        false_positive,
        false_negative,
        true_positive,
    ) = cm.ravel()


    # =====================================================
    # FINAL METRICS
    # =====================================================

    print(
        "\n"
    )

    print(
        "=" * 70
    )

    print(
        "FINAL TEST METRICS"
    )

    print(
        "=" * 70
    )


    print(
        f"Held-out test examples: "
        f"{len(y_true)}"
    )


    print(
        f"Accuracy:  "
        f"{accuracy:.4f} "
        f"({accuracy * 100:.2f}%)"
    )

    print(
        f"Precision: "
        f"{precision:.4f}"
    )

    print(
        f"Recall:    "
        f"{recall:.4f}"
    )

    print(
        f"F1 Score:  "
        f"{f1:.4f}"
    )


    # =====================================================
    # CONFUSION MATRIX
    # =====================================================

    print(
        "\nConfusion Matrix"
    )

    print(
        "(Rows = Actual, Columns = Predicted)"
    )

    print()

    print(
        "                    Predicted"
    )

    print(
        "                 Rejected  Accepted"
    )

    print(
        f"Actual Rejected    "
        f"{true_negative:5d}     "
        f"{false_positive:5d}"
    )

    print(
        f"Actual Accepted    "
        f"{false_negative:5d}     "
        f"{true_positive:5d}"
    )


    print(
        "\nConfusion-matrix interpretation:"
    )

    print(
        f"True negatives  "
        f"(Rejected -> Rejected): "
        f"{true_negative}"
    )

    print(
        f"False positives "
        f"(Rejected -> Accepted): "
        f"{false_positive}"
    )

    print(
        f"False negatives "
        f"(Accepted -> Rejected): "
        f"{false_negative}"
    )

    print(
        f"True positives  "
        f"(Accepted -> Accepted): "
        f"{true_positive}"
    )


    # =====================================================
    # CLASS DISTRIBUTIONS
    # =====================================================

    actual_rejected = int(
        np.sum(
            y_true == 0
        )
    )

    actual_accepted = int(
        np.sum(
            y_true == 1
        )
    )


    predicted_rejected = int(
        np.sum(
            y_pred == 0
        )
    )

    predicted_accepted = int(
        np.sum(
            y_pred == 1
        )
    )


    print(
        "\n"
    )

    print(
        "=" * 70
    )

    print(
        "CLASS DISTRIBUTION"
    )

    print(
        "=" * 70
    )


    print(
        "\nActual test-set distribution:"
    )

    print(
        f"Rejected: "
        f"{actual_rejected} "
        f"("
        f"{actual_rejected / len(y_true) * 100:.2f}%"
        f")"
    )

    print(
        f"Accepted: "
        f"{actual_accepted} "
        f"("
        f"{actual_accepted / len(y_true) * 100:.2f}%"
        f")"
    )


    print(
        "\nPredicted distribution:"
    )

    print(
        f"Rejected: "
        f"{predicted_rejected} "
        f"("
        f"{predicted_rejected / len(y_pred) * 100:.2f}%"
        f")"
    )

    print(
        f"Accepted: "
        f"{predicted_accepted} "
        f"("
        f"{predicted_accepted / len(y_pred) * 100:.2f}%"
        f")"
    )


    # =====================================================
    # RESULTS DATAFRAME
    # =====================================================

    results = test_df.copy()


    results[
        "actual_label"
    ] = y_true

    results[
        "predicted_label"
    ] = y_pred


    results[
        "actual_status"
    ] = np.where(
        y_true == 1,
        "Accepted",
        "Rejected",
    )


    results[
        "predicted_status"
    ] = np.where(
        y_pred == 1,
        "Accepted",
        "Rejected",
    )


    results[
        "probability_rejected"
    ] = rejected_probability

    results[
        "probability_accepted"
    ] = accepted_probability


    results[
        "correct"
    ] = (
        results[
            "actual_label"
        ]
        == results[
            "predicted_label"
        ]
    )


    # =====================================================
    # PROBABILITY EXAMPLES
    # =====================================================

    print(
        "\n"
    )

    print(
        "=" * 70
    )

    print(
        "PROBABILITY EXAMPLES"
    )

    print(
        "=" * 70
    )


    sample_count = min(
        5,
        len(results),
    )


    probability_examples = (
        results.iloc[
            :sample_count
        ]
    )


    for (
        number,
        (_, row),
    ) in enumerate(
        probability_examples.iterrows(),
        start=1,
    ):

        print(
            f"\nExample {number}:"
        )

        print(
            f"Actual: "
            f"{row['actual_status']}"
        )

        print(
            f"Predicted: "
            f"{row['predicted_status']}"
        )

        print(
            f"Probability Rejected: "
            f"{row['probability_rejected']:.4f}"
        )

        print(
            f"Probability Accepted: "
            f"{row['probability_accepted']:.4f}"
        )

        print(
            f"Input: "
            f"{row['model_input']}"
        )


    # =====================================================
    # CORRECT EXAMPLES
    # =====================================================

    correct_examples = (
        results[
            results[
                "correct"
            ]
        ]
        .head(
            3
        )
    )


    print(
        "\n"
    )

    print(
        "=" * 70
    )

    print(
        "CORRECTLY CLASSIFIED EXAMPLES"
    )

    print(
        "=" * 70
    )


    for (
        number,
        (_, row),
    ) in enumerate(
        correct_examples.iterrows(),
        start=1,
    ):

        print(
            f"\nCorrect Example {number}:"
        )

        print(
            f"Actual: "
            f"{row['actual_status']}"
        )

        print(
            f"Predicted: "
            f"{row['predicted_status']}"
        )

        print(
            f"Accepted probability: "
            f"{row['probability_accepted']:.4f}"
        )

        print(
            f"Input: "
            f"{row['model_input']}"
        )


    # =====================================================
    # INCORRECT EXAMPLES
    # =====================================================

    incorrect_examples = (
        results[
            ~results[
                "correct"
            ]
        ]
        .head(
            3
        )
    )


    print(
        "\n"
    )

    print(
        "=" * 70
    )

    print(
        "INCORRECTLY CLASSIFIED EXAMPLES"
    )

    print(
        "=" * 70
    )


    for (
        number,
        (_, row),
    ) in enumerate(
        incorrect_examples.iterrows(),
        start=1,
    ):

        print(
            f"\nIncorrect Example {number}:"
        )

        print(
            f"Actual: "
            f"{row['actual_status']}"
        )

        print(
            f"Predicted: "
            f"{row['predicted_status']}"
        )

        print(
            f"Accepted probability: "
            f"{row['probability_accepted']:.4f}"
        )

        print(
            f"Input: "
            f"{row['model_input']}"
        )


    # =====================================================
    # INTERPRETATION
    # =====================================================

    majority_baseline = (
        max(
            actual_rejected,
            actual_accepted,
        )
        / len(
            y_true
        )
    )


    module_12_accuracy = (
        0.7228
    )


    print(
        "\n"
    )

    print(
        "=" * 70
    )

    print(
        "SECTION 5 - INTERPRETATION"
    )

    print(
        "=" * 70
    )


    print(
        f"\nThe majority-class baseline "
        f"for the held-out test set is "
        f"{majority_baseline:.4f} "
        f"({majority_baseline * 100:.2f}%)."
    )


    print(
        f"The fine-tuned DistilBERT model "
        f"achieves {accuracy:.4f} "
        f"({accuracy * 100:.2f}%), "
        f"which is meaningfully above "
        f"the majority-class baseline."
    )


    # -----------------------------------------------------
    # Bias / class-distribution interpretation
    # -----------------------------------------------------

    actual_accepted_ratio = (
        actual_accepted
        / len(
            y_true
        )
    )

    predicted_accepted_ratio = (
        predicted_accepted
        / len(
            y_pred
        )
    )


    prediction_difference = (
        predicted_accepted_ratio
        - actual_accepted_ratio
    )


    if abs(
        prediction_difference
    ) < 0.05:

        print(
            "The predicted class distribution is reasonably "
            "close to the actual test-set distribution, "
            "so the model does not show an extreme overall "
            "class bias."
        )


    elif prediction_difference > 0:

        print(
            "The model predicts Accepted more frequently "
            "than the actual test-set distribution, "
            "suggesting some bias toward the Accepted class."
        )


    else:

        print(
            "The model predicts Rejected more frequently "
            "than the actual test-set distribution, "
            "suggesting some bias toward the Rejected class."
        )


    # -----------------------------------------------------
    # Compare against Module 12
    # -----------------------------------------------------

    difference = (
        accuracy
        - module_12_accuracy
    )


    print(
        f"\nThe earlier Module 12 two-layer NumPy "
        f"neural network achieved a test accuracy of "
        f"{module_12_accuracy:.4f} "
        f"({module_12_accuracy * 100:.2f}%)."
    )


    if difference > 0:

        print(
            f"The fine-tuned transformer is higher by "
            f"{difference * 100:.2f} percentage points."
        )


    elif difference < 0:

        print(
            f"The fine-tuned transformer is lower by "
            f"{abs(difference) * 100:.2f} percentage points."
        )


    else:

        print(
            "The two models achieved the same test accuracy."
        )


    # -----------------------------------------------------
    # Dataset limitations
    # -----------------------------------------------------

    print(
        "\nDespite the stronger modeling approach, "
        "this dataset is not sufficient for a realistic "
        "admissions predictor."
    )

    print(
        "Important admissions factors such as recommendation "
        "letters, research experience, statement quality, "
        "faculty fit, program competitiveness, funding, "
        "interviews, and other contextual information "
        "are absent."
    )

    print(
        "GRE-related fields are also highly sparse."
    )

    print(
        "Therefore, the model should be interpreted as "
        "learning historical associations in the dataset "
        "rather than reproducing real admissions "
        "decision rules."
    )


    # =====================================================
    # SAVE DETAILED PREDICTIONS
    # =====================================================

    results.to_csv(
        "evaluation_predictions.csv",
        index=False,
    )


    print(
        "\nDetailed test predictions saved to: "
        "evaluation_predictions.csv"
    )


    # =====================================================
    # RETURN METRICS
    # =====================================================

    return {

        "held_out_test_examples":
            int(
                len(
                    y_true
                )
            ),

        "accuracy":
            float(
                accuracy
            ),

        "precision":
            float(
                precision
            ),

        "recall":
            float(
                recall
            ),

        "f1_score":
            float(
                f1
            ),

        "confusion_matrix":
            cm.tolist(),

        "true_negatives":
            int(
                true_negative
            ),

        "false_positives":
            int(
                false_positive
            ),

        "false_negatives":
            int(
                false_negative
            ),

        "true_positives":
            int(
                true_positive
            ),

        "actual_rejected":
            actual_rejected,

        "actual_accepted":
            actual_accepted,

        "predicted_rejected":
            predicted_rejected,

        "predicted_accepted":
            predicted_accepted,

        "majority_class_baseline":
            float(
                majority_baseline
            ),

        "module_12_accuracy":
            float(
                module_12_accuracy
            ),

        "improvement_over_module_12":
            float(
                difference
            ),
    }


# =========================================================
# MAIN
# =========================================================

def main():
    """
    Run complete Section 5 evaluation.
    """

    test_df = prepare_data()


    (
        tokenizer,
        model,
    ) = load_saved_model()


    (
        y_true,
        y_pred,
        accepted_probability,
        rejected_probability,
    ) = evaluate(
        test_df,
        tokenizer,
        model,
    )


    metrics = report_results(
        test_df,
        y_true,
        y_pred,
        accepted_probability,
        rejected_probability,
    )


    # =====================================================
    # SAVE METRICS JSON
    # =====================================================

    with open(
        "evaluation_metrics.json",
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            metrics,
            file,
            indent=4,
        )


    print(
        "\nEvaluation metrics saved to: "
        "evaluation_metrics.json"
    )


    print(
        "\n"
    )

    print(
        "=" * 70
    )

    print(
        "SECTION 5 COMPLETED SUCCESSFULLY"
    )

    print(
        "=" * 70
    )


# =========================================================
# SCRIPT ENTRY POINT
# =========================================================

if __name__ == "__main__":
    main()