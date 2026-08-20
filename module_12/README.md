# Module 12 - Two-Layer Neural Network

**Student:** Amr Mansour
**JHED ID:** amanso8

## Overview

This assignment implements, trains, evaluates, and analyzes a simple two-layer neural network for graduate admissions classification.

The neural network is implemented manually using **NumPy**. **scikit-learn is used only for the train/test split**, as required by the assignment.

The model predicts whether an applicant is:

* **Accepted = 1**
* **Rejected = 0**

using exactly six input features:

1. `gpa`
2. `gre`
3. `gre_v`
4. `gre_aw`
5. `ms_vs_phd`
6. `international_vs_local`

---

## Files Included

The `module_12` folder contains:

* `neural_network.py` - complete assignment implementation
* `applicant_data.jsonl` - applicant dataset in JSON Lines format
* `mse_curve.png` - training and test MSE over time
* `training.log` - training printouts and final evaluation results
* `writeup.pdf` - short assignment write-up containing results, graph, artificial applicant findings, and reflection
* `README.md` - instructions and assignment documentation
* `requirements.txt` - Python package requirements

---

## Requirements

The solution was developed using Python 3.10+ compatible code.

Required packages:

```text
numpy
pandas
matplotlib
scikit-learn
```

Install the dependencies with:

```bash
python -m pip install -r requirements.txt
```

---

## How to Run

Open a terminal in the `module_12` folder and run:

```bash
python neural_network.py
```

The program will:

1. Load the JSON Lines applicant dataset
2. Filter and prepare the required features
3. Split the data into training and test sets
4. Impute missing values using training-set medians
5. Standardize features using training-set statistics
6. Build the neural network using NumPy
7. Train the network using full-batch gradient descent
8. Track training MSE, test MSE, and test accuracy
9. Restore the parameters associated with the best test MSE
10. Evaluate the final model
11. Create `mse_curve.png`
12. Test the model on artificial applicants
13. Print the reflection
14. Save the complete training information to `training.log`

---

# 1. Dataset Preparation

The dataset is loaded from:

```text
applicant_data.jsonl
```

Each line is a separate JSON object.

The program keeps only records where:

* `applicant_status` is `Accepted` or `Rejected`
* `masters_or_phd` is `Masters` or `PhD`

The following fields are converted to numeric values:

* `gpa`
* `gre`
* `gre_v`
* `gre_aw`

Two binary features are created:

```text
ms_vs_phd:
PhD = 1
Masters = 0
```

```text
international_vs_local:
International = 1
Local/American = 0
```

The target variable is:

```text
Accepted = 1
Rejected = 0
```

The final model uses exactly these six input features:

```text
gpa
gre
gre_v
gre_aw
ms_vs_phd
international_vs_local
```

### Dataset Counts

```text
Original dataset rows: 14,188
Rows after filtering: 12,712
Accepted rows: 5,789
Rejected rows: 6,923
```

---

# 2. Train/Test Split and Preprocessing

The dataset is split using:

```python
train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    shuffle=True
)
```

This produces:

```text
Training set size: 10,169
Test set size: 2,543
```

### Leakage-Safe Preprocessing

All preprocessing statistics are computed from the **training set only**.

The program:

1. Computes the median of each feature from the training set
2. Uses those medians to fill missing values in both training and test sets
3. Computes feature means from the training set
4. Computes feature standard deviations from the training set
5. Replaces any zero standard deviation with 1
6. Standardizes both datasets using the training-set means and standard deviations

This prevents information from the test set from influencing training and avoids data leakage.

---

# 3. Neural Network Architecture

The required network architecture is:

```text
6 input features
        ↓
6 hidden sigmoid units
        ↓
1 sigmoid output
```

The network is implemented using **NumPy only**.

### Parameter Dimensions

```text
W1: (6, 6)
b1: (1, 6)
W2: (6, 1)
b2: (1, 1)
```

`W1` connects the six input features to the six hidden units.

`b1` contains one bias for each hidden unit.

`W2` connects the six hidden units to the single output unit.

`b2` contains the output-layer bias.

The hidden layer calculates a weighted combination of the six input features, adds its biases, and applies the sigmoid activation function.

The output layer combines the hidden-layer activations, adds its bias, and applies sigmoid again.

Because sigmoid produces a value between 0 and 1, the final output can be interpreted as a **probability-like acceptance score**.

---

## Required Hyperparameters

The implementation uses the exact assignment values:

```text
RANDOM_SEED = 42
HIDDEN_UNITS = 6
LEARNING_RATE = 0.05
MAX_EPOCHS = 10000
PATIENCE = 100
```

Weights are initialized using a normal distribution with:

```text
Mean = 0
Standard deviation = 0.1
```

All biases are initialized to zero.

The loss function is:

```text
Mean Squared Error (MSE)
```

The implementation includes the required methods:

* `forward()`
* `backward()`
* `predict_proba()`
* `predict()`

---

# 4. Training and Early Stopping

The model uses **full-batch gradient descent**.

For each epoch, the program:

1. Runs a forward pass on the training set
2. Calculates training MSE
3. Performs backpropagation
4. Updates weights and biases
5. Runs a forward pass on the test set
6. Calculates test MSE
7. Calculates test accuracy using a threshold of `0.5`
8. Saves the results to a history structure

Progress is printed every 100 epochs and includes:

```text
Epoch
Training MSE
Test MSE
Test Accuracy
```

The program tracks:

* the best test MSE
* the epoch associated with the best test MSE
* the model parameters associated with that result

If test MSE does not improve for 100 consecutive epochs, training stops and the best parameters are restored.

For the final run, test MSE continued improving through the maximum allowed epoch, so the model reached epoch 10,000 before the patience condition was triggered.

The complete training output is saved in:

```text
training.log
```

---

# 5. Final Evaluation

Final results from the completed run:

| Metric                    |   Result |
| ------------------------- | -------: |
| Rows used after filtering |   12,712 |
| Training set size         |   10,169 |
| Test set size             |    2,543 |
| Best epoch                |   10,000 |
| Best test MSE             | 0.200431 |
| Final training accuracy   |   72.83% |
| Final test accuracy       |   72.28% |

The assignment specifies that successful training should achieve at least **53% test accuracy**.

The final model achieved:

```text
72.28%
```

Training accuracy and test accuracy are very close:

```text
Training accuracy: 72.83%
Test accuracy:     72.28%
```

This does not indicate severe overfitting in this run.

However, the accuracy should not be interpreted as evidence that the model is a realistic admissions decision system because the available dataset is incomplete and several GRE-related features contain substantial missing data.

---

# 6. MSE Curve

The program creates:

```text
mse_curve.png
```

The graph contains:

* training MSE versus epoch
* test MSE versus epoch
* title
* x-axis label
* y-axis label
* legend

The best epoch is also marked on the graph.

---

# 7. Artificial Applicants

Three artificial applicants are used to test the trained model on contrasting profiles.

The same preprocessing pipeline used for the original data is also used for the artificial applicants.

### Results

| Applicant |  GPA | GRE | GRE-V | GRE-AW | Degree  | Citizenship    | Probability | Label | Status   |
| --------- | ---: | --: | ----: | -----: | ------- | -------------- | ----------: | ----: | -------- |
| 1         | 3.95 | 330 |   165 |    5.0 | PhD     | International  |      0.3549 |     0 | Rejected |
| 2         | 3.60 | 315 |   160 |    4.5 | Masters | American/Local |      0.7195 |     1 | Accepted |
| 3         | 3.10 | 295 |   150 |    3.5 | Masters | International  |      0.6742 |     1 | Accepted |

The artificial applicants produced a counterintuitive result: the applicant with the strongest numerical academic profile did not receive the highest predicted acceptance probability.

This suggests that the neural network did not learn a simple rule in which higher GPA and GRE values always result in higher acceptance probability.

Degree level and citizenship also influence the nonlinear relationships learned by the network.

These predictions should be interpreted cautiously because GRE-related variables are highly sparse in the original data and many values are therefore replaced using training-set medians.

The model reflects associations in the available historical data rather than causal admissions rules.

---

# 8. Reflection

Implementing the neural network manually using NumPy is useful because it makes the mechanics of a neural network transparent. Forward propagation, sigmoid activation, loss calculation, backpropagation, and gradient updates can all be inspected directly rather than being hidden inside a machine-learning framework.

One limitation is the use of Mean Squared Error for binary classification. MSE works with the sigmoid output required in this assignment, but binary cross-entropy would normally be a more natural loss function for this type of classification problem.

The admissions dataset is also incomplete. Important factors such as recommendation letters, research experience, statement quality, faculty fit, program competitiveness, work experience, and funding are not available.

Several GRE-related variables are also highly sparse.

Because of these limitations, even a reasonable test accuracy can be misleading. The model may learn historical correlations, relationships influenced by missing-data imputation, or patterns that do not represent actual admissions decisions.

A stronger model could use:

* a richer and more complete dataset
* improved handling of missing information
* additional admissions-related features
* alternative classification loss functions
* additional evaluation metrics beyond accuracy

The purpose of this implementation is therefore to demonstrate the mechanics of a simple two-layer neural network rather than to create a production admissions decision model.

---

## Reproducibility

The submission is self-contained.

To reproduce the results:

1. Open the `module_12` folder.
2. Install the packages from `requirements.txt`.
3. Run:

```bash
python neural_network.py
```

4. Review the console output.
5. Confirm that `mse_curve.png` and `training.log` are generated.

No absolute path to another module or directory is required.

---

## Submission

The completed `module_12` folder should be submitted to both:

* **Canvas**
* **Private GitHub repository**

The Canvas ZIP and GitHub `module_12` folder should contain the same final assignment deliverables.
