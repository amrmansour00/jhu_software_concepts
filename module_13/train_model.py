import os
import json
import random
import time

import numpy as np
import pandas as pd
import torch

from torch.utils.data import Dataset, DataLoader
from torch.optim import AdamW

from sklearn.model_selection import train_test_split

from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification
)


# =========================================================
# MODULE 13 - SCALE & LANGUAGE MODEL DEPLOYMENT
# SECTIONS 1-4
# =========================================================


# =========================================================
# GLOBAL CONFIGURATION
# =========================================================

DATA_PATH = "applicant_data.csv"

SAVE_DIR = "saved_model"
TRAINING_LOG_PATH = "training.log"

RANDOM_SEED = 42

TEST_SIZE = 0.20
SHUFFLE = True


# ---------------------------------------------------------
# SECTION 4 MODEL CONFIGURATION
# ---------------------------------------------------------

MODEL_NAME = "distilbert-base-uncased"
TOKENIZER_NAME = "distilbert-base-uncased"

MAX_LENGTH = 256
BATCH_SIZE = 8
NUM_EPOCHS = 2
LEARNING_RATE = 2e-5


DEVICE = torch.device(
    "cuda"
    if torch.cuda.is_available()
    else "cpu"
)


# =========================================================
# REPRODUCIBILITY
# =========================================================

random.seed(
    RANDOM_SEED
)

np.random.seed(
    RANDOM_SEED
)

torch.manual_seed(
    RANDOM_SEED
)

if torch.cuda.is_available():

    torch.cuda.manual_seed_all(
        RANDOM_SEED
    )


# =========================================================
# SECTION 1
# LOAD AND PREPARE THE APPLICANT DATASET
# =========================================================


# ---------------------------------------------------------
# 1. Load cleaned dataset
# ---------------------------------------------------------

df = pd.read_csv(
    DATA_PATH
)

original_rows = len(
    df
)


# ---------------------------------------------------------
# 2. Remove duplicate applicant records
# ---------------------------------------------------------

rows_before_duplicates = len(
    df
)

df = df.drop_duplicates(
    subset=["entry_url"],
    keep="first"
).copy()

duplicates_removed = (
    rows_before_duplicates
    - len(df)
)


# ---------------------------------------------------------
# 3. Keep only Accepted / Rejected
# ---------------------------------------------------------

df = df[
    df["applicant_status"].isin(
        [
            "Accepted",
            "Rejected"
        ]
    )
].copy()


# ---------------------------------------------------------
# 4. Convert numeric fields
# ---------------------------------------------------------

NUMERIC_FIELDS = [
    "gpa",
    "gre_score",
    "gre_v_score",
    "gre_aw"
]

for column in NUMERIC_FIELDS:

    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )


# ---------------------------------------------------------
# 5. Create binary target
# ---------------------------------------------------------

df["label"] = df[
    "applicant_status"
].map({
    "Accepted": 1,
    "Rejected": 0
})


# ---------------------------------------------------------
# 6. Define fields used for modeling
# ---------------------------------------------------------

TEXT_FIELDS = [
    "program_name",
    "university"
]

NON_TEXT_FIELDS = [
    "degree",
    "student_type",
    "gpa",
    "gre_score",
    "gre_v_score",
    "gre_aw",
    "start_term"
]

MODEL_FIELDS = (
    TEXT_FIELDS
    + NON_TEXT_FIELDS
)


# ---------------------------------------------------------
# 7. Keep usable applicant rows
# ---------------------------------------------------------

usable_mask = (
    df["program_name"].notna()
    | df["university"].notna()
)

df = df[
    usable_mask
].copy()


# ---------------------------------------------------------
# 8. Required counts
# ---------------------------------------------------------

accepted_count = int(
    (
        df["label"]
        == 1
    ).sum()
)

rejected_count = int(
    (
        df["label"]
        == 0
    ).sum()
)


# ---------------------------------------------------------
# 9. Section 1 output
# ---------------------------------------------------------

print(
    "=" * 70
)

print(
    "SECTION 1 - LOAD AND PREPARE THE APPLICANT DATASET"
)

print(
    "=" * 70
)


print(
    f"Number of rows in original dataset: "
    f"{original_rows}"
)

print(
    f"Duplicate rows removed by entry URL: "
    f"{duplicates_removed}"
)

print(
    f"Number of rows remaining after filtering: "
    f"{len(df)}"
)

print(
    f"Number of Accepted rows: "
    f"{accepted_count}"
)

print(
    f"Number of Rejected rows: "
    f"{rejected_count}"
)


print(
    "\nText-based fields used:"
)

for field in TEXT_FIELDS:

    print(
        f"- {field}"
    )


print(
    "\nNon-text fields used:"
)

for field in NON_TEXT_FIELDS:

    print(
        f"- {field}"
    )


print(
    "\nFull list of fields used for modeling:"
)

for field in MODEL_FIELDS:

    print(
        f"- {field}"
    )


print(
    "\nPreview of cleaned DataFrame:"
)

preview_columns = [
    "program_name",
    "university",
    "degree",
    "student_type",
    "gpa",
    "gre_score",
    "gre_v_score",
    "gre_aw",
    "start_term",
    "applicant_status",
    "label"
]

print(
    df[
        preview_columns
    ]
    .head()
    .to_string(
        index=False
    )
)


# =========================================================
# SECTION 2
# CONVERT EACH APPLICANT INTO A UNIFIED MODEL INPUT
# =========================================================


# ---------------------------------------------------------
# 10. Missing-value formatting
# ---------------------------------------------------------

def format_value(value):
    """
    Convert missing or blank values into a consistent
    human-readable placeholder.
    """

    if pd.isna(
        value
    ):

        return "Unknown"


    value = str(
        value
    ).strip()


    if (
        value == ""
        or value.lower()
        in {
            "nan",
            "none"
        }
    ):

        return "Unknown"


    return value


# ---------------------------------------------------------
# 11. Create unified applicant input
# ---------------------------------------------------------

def create_unified_input(row):
    """
    Convert a single applicant record into one consistent
    text representation containing both text and
    structured information.

    The true target is deliberately excluded to prevent
    target leakage.
    """

    return (
        f"Program: "
        f"{format_value(row['program_name'])}. "

        f"University: "
        f"{format_value(row['university'])}. "

        f"Degree: "
        f"{format_value(row['degree'])}. "

        f"Citizenship: "
        f"{format_value(row['student_type'])}. "

        f"GPA: "
        f"{format_value(row['gpa'])}. "

        f"GRE: "
        f"{format_value(row['gre_score'])}. "

        f"GRE Verbal: "
        f"{format_value(row['gre_v_score'])}. "

        f"GRE Analytical Writing: "
        f"{format_value(row['gre_aw'])}. "

        f"Term: "
        f"{format_value(row['start_term'])}."
    )


df[
    "model_input"
] = df.apply(
    create_unified_input,
    axis=1
)


MODEL_INPUT_TEMPLATE = (
    "Program: <program_name>. "
    "University: <university>. "
    "Degree: <degree>. "
    "Citizenship: <student_type>. "
    "GPA: <gpa>. "
    "GRE: <gre_score>. "
    "GRE Verbal: <gre_v_score>. "
    "GRE Analytical Writing: <gre_aw>. "
    "Term: <start_term>."
)


# ---------------------------------------------------------
# 12. Section 2 output
# ---------------------------------------------------------

print(
    "\n"
)

print(
    "=" * 70
)

print(
    "SECTION 2 - CONVERT EACH APPLICANT "
    "INTO A UNIFIED MODEL INPUT"
)

print(
    "=" * 70
)


print(
    "\nExact template used:"
)

print(
    MODEL_INPUT_TEMPLATE
)


print(
    "\nMissing fields are represented "
    "consistently as: Unknown"
)

print(
    "The target label and applicant_status "
    "are NOT included in the model input."
)

print(
    "\nThe unified input contains both text "
    "and structured/non-text information."
)


print(
    "\nThree sample model inputs:"
)

for index, text in enumerate(
    df[
        "model_input"
    ].head(
        3
    ),
    start=1
):

    print(
        f"\nSample {index}:"
    )

    print(
        text
    )


# ---------------------------------------------------------
# 13. Section 2 validation
# ---------------------------------------------------------

assert len(
    TEXT_FIELDS
) >= 2

assert len(
    NON_TEXT_FIELDS
) >= 3

assert set(
    df[
        "label"
    ].unique()
).issubset({
    0,
    1
})


# =========================================================
# SECTION 3
# SPLIT DATA INTO TRAINING AND TEST SETS
# =========================================================


# ---------------------------------------------------------
# 14. Required stratified 80/20 split
# ---------------------------------------------------------

train_df, test_df = train_test_split(
    df,
    test_size=TEST_SIZE,
    random_state=RANDOM_SEED,
    shuffle=SHUFFLE,
    stratify=df[
        "label"
    ]
)


train_df = train_df.reset_index(
    drop=True
)

test_df = test_df.reset_index(
    drop=True
)


# ---------------------------------------------------------
# 15. Class balance
# ---------------------------------------------------------

train_class_counts = (
    train_df[
        "applicant_status"
    ]
    .value_counts()
)

test_class_counts = (
    test_df[
        "applicant_status"
    ]
    .value_counts()
)


train_class_percentages = (
    train_df[
        "applicant_status"
    ]
    .value_counts(
        normalize=True
    )
    * 100
)

test_class_percentages = (
    test_df[
        "applicant_status"
    ]
    .value_counts(
        normalize=True
    )
    * 100
)


# ---------------------------------------------------------
# 16. Section 3 output
# ---------------------------------------------------------

print(
    "\n"
)

print(
    "=" * 70
)

print(
    "SECTION 3 - SPLIT THE DATA INTO "
    "TRAINING AND TESTING SETS"
)

print(
    "=" * 70
)


print(
    f"Training set size: "
    f"{len(train_df)}"
)

print(
    f"Test set size: "
    f"{len(test_df)}"
)


print(
    "\nTraining-set class balance:"
)

for class_name in [
    "Accepted",
    "Rejected"
]:

    count = int(
        train_class_counts.get(
            class_name,
            0
        )
    )

    percentage = float(
        train_class_percentages.get(
            class_name,
            0
        )
    )

    print(
        f"{class_name}: "
        f"{count} "
        f"({percentage:.2f}%)"
    )


print(
    "\nTest-set class balance:"
)

for class_name in [
    "Accepted",
    "Rejected"
]:

    count = int(
        test_class_counts.get(
            class_name,
            0
        )
    )

    percentage = float(
        test_class_percentages.get(
            class_name,
            0
        )
    )

    print(
        f"{class_name}: "
        f"{count} "
        f"({percentage:.2f}%)"
    )


print(
    "\nWhy train/test separation matters:"
)

print(
    "The model is trained only on the training set and "
    "evaluated on applicants held out from training. "
    "This provides a more realistic estimate of how the "
    "classifier behaves on unseen applicants."
)

print(
    "This separation is especially important before "
    "deployment on a public-facing webpage because real "
    "users will submit applicant information that the "
    "model has never seen before."
)

print(
    "Stratification preserves approximately the same "
    "Accepted/Rejected class balance in both sets."
)


# =========================================================
# SECTION 4
# FINE-TUNE A PRETRAINED PYTORCH LANGUAGE MODEL
# =========================================================


# ---------------------------------------------------------
# 17. Model configuration output
# ---------------------------------------------------------

print(
    "\n"
)

print(
    "=" * 70
)

print(
    "SECTION 4 - FINE-TUNE A PRETRAINED "
    "PYTORCH LANGUAGE MODEL"
)

print(
    "=" * 70
)


print(
    "\nChosen model:"
)

print(
    MODEL_NAME
)


print(
    "\nWhy this model was selected:"
)

print(
    "DistilBERT is a pretrained Hugging Face transformer "
    "that supports sequence classification while being "
    "smaller and faster than full BERT. The assignment "
    "specifically recommends a lightweight model such as "
    "DistilBERT for ordinary hardware."
)


print(
    "\nTokenizer:"
)

print(
    TOKENIZER_NAME
)


print(
    "\nTokenizer explanation:"
)

print(
    "The DistilBERT tokenizer matches the vocabulary and "
    "tokenization scheme used by the pretrained model. "
    "Unified applicant inputs use truncation and "
    "fixed-length padding to a maximum of 256 tokens."
)


print(
    "\nTraining configuration:"
)

print(
    f"Model name: "
    f"{MODEL_NAME}"
)

print(
    f"Tokenizer name: "
    f"{TOKENIZER_NAME}"
)

print(
    f"Maximum sequence length: "
    f"{MAX_LENGTH}"
)

print(
    f"Batch size: "
    f"{BATCH_SIZE}"
)

print(
    f"Number of epochs: "
    f"{NUM_EPOCHS}"
)

print(
    f"Learning rate: "
    f"{LEARNING_RATE}"
)

print(
    "Optimizer: AdamW"
)

print(
    f"Device: "
    f"{DEVICE}"
)


# ---------------------------------------------------------
# 18. Load tokenizer
# ---------------------------------------------------------

print(
    "\nLoading tokenizer..."
)

tokenizer = AutoTokenizer.from_pretrained(
    TOKENIZER_NAME
)


# =========================================================
# PYTORCH DATASET
# =========================================================

class ApplicantDataset(
    Dataset
):

    def __init__(
        self,
        dataframe,
        tokenizer,
        max_length
    ):

        self.texts = (
            dataframe[
                "model_input"
            ]
            .tolist()
        )

        self.labels = (
            dataframe[
                "label"
            ]
            .astype(
                int
            )
            .tolist()
        )

        self.tokenizer = tokenizer

        self.max_length = (
            max_length
        )


    def __len__(
        self
    ):

        return len(
            self.texts
        )


    def __getitem__(
        self,
        index
    ):

        text = self.texts[
            index
        ]

        label = self.labels[
            index
        ]


        encoding = self.tokenizer(
            text,
            add_special_tokens=True,
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_attention_mask=True,
            return_tensors="pt"
        )


        return {

            "input_ids":
                encoding[
                    "input_ids"
                ].squeeze(
                    0
                ),

            "attention_mask":
                encoding[
                    "attention_mask"
                ].squeeze(
                    0
                ),

            "labels":
                torch.tensor(
                    label,
                    dtype=torch.long
                )
        }


# ---------------------------------------------------------
# 19. Create datasets
# ---------------------------------------------------------

train_dataset = ApplicantDataset(
    train_df,
    tokenizer,
    MAX_LENGTH
)

test_dataset = ApplicantDataset(
    test_df,
    tokenizer,
    MAX_LENGTH
)


# ---------------------------------------------------------
# 20. Create DataLoaders
# ---------------------------------------------------------

train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=True,
    num_workers=0
)

test_loader = DataLoader(
    test_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=0
)


print(
    "\nDataset construction complete."
)

print(
    f"Training batches: "
    f"{len(train_loader)}"
)

print(
    f"Test batches: "
    f"{len(test_loader)}"
)


# ---------------------------------------------------------
# 21. Load pretrained model
# ---------------------------------------------------------

print(
    "\nLoading pretrained model..."
)

model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME,
    num_labels=2,

    id2label={
        0: "Rejected",
        1: "Accepted"
    },

    label2id={
        "Rejected": 0,
        "Accepted": 1
    }
)


model = model.to(
    DEVICE
)


# ---------------------------------------------------------
# 22. Optimizer
# ---------------------------------------------------------

optimizer = AdamW(
    model.parameters(),
    lr=LEARNING_RATE
)


# =========================================================
# EVALUATION HELPER
# =========================================================

def evaluate_model(
    model,
    data_loader,
    device
):

    model.eval()

    total_loss = 0.0

    total_correct = 0

    total_examples = 0


    with torch.no_grad():

        for batch in data_loader:

            input_ids = batch[
                "input_ids"
            ].to(
                device
            )

            attention_mask = batch[
                "attention_mask"
            ].to(
                device
            )

            labels = batch[
                "labels"
            ].to(
                device
            )


            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels
            )


            loss = outputs.loss

            logits = outputs.logits


            predictions = torch.argmax(
                logits,
                dim=1
            )


            current_batch_size = (
                labels.size(
                    0
                )
            )


            total_loss += (
                loss.item()
                * current_batch_size
            )

            total_correct += (
                predictions
                == labels
            ).sum().item()

            total_examples += (
                current_batch_size
            )


    average_loss = (
        total_loss
        / total_examples
    )

    accuracy = (
        total_correct
        / total_examples
    )


    return (
        average_loss,
        accuracy
    )


# =========================================================
# SAVE CHECKPOINT HELPER
# =========================================================

def save_checkpoint(
    model,
    tokenizer,
    epoch,
    test_loss,
    test_accuracy
):

    os.makedirs(
        SAVE_DIR,
        exist_ok=True
    )


    model.save_pretrained(
        SAVE_DIR
    )

    tokenizer.save_pretrained(
        SAVE_DIR
    )


    metadata = {

        "source_model":
            MODEL_NAME,

        "tokenizer":
            TOKENIZER_NAME,

        "max_length":
            MAX_LENGTH,

        "batch_size":
            BATCH_SIZE,

        "epochs_configured":
            NUM_EPOCHS,

        "learning_rate":
            LEARNING_RATE,

        "optimizer":
            "AdamW",

        "device":
            str(
                DEVICE
            ),

        "random_seed":
            RANDOM_SEED,

        "best_epoch":
            epoch,

        "best_test_loss":
            float(
                test_loss
            ),

        "best_test_accuracy":
            float(
                test_accuracy
            ),

        "label_mapping": {
            "0": "Rejected",
            "1": "Accepted"
        },

        "text_fields":
            TEXT_FIELDS,

        "non_text_fields":
            NON_TEXT_FIELDS,

        "model_input_template":
            MODEL_INPUT_TEMPLATE
    }


    metadata_path = os.path.join(
        SAVE_DIR,
        "metadata.json"
    )


    with open(
        metadata_path,
        "w",
        encoding="utf-8"
    ) as metadata_file:

        json.dump(
            metadata,
            metadata_file,
            indent=4
        )


# =========================================================
# TRAINING LOOP
# =========================================================

training_history = []

training_log_lines = []

best_test_accuracy = -1.0

best_test_loss = float(
    "inf"
)

best_epoch = 0


overall_start_time = (
    time.time()
)


print(
    "\nStarting DistilBERT fine-tuning..."
)

print(
    "NOTE: This machine is using CPU, so training may "
    "take a significant amount of time."
)


for epoch in range(
    1,
    NUM_EPOCHS + 1
):

    epoch_start_time = (
        time.time()
    )

    model.train()

    running_loss = 0.0

    examples_seen = 0


    print(
        "\n"
        + "-" * 70
    )

    print(
        f"Epoch {epoch}/{NUM_EPOCHS}"
    )

    print(
        "-" * 70
    )


    for batch_number, batch in enumerate(
        train_loader,
        start=1
    ):

        input_ids = batch[
            "input_ids"
        ].to(
            DEVICE
        )

        attention_mask = batch[
            "attention_mask"
        ].to(
            DEVICE
        )

        labels = batch[
            "labels"
        ].to(
            DEVICE
        )


        optimizer.zero_grad()


        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=labels
        )


        loss = outputs.loss


        loss.backward()


        optimizer.step()


        current_batch_size = (
            labels.size(
                0
            )
        )


        running_loss += (
            loss.item()
            * current_batch_size
        )

        examples_seen += (
            current_batch_size
        )


        if (
            batch_number % 100
            == 0

            or batch_number
            == len(
                train_loader
            )
        ):

            average_train_loss = (
                running_loss
                / examples_seen
            )


            log_line = (

                f"Epoch "
                f"{epoch}/{NUM_EPOCHS} | "

                f"Batch "
                f"{batch_number}/"
                f"{len(train_loader)} | "

                f"Average Train Loss: "
                f"{average_train_loss:.4f}"
            )


            print(
                log_line
            )


            training_log_lines.append(
                log_line
            )


    epoch_train_loss = (
        running_loss
        / examples_seen
    )


    # -----------------------------------------------------
    # Test evaluation after epoch
    # -----------------------------------------------------

    test_loss, test_accuracy = evaluate_model(
        model,
        test_loader,
        DEVICE
    )


    epoch_duration = (
        time.time()
        - epoch_start_time
    )


    epoch_result = {

        "epoch":
            epoch,

        "train_loss":
            epoch_train_loss,

        "test_loss":
            test_loss,

        "test_accuracy":
            test_accuracy,

        "duration_seconds":
            epoch_duration
    }


    training_history.append(
        epoch_result
    )


    print(
        f"\nEpoch {epoch} summary:"
    )

    print(
        f"Training loss: "
        f"{epoch_train_loss:.4f}"
    )

    print(
        f"Test loss: "
        f"{test_loss:.4f}"
    )

    print(
        f"Test accuracy: "
        f"{test_accuracy:.4f} "
        f"({test_accuracy * 100:.2f}%)"
    )

    print(
        f"Epoch duration: "
        f"{epoch_duration / 60:.2f} minutes"
    )


    summary_line = (

        f"Epoch {epoch} | "

        f"Train Loss: "
        f"{epoch_train_loss:.4f} | "

        f"Test Loss: "
        f"{test_loss:.4f} | "

        f"Test Accuracy: "
        f"{test_accuracy:.4f}"
    )


    training_log_lines.append(
        summary_line
    )


    # =====================================================
    # SAVE BEST MODEL IMMEDIATELY
    # =====================================================
    #
    # Primary selection criterion:
    # highest held-out test accuracy.
    #
    # If accuracy ties, choose lower test loss.

    is_better_model = (

        test_accuracy
        > best_test_accuracy

        or (

            np.isclose(
                test_accuracy,
                best_test_accuracy
            )

            and test_loss
            < best_test_loss
        )
    )


    if is_better_model:

        best_test_accuracy = (
            test_accuracy
        )

        best_test_loss = (
            test_loss
        )

        best_epoch = (
            epoch
        )


        print(
            "\nNew best model found."
        )

        print(
            f"Saving checkpoint from "
            f"epoch {epoch}..."
        )


        save_checkpoint(
            model=model,
            tokenizer=tokenizer,
            epoch=epoch,
            test_loss=test_loss,
            test_accuracy=test_accuracy
        )


        print(
            f"Best checkpoint saved to: "
            f"{SAVE_DIR}"
        )


# =========================================================
# FINAL TRAINING SUMMARY
# =========================================================

total_training_time = (
    time.time()
    - overall_start_time
)


print(
    "\n"
)

print(
    "=" * 70
)

print(
    "SECTION 4 - TRAINING COMPLETE"
)

print(
    "=" * 70
)


print(
    f"Model: "
    f"{MODEL_NAME}"
)

print(
    f"Tokenizer: "
    f"{TOKENIZER_NAME}"
)

print(
    f"Maximum sequence length: "
    f"{MAX_LENGTH}"
)

print(
    f"Batch size: "
    f"{BATCH_SIZE}"
)

print(
    f"Epochs completed: "
    f"{NUM_EPOCHS}"
)

print(
    f"Learning rate: "
    f"{LEARNING_RATE}"
)

print(
    "Optimizer: AdamW"
)

print(
    f"Device used: "
    f"{DEVICE}"
)

print(
    f"Total training time: "
    f"{total_training_time / 60:.2f} minutes"
)


print(
    "\nTraining history:"
)

for result in training_history:

    print(

        f"Epoch "
        f"{result['epoch']} | "

        f"Train Loss: "
        f"{result['train_loss']:.4f} | "

        f"Test Loss: "
        f"{result['test_loss']:.4f} | "

        f"Test Accuracy: "
        f"{result['test_accuracy']:.4f}"
    )


print(
    "\nBest saved checkpoint:"
)

print(
    f"Best epoch: "
    f"{best_epoch}"
)

print(
    f"Best test accuracy: "
    f"{best_test_accuracy:.4f} "
    f"({best_test_accuracy * 100:.2f}%)"
)

print(
    f"Best test loss: "
    f"{best_test_loss:.4f}"
)

print(
    f"Saved model directory: "
    f"{SAVE_DIR}"
)


# =========================================================
# SAVE TRAINING LOG
# =========================================================

with open(
    TRAINING_LOG_PATH,
    "w",
    encoding="utf-8"
) as log_file:

    log_file.write(
        "MODULE 13 DISTILBERT TRAINING LOG\n"
    )

    log_file.write(
        "=" * 70
        + "\n\n"
    )


    log_file.write(
        f"Model: "
        f"{MODEL_NAME}\n"
    )

    log_file.write(
        f"Tokenizer: "
        f"{TOKENIZER_NAME}\n"
    )

    log_file.write(
        f"Maximum sequence length: "
        f"{MAX_LENGTH}\n"
    )

    log_file.write(
        f"Batch size: "
        f"{BATCH_SIZE}\n"
    )

    log_file.write(
        f"Epochs: "
        f"{NUM_EPOCHS}\n"
    )

    log_file.write(
        f"Learning rate: "
        f"{LEARNING_RATE}\n"
    )

    log_file.write(
        "Optimizer: AdamW\n"
    )

    log_file.write(
        f"Device: "
        f"{DEVICE}\n"
    )

    log_file.write(
        f"Random seed: "
        f"{RANDOM_SEED}\n\n"
    )


    log_file.write(
        f"Training set size: "
        f"{len(train_df)}\n"
    )

    log_file.write(
        f"Test set size: "
        f"{len(test_df)}\n\n"
    )


    log_file.write(
        "REPRESENTATIVE TRAINING OUTPUT\n"
    )

    log_file.write(
        "-" * 70
        + "\n"
    )


    for line in training_log_lines:

        log_file.write(
            line
            + "\n"
        )


    log_file.write(
        "\nBEST CHECKPOINT\n"
    )

    log_file.write(
        "-" * 70
        + "\n"
    )

    log_file.write(
        f"Best epoch: "
        f"{best_epoch}\n"
    )

    log_file.write(
        f"Best test accuracy: "
        f"{best_test_accuracy:.4f}\n"
    )

    log_file.write(
        f"Best test loss: "
        f"{best_test_loss:.4f}\n"
    )

    log_file.write(
        f"Total training time: "
        f"{total_training_time / 60:.2f} minutes\n"
    )


print(
    f"\nTraining log saved to: "
    f"{TRAINING_LOG_PATH}"
)


# =========================================================
# VERIFY SAVED MODEL FILES EXIST
# =========================================================

required_saved_files = [
    os.path.join(
        SAVE_DIR,
        "config.json"
    ),

    os.path.join(
        SAVE_DIR,
        "metadata.json"
    )
]


for path in required_saved_files:

    if not os.path.exists(
        path
    ):

        raise FileNotFoundError(
            f"Expected saved file was not created: "
            f"{path}"
        )


print(
    "\nSaved-model verification passed."
)


print(
    "\n"
)

print(
    "=" * 70
)

print(
    "SECTIONS 1-4 COMPLETED SUCCESSFULLY"
)

print(
    "=" * 70
)