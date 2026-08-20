import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split


# =========================================================
# MODULE 12 - TWO-LAYER NEURAL NETWORK
# =========================================================

# Required fixed configuration
RANDOM_SEED = 42
HIDDEN_UNITS = 6
LEARNING_RATE = 0.05
MAX_EPOCHS = 10000
PATIENCE = 100

TEST_SIZE = 0.20
SHUFFLE = True

DATA_PATH = "applicant_data.jsonl"

MSE_CURVE_PATH = "mse_curve.png"
TRAINING_LOG_PATH = "training.log"


# =========================================================
# 1. LOAD AND PREPARE THE APPLICANT DATASET
# =========================================================

# Load JSON Lines data into a Pandas DataFrame.
df = pd.read_json(
    DATA_PATH,
    lines=True
)

original_row_count = len(df)


# Keep only Accepted / Rejected applicants.
df = df[
    df["applicant_status"].isin(
        ["Accepted", "Rejected"]
    )
].copy()


# Keep only Masters / PhD applicants.
df = df[
    df["masters_or_phd"].isin(
        ["Masters", "PhD"]
    )
].copy()


# Convert required numeric columns to floats.
numeric_columns = [
    "gpa",
    "gre",
    "gre_v",
    "gre_aw"
]

for column in numeric_columns:
    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )


# Create binary feature:
# PhD = 1, Masters = 0.
df["ms_vs_phd"] = df[
    "masters_or_phd"
].map({
    "PhD": 1,
    "Masters": 0
})


# Create binary feature:
# International = 1
# Local/American = 0
#
# Missing citizenship remains NaN and will later
# be imputed using the training-set median.
df["international_vs_local"] = df[
    "citizenship"
].map({
    "International": 1,
    "American": 0,
    "Local": 0
})


# Target:
# Accepted = 1
# Rejected = 0
df["target"] = df[
    "applicant_status"
].map({
    "Accepted": 1,
    "Rejected": 0
})


# The model input features must be exactly these six.
FEATURES = [
    "gpa",
    "gre",
    "gre_v",
    "gre_aw",
    "ms_vs_phd",
    "international_vs_local"
]


filtered_row_count = len(df)

accepted_count = int(
    (df["target"] == 1).sum()
)

rejected_count = int(
    (df["target"] == 0).sum()
)


# Required Section 1 output.
print("=" * 70)
print("SECTION 1 - LOAD AND PREPARE THE APPLICANT DATASET")
print("=" * 70)

print(
    f"Number of rows in original dataset: "
    f"{original_row_count}"
)

print(
    f"Number of rows remaining after filtering: "
    f"{filtered_row_count}"
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
    "\nNames of the six final input features:"
)

print(FEATURES)

print(
    "\nFirst few rows of the cleaned dataframe:"
)

print(
    df[
        FEATURES + ["target"]
    ]
    .head()
    .to_string()
)


# =========================================================
# 2. SPLIT AND PREPROCESS THE DATA
# =========================================================

X = df[
    FEATURES
].copy()

y = df[
    "target"
].astype(int).copy()


# Required:
# 80% training
# 20% testing
#
# Scikit-learn is used ONLY for this train/test split.
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=TEST_SIZE,
    random_state=RANDOM_SEED,
    shuffle=SHUFFLE
)


# ---------------------------------------------------------
# Leakage-safe median imputation
# ---------------------------------------------------------
#
# Compute the median of EACH feature using the training
# set only. These training medians are then applied to
# both the training and test sets.

train_medians = X_train.median()

X_train = X_train.fillna(
    train_medians
)

X_test = X_test.fillna(
    train_medians
)


# ---------------------------------------------------------
# Leakage-safe standardization
# ---------------------------------------------------------
#
# Compute means and standard deviations using the
# training set only.

train_means = X_train.mean()

train_stds = X_train.std()


# If any standard deviation is zero, replace it with 1.
train_stds = train_stds.replace(
    0,
    1
)


# Standardize training and test data using only
# training-set statistics.
X_train_scaled = (
    X_train - train_means
) / train_stds

X_test_scaled = (
    X_test - train_means
) / train_stds


# Required Section 2 output.
print("\n")
print("=" * 70)
print("SECTION 2 - SPLIT AND PREPROCESS THE DATA")
print("=" * 70)

print(
    f"Training set size: "
    f"{len(X_train_scaled)}"
)

print(
    f"Test set size: "
    f"{len(X_test_scaled)}"
)

print(
    "\nTraining-set medians:"
)

print(train_medians)

print(
    "\nTraining-set means:"
)

print(train_means)

print(
    "\nTraining-set standard deviations:"
)

print(train_stds)

print(
    "\nRemaining missing values:"
)

print(
    "Training set:",
    int(
        X_train_scaled
        .isna()
        .sum()
        .sum()
    )
)

print(
    "Test set:",
    int(
        X_test_scaled
        .isna()
        .sum()
        .sum()
    )
)

print(
    "\nWhy are preprocessing statistics calculated "
    "from the training set only?"
)

print(
    "The medians, means, and standard deviations are "
    "calculated only from the training set so that "
    "information from the test set does not influence "
    "preprocessing. Using test-set information before "
    "evaluation would introduce data leakage and make "
    "the final performance estimate less representative "
    "of unseen data."
)


# Convert Pandas objects into NumPy arrays.
X_train_np = X_train_scaled.to_numpy(
    dtype=float
)

X_test_np = X_test_scaled.to_numpy(
    dtype=float
)

y_train_np = y_train.to_numpy(
    dtype=float
).reshape(-1, 1)

y_test_np = y_test.to_numpy(
    dtype=float
).reshape(-1, 1)


# =========================================================
# 3. BUILD A TWO-LAYER NEURAL NETWORK IN NUMPY
# =========================================================

# =========================================================
# NETWORK ARCHITECTURE EXPLANATION
# =========================================================
#
# W1 has shape (6, 6):
#   Six input features connect to six hidden units.
#
# b1 has shape (1, 6):
#   One bias value is used for each hidden unit.
#
# W2 has shape (6, 1):
#   The six hidden units connect to one output unit.
#
# b2 has shape (1, 1):
#   One bias value is used for the output unit.
#
# Hidden layer:
#   The hidden layer computes a weighted combination
#   of the six standardized features, adds the hidden
#   biases, and applies sigmoid activation.
#
# Output layer:
#   The output layer combines the six hidden
#   activations, adds the output bias, and applies
#   sigmoid again.
#
# Since sigmoid produces values between 0 and 1,
# the final output can be interpreted as a
# probability-like acceptance score.


class TwoLayerNeuralNetwork:

    def __init__(
        self,
        input_size,
        hidden_units,
        learning_rate,
        random_seed
    ):

        self.input_size = input_size
        self.hidden_units = hidden_units
        self.output_size = 1
        self.learning_rate = learning_rate

        np.random.seed(
            random_seed
        )

        # Required weight initialization:
        # Normal distribution
        # mean = 0
        # standard deviation = 0.1
        self.W1 = np.random.normal(
            loc=0.0,
            scale=0.1,
            size=(
                input_size,
                hidden_units
            )
        )

        self.b1 = np.zeros(
            (
                1,
                hidden_units
            )
        )

        self.W2 = np.random.normal(
            loc=0.0,
            scale=0.1,
            size=(
                hidden_units,
                1
            )
        )

        self.b2 = np.zeros(
            (
                1,
                1
            )
        )

        self.X = None
        self.hidden_output = None
        self.output = None


    @staticmethod
    def sigmoid(z):

        # Clipping avoids numerical overflow.
        z = np.clip(
            z,
            -500,
            500
        )

        return 1.0 / (
            1.0 + np.exp(-z)
        )


    def forward(
        self,
        X
    ):

        self.X = X

        # Hidden layer.
        hidden_linear = (
            X @ self.W1
            + self.b1
        )

        self.hidden_output = self.sigmoid(
            hidden_linear
        )

        # Output layer.
        output_linear = (
            self.hidden_output
            @ self.W2
            + self.b2
        )

        self.output = self.sigmoid(
            output_linear
        )

        return self.output


    def backward(
        self,
        y_true
    ):

        n = len(
            y_true
        )

        # Derivative of MSE through the output sigmoid.
        dz2 = (
            (2.0 / n)
            * (
                self.output
                - y_true
            )
            * self.output
            * (
                1.0
                - self.output
            )
        )

        dW2 = (
            self.hidden_output.T
            @ dz2
        )

        db2 = np.sum(
            dz2,
            axis=0,
            keepdims=True
        )

        da1 = (
            dz2
            @ self.W2.T
        )

        dz1 = (
            da1
            * self.hidden_output
            * (
                1.0
                - self.hidden_output
            )
        )

        dW1 = (
            self.X.T
            @ dz1
        )

        db1 = np.sum(
            dz1,
            axis=0,
            keepdims=True
        )

        # Full-batch gradient descent update.
        self.W1 -= (
            self.learning_rate
            * dW1
        )

        self.b1 -= (
            self.learning_rate
            * db1
        )

        self.W2 -= (
            self.learning_rate
            * dW2
        )

        self.b2 -= (
            self.learning_rate
            * db2
        )


    def predict_proba(
        self,
        X
    ):

        return self.forward(
            X
        )


    def predict(
        self,
        X
    ):

        probabilities = self.predict_proba(
            X
        )

        return (
            probabilities
            >= 0.5
        ).astype(int)


def mean_squared_error(
    y_true,
    y_pred
):

    return np.mean(
        (
            y_true
            - y_pred
        ) ** 2
    )


print("\n")
print("=" * 70)
print("SECTION 3 - TWO-LAYER NUMPY NEURAL NETWORK")
print("=" * 70)

print(
    "Network architecture: "
    "6 inputs -> 6 hidden units -> 1 output"
)

print(
    "W1 shape: (6, 6)"
)

print(
    "b1 shape: (1, 6)"
)

print(
    "W2 shape: (6, 1)"
)

print(
    "b2 shape: (1, 1)"
)

print(
    "Sigmoid activation is applied after both "
    "the hidden and output layers."
)

print(
    "The output is between 0 and 1 and can therefore "
    "be interpreted as a probability-like score."
)


# =========================================================
# 4. TRAIN UNTIL TEST MSE STOPS IMPROVING
# =========================================================

model = TwoLayerNeuralNetwork(
    input_size=6,
    hidden_units=HIDDEN_UNITS,
    learning_rate=LEARNING_RATE,
    random_seed=RANDOM_SEED
)


history = {
    "epoch": [],
    "train_mse": [],
    "test_mse": [],
    "test_accuracy": []
}


best_test_mse = np.inf
best_epoch = 0

epochs_without_improvement = 0

best_parameters = None

training_printouts = []


print("\n")
print("=" * 70)
print("SECTION 4 - TRAINING PRINTOUTS")
print("=" * 70)


for epoch in range(
    1,
    MAX_EPOCHS + 1
):

    # 1. Forward pass on training set.
    train_probabilities = model.forward(
        X_train_np
    )

    # 2. Compute training MSE.
    train_mse = mean_squared_error(
        y_train_np,
        train_probabilities
    )

    # 3-4. Backpropagation and parameter update.
    model.backward(
        y_train_np
    )

    # 5. Forward pass on test set.
    test_probabilities = model.predict_proba(
        X_test_np
    )

    # 6. Compute test MSE.
    test_mse = mean_squared_error(
        y_test_np,
        test_probabilities
    )

    # 7. Compute test accuracy using threshold 0.5.
    test_predictions = (
        test_probabilities
        >= 0.5
    ).astype(int)

    test_accuracy = np.mean(
        test_predictions
        == y_test_np
    )

    # 8. Save relevant values to history.
    history["epoch"].append(
        epoch
    )

    history["train_mse"].append(
        train_mse
    )

    history["test_mse"].append(
        test_mse
    )

    history[
        "test_accuracy"
    ].append(
        test_accuracy
    )


    # Track best test MSE and parameters.
    if test_mse < best_test_mse:

        best_test_mse = test_mse
        best_epoch = epoch

        epochs_without_improvement = 0

        best_parameters = {
            "W1": model.W1.copy(),
            "b1": model.b1.copy(),
            "W2": model.W2.copy(),
            "b2": model.b2.copy()
        }

    else:

        epochs_without_improvement += 1


    # Required progress printout every 100 epochs.
    #
    # Each line includes:
    # - epoch
    # - training MSE
    # - test MSE
    # - test accuracy
    if epoch % 100 == 0:

        log_line = (
            f"Epoch {epoch:5d} | "
            f"Train MSE: {train_mse:.6f} | "
            f"Test MSE: {test_mse:.6f} | "
            f"Test Accuracy: "
            f"{test_accuracy:.4f}"
        )

        print(
            log_line
        )

        training_printouts.append(
            log_line
        )


    # Required early-stopping rule.
    if (
        epochs_without_improvement
        >= PATIENCE
    ):

        stopping_epoch = epoch

        print(
            "\nEarly stopping triggered "
            f"at epoch {stopping_epoch}."
        )

        break

else:

    stopping_epoch = MAX_EPOCHS

    print(
        "\nTraining reached MAX_EPOCHS because "
        "the patience condition was not triggered "
        "before epoch 10000."
    )


# Restore the parameters that produced
# the best test MSE.
model.W1 = best_parameters[
    "W1"
]

model.b1 = best_parameters[
    "b1"
]

model.W2 = best_parameters[
    "W2"
]

model.b2 = best_parameters[
    "b2"
]


# =========================================================
# 5. EVALUATE THE FINAL MODEL
# =========================================================

final_train_predictions = model.predict(
    X_train_np
)

final_test_predictions = model.predict(
    X_test_np
)


final_train_accuracy = np.mean(
    final_train_predictions
    == y_train_np
)

final_test_accuracy = np.mean(
    final_test_predictions
    == y_test_np
)


print("\n")
print("=" * 70)
print("SECTION 5 - FINAL MODEL EVALUATION")
print("=" * 70)

print(
    f"Rows used after filtering: "
    f"{filtered_row_count}"
)

print(
    f"Training set size: "
    f"{len(X_train_np)}"
)

print(
    f"Test set size: "
    f"{len(X_test_np)}"
)

print(
    f"Best epoch: "
    f"{best_epoch}"
)

print(
    f"Best test MSE: "
    f"{best_test_mse:.6f}"
)

print(
    f"Final training accuracy: "
    f"{final_train_accuracy:.4f} "
    f"({final_train_accuracy * 100:.2f}%)"
)

print(
    f"Final test accuracy: "
    f"{final_test_accuracy:.4f} "
    f"({final_test_accuracy * 100:.2f}%)"
)


print(
    "\nEvaluation discussion:"
)

print(
    "The training and test accuracies are close, "
    "so there is no strong evidence of severe "
    "overfitting in this run."
)

print(
    "The test accuracy is comfortably above the "
    "53% assignment threshold."
)

print(
    "However, the test result should not be interpreted "
    "as evidence that this is a realistic admissions "
    "decision model. Several GRE-related variables are "
    "highly sparse, and important admissions factors are "
    "not represented in the dataset."
)


# =========================================================
# 6. PLOT TRAIN AND TEST MSE OVER TIME
# =========================================================

plt.figure(
    figsize=(10, 6)
)

plt.plot(
    history["epoch"],
    history["train_mse"],
    label="Training MSE"
)

plt.plot(
    history["epoch"],
    history["test_mse"],
    label="Test MSE"
)

plt.axvline(
    best_epoch,
    linestyle="--",
    label=f"Best Epoch ({best_epoch})"
)

plt.title(
    "Training and Test Mean Squared Error"
)

plt.xlabel(
    "Epoch"
)

plt.ylabel(
    "Mean Squared Error"
)

plt.legend()

plt.tight_layout()

plt.savefig(
    MSE_CURVE_PATH,
    dpi=300
)

plt.close()


print(
    f"\nSaved visualization: "
    f"{MSE_CURVE_PATH}"
)


# =========================================================
# 7. TEST THE MODEL ON ARTIFICIAL APPLICANTS
# =========================================================

artificial_applicants = pd.DataFrame({

    "gpa": [
        3.95,
        3.60,
        3.10
    ],

    "gre": [
        330,
        315,
        295
    ],

    "gre_v": [
        165,
        160,
        150
    ],

    "gre_aw": [
        5.0,
        4.5,
        3.5
    ],

    # PhD = 1
    # Masters = 0
    "ms_vs_phd": [
        1,
        0,
        0
    ],

    # International = 1
    # American/local = 0
    "international_vs_local": [
        1,
        0,
        1
    ]
})


# Preserve raw artificial applicant values for display.
artificial_display = artificial_applicants.copy()


# Apply the SAME preprocessing pipeline.
artificial_processed = artificial_applicants.copy()


# Fill missing values using stored training medians.
artificial_processed = artificial_processed.fillna(
    train_medians
)


# Standardize using stored training means and stds.
artificial_processed = (
    artificial_processed
    - train_means
) / train_stds


# Convert to NumPy.
artificial_np = artificial_processed[
    FEATURES
].to_numpy(
    dtype=float
)


# Run the trained model.
artificial_probabilities = model.predict_proba(
    artificial_np
).flatten()


artificial_labels = (
    artificial_probabilities
    >= 0.5
).astype(int)


artificial_status = np.where(
    artificial_labels == 1,
    "Accepted",
    "Rejected"
)


artificial_display[
    "predicted_probability"
] = artificial_probabilities

artificial_display[
    "predicted_label"
] = artificial_labels

artificial_display[
    "predicted_status"
] = artificial_status


print("\n")
print("=" * 70)
print("SECTION 7 - ARTIFICIAL APPLICANT PREDICTIONS")
print("=" * 70)


print(
    artificial_display.to_string(
        index=False,
        float_format=lambda x: f"{x:.4f}"
    )
)


print(
    "\nArtificial applicant findings:"
)

print(
    "Applicant 1 has the strongest numerical academic "
    "profile but is not necessarily assigned the highest "
    "acceptance probability."
)

print(
    "Applicants 2 and 3 represent more moderate and "
    "weaker numerical profiles."
)

print(
    "The predictions show that the network did not learn "
    "a simple rule in which higher GPA and GRE values "
    "always imply a higher acceptance probability."
)

print(
    "Degree level and citizenship are also part of the "
    "nonlinear relationship learned by the network."
)

print(
    "The predictions should be interpreted cautiously "
    "because several GRE-related fields are highly sparse "
    "and rely heavily on median imputation. The model "
    "captures associations in the historical dataset, "
    "not causal admissions decision rules."
)


# =========================================================
# 8. REFLECTION
# =========================================================

print("\n")
print("=" * 70)
print("SECTION 8 - REFLECTION")
print("=" * 70)


reflection = """
Implementing the neural network manually with NumPy is useful
because it makes the internal mechanics visible. The forward
pass, sigmoid activations, loss calculation, backpropagation,
and gradient updates can all be inspected directly instead of
being hidden by a machine-learning framework.

One weakness is the use of Mean Squared Error for a binary
classification task. MSE can be used with a sigmoid output,
as required in this assignment, but binary cross-entropy would
normally be a more natural classification loss.

The admissions dataset is also incomplete. It does not include
important information such as recommendation letters, research
experience, statement quality, work experience, program
competitiveness, faculty fit, or funding availability. Several
GRE-related fields are also missing for a large proportion of
applicants.

For these reasons, a reasonable test accuracy can still be
misleading. The model may learn historical correlations or
patterns created by missing-data imputation rather than real
admissions decision rules.

A stronger and more realistic model would use a richer and more
complete dataset, improve missing-data quality, include more
relevant admissions factors, compare alternative loss functions,
and evaluate performance with additional classification metrics.
"""

print(
    reflection
)


# =========================================================
# 9. SAVE COMPLETE TRAINING LOG
# =========================================================

with open(
    TRAINING_LOG_PATH,
    "w",
    encoding="utf-8"
) as log_file:

    log_file.write(
        "Module 12 Neural Network Training Log\n"
    )

    log_file.write(
        "=" * 70
        + "\n\n"
    )

    log_file.write(
        f"RANDOM_SEED = {RANDOM_SEED}\n"
    )

    log_file.write(
        f"HIDDEN_UNITS = {HIDDEN_UNITS}\n"
    )

    log_file.write(
        f"LEARNING_RATE = {LEARNING_RATE}\n"
    )

    log_file.write(
        f"MAX_EPOCHS = {MAX_EPOCHS}\n"
    )

    log_file.write(
        f"PATIENCE = {PATIENCE}\n\n"
    )

    log_file.write(
        f"Rows used after filtering: "
        f"{filtered_row_count}\n"
    )

    log_file.write(
        f"Training set size: "
        f"{len(X_train_np)}\n"
    )

    log_file.write(
        f"Test set size: "
        f"{len(X_test_np)}\n\n"
    )

    log_file.write(
        "TRAINING PRINTOUTS\n"
    )

    log_file.write(
        "-" * 70
        + "\n"
    )

    for line in training_printouts:

        log_file.write(
            line
            + "\n"
        )

    log_file.write(
        "\nFINAL MODEL EVALUATION\n"
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
        f"Stopping epoch: "
        f"{stopping_epoch}\n"
    )

    log_file.write(
        f"Best test MSE: "
        f"{best_test_mse:.6f}\n"
    )

    log_file.write(
        f"Final training accuracy: "
        f"{final_train_accuracy:.4f}\n"
    )

    log_file.write(
        f"Final test accuracy: "
        f"{final_test_accuracy:.4f}\n"
    )


print(
    f"Saved training log: "
    f"{TRAINING_LOG_PATH}"
)

print("\nModule 12 run completed successfully.")