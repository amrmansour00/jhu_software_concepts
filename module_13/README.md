# Module 13 - Fine-Tuned Language Model Admissions Classifier

**Student:** Amr Mansour  
**JHED ID:** amanso8  
**Course:** Software Concepts  
**Institution:** Johns Hopkins University

---

## Overview

This project extends the graduate admissions analysis developed in previous modules by fine-tuning a pretrained language model to classify graduate admissions outcomes.

The project uses **DistilBERT (`distilbert-base-uncased`)**, PyTorch, and Hugging Face Transformers to classify graduate applicants as:

- Accepted
- Rejected

The complete workflow includes:

1. Loading and cleaning the graduate admissions dataset.
2. Converting applicant information into a unified language-model input.
3. Creating stratified training and testing datasets.
4. Fine-tuning a pretrained DistilBERT sequence-classification model.
5. Evaluating the trained model on a held-out test set.
6. Saving and reloading the trained model without retraining.
7. Deploying the saved model through a Flask webpage.
8. Comparing the transformer model with the Module 12 NumPy neural network.
9. Discussing model limitations and ethical considerations.

---

## Dataset

The source dataset contains **14,188 graduate admissions records**.

Only applicants with final outcomes of `Accepted` or `Rejected` are used for binary classification. `Waitlisted` records are excluded because the assignment focuses on a two-class classification problem.

After filtering:

| Class | Records |
|---|---:|
| Accepted | 5,789 |
| Rejected | 6,923 |
| **Total** | **12,712** |

The resulting class distribution is approximately:

- Accepted: 45.54%
- Rejected: 54.46%

### Features Used

Text-based fields:

- `program_name`
- `university`

Structured/non-text fields:

- `degree`
- `student_type`
- `gpa`
- `gre_score`
- `gre_v_score`
- `gre_aw`
- `start_term`

Missing values are represented consistently as `Unknown`.

The classification target is encoded as:

- `0 = Rejected`
- `1 = Accepted`

The target label and `applicant_status` are never included in the model input.

---

## Unified Model Input

Because DistilBERT expects text input, the available textual and structured applicant information is converted into a single natural-language representation.

Each applicant is represented using the following template:

```text
Program: <program_name>. University: <university>. Degree: <degree>.
Citizenship: <student_type>. GPA: <gpa>. GRE: <gre_score>.
GRE Verbal: <gre_v_score>. GRE Analytical Writing: <gre_aw>.
Term: <start_term>.
```

For example:

```text
Program: Global Health. University: Meharry Medical College.
Degree: PhD. Citizenship: American. GPA: 3.9. GRE: Unknown.
GRE Verbal: Unknown. GRE Analytical Writing: Unknown.
Term: Fall 2026.
```

This approach allows both textual information and structured applicant attributes to be processed by the same pretrained transformer model.

---

## Train/Test Split

The filtered dataset is divided into training and testing sets using a stratified 80/20 split.

The split uses:

```text
test_size = 0.20
random_state = 42
```

Result:

| Dataset | Accepted | Rejected | Total |
|---|---:|---:|---:|
| Training | 4,631 | 5,538 | 10,169 |
| Test | 1,158 | 1,385 | 2,543 |

Stratification preserves approximately the same Accepted/Rejected class distribution in both datasets.

The model is trained only on the training set. The held-out test set is used to evaluate performance on applicants that were not used during model training.

---

## Model Selection

The pretrained model selected for the assignment is:

```text
distilbert-base-uncased
```

DistilBERT was selected because it provides pretrained transformer-based language representations while being smaller and computationally lighter than full BERT.

This makes it more suitable for fine-tuning on ordinary hardware while still demonstrating the use of a modern pretrained language model.

The matching DistilBERT tokenizer is used so that the input representation follows the vocabulary and tokenization scheme expected by the pretrained model.

---

## Training Configuration

The final training configuration is:

| Parameter | Value |
|---|---|
| Model | `distilbert-base-uncased` |
| Tokenizer | `distilbert-base-uncased` |
| Maximum sequence length | 256 |
| Batch size | 8 |
| Number of epochs | 2 |
| Learning rate | `2e-5` |
| Optimizer | AdamW |
| Random seed | 42 |
| Device | CPU |

Training was performed using PyTorch.

Because the available machine did not have CUDA support, training was performed entirely on the CPU.

---

## Training Results

The model was trained for two epochs.

| Epoch | Training Loss | Test Loss | Test Accuracy |
|---|---:|---:|---:|
| 1 | 0.5774 | 0.5422 | 73.89% |
| 2 | 0.5365 | 0.5383 | 73.10% |

Epoch 1 produced the highest test accuracy and was therefore retained as the **best checkpoint**.

The best model was saved automatically to:

```text
saved_model/
```

This prevents the final application from depending on the model state from the last training epoch when an earlier checkpoint performed better on the held-out data.

---

## Final Model Evaluation

The saved best checkpoint was reloaded and evaluated against the complete held-out test set of **2,543 applicants**.

### Final Metrics

| Metric | Result |
|---|---:|
| Accuracy | **73.93%** |
| Precision | **0.7630** |
| Recall | **0.6200** |
| F1 Score | **0.6841** |
| Majority-Class Baseline | **54.46%** |

The model therefore performs substantially better than predicting only the majority class.

---

## Confusion Matrix

The final confusion matrix is:

| Actual / Predicted | Rejected | Accepted |
|---|---:|---:|
| Rejected | 1,162 | 223 |
| Accepted | 440 | 718 |

This corresponds to:

- **True Negatives:** 1,162
- **False Positives:** 223
- **False Negatives:** 440
- **True Positives:** 718

The actual test-set distribution is:

- Rejected: 1,385 (54.46%)
- Accepted: 1,158 (45.54%)

The model predicted:

- Rejected: 1,602 (63.00%)
- Accepted: 941 (37.00%)

The model therefore predicts `Rejected` more frequently than the actual test-set distribution, suggesting some tendency toward the Rejected class.

Detailed predictions are stored in:

```text
evaluation_predictions.csv
```

The calculated evaluation metrics are stored in:

```text
evaluation_metrics.json
```

---

## Comparison with Module 12

Module 12 implemented a two-layer neural network manually using NumPy.

The Module 13 assignment replaces that manually implemented network with a fine-tuned pretrained transformer.

| Model | Test Accuracy |
|---|---:|
| Module 12 NumPy Neural Network | 72.28% |
| Module 13 Fine-Tuned DistilBERT | **73.93%** |

The Module 13 transformer improves test accuracy by approximately **1.65 percentage points**.

The DistilBERT model also has the advantage of incorporating textual information such as the program name and university directly into the model input.

However, this improvement comes with substantially greater computational requirements. Training the transformer on CPU required several hours, whereas the simpler NumPy neural network was much less computationally demanding.

Therefore, although the pretrained transformer produced better predictive performance, the improvement should be considered together with the additional computational and deployment complexity.

---

## Saving the Trained Model

The best model checkpoint and tokenizer are persisted in the `saved_model` directory.

```text
saved_model/
├── config.json
├── metadata.json
├── model.safetensors
├── tokenizer.json
└── tokenizer_config.json
```

The saved `metadata.json` file contains information required to reproduce the inference configuration, including:

- source pretrained model
- tokenizer
- maximum sequence length
- batch size
- configured epochs
- learning rate
- optimizer
- device
- random seed
- best epoch
- best test accuracy
- best test loss
- label mapping
- fields used during modeling
- unified model-input template

---

## Reloading the Model

The saved model can be reloaded without performing training again.

Run:

```powershell
python inference.py
```

The script verifies the saved artifacts, loads the tokenizer and trained DistilBERT model, and performs inference on artificial applicant examples.

This demonstrates that model training and model deployment are separated.

The Flask application uses the same saved model rather than retraining the model whenever the application starts or receives a prediction request.

---

## Flask Web Application

The trained model is integrated into the existing Flask application.

The prediction page is available at:

```text
/will-you-get-in
```

Start the Flask application using:

```powershell
python run.py
```

Then open:

```text
http://127.0.0.1:5000/will-you-get-in
```

The **Will You Get In?** page allows users to enter applicant information including:

- program
- university
- degree
- citizenship/student type
- GPA
- GRE score
- GRE verbal score
- GRE analytical writing score
- start term

The webpage converts these values into exactly the same unified input format used during model training.

The saved DistilBERT model then returns:

- predicted admissions status
- Accepted probability
- Rejected probability

The prediction interface therefore demonstrates an end-to-end workflow from user input through transformer inference to a web-based result.

---

## Web Application Disclaimer

The prediction page includes a disclaimer explaining that the application is an educational class project.

The model is trained on historical, self-reported graduate admissions data and its output should not be interpreted as an actual admissions decision or reliable estimate of an individual's admission prospects.

The webpage is intended to demonstrate machine-learning deployment rather than provide real admissions advice.

---

## Project Structure

The final Module 13 project contains:

```text
module_13/
│
├── applicant_data.csv
├── train_model.py
├── evaluate_model.py
├── inference.py
├── run.py
├── db.py
├── query_data.py
├── README.md
├── requirements.txt
├── training.log
├── evaluation_metrics.json
├── evaluation_predictions.csv
├── writeup.pdf
│
├── saved_model/
│   ├── config.json
│   ├── metadata.json
│   ├── model.safetensors
│   ├── tokenizer.json
│   └── tokenizer_config.json
│
├── templates/
│   ├── index.html
│   └── will_you_get_in.html
│
├── static/
│   └── style.css
│
└── screenshots/
    ├── blank_prediction_page.png
    ├── completed_prediction_page.png
    └── training_evaluation.png
```

---

## Installation

Install the project dependencies with:

```powershell
pip install -r requirements.txt
```

The requirements include the packages used for data processing, model training, evaluation, inference, and the Flask application.

---

## Running the Project

### 1. Train the Model

Training is required only when recreating the fine-tuned model:

```powershell
python train_model.py
```

The best checkpoint is saved to:

```text
saved_model/
```

Because transformer fine-tuning is computationally intensive on CPU, retraining is not required to run the final application when the saved model is already available.

### 2. Evaluate the Model

Run:

```powershell
python evaluate_model.py
```

This reconstructs the same held-out test split, reloads the saved best checkpoint, performs inference, and calculates the final classification metrics.

The evaluation produces:

```text
Accuracy:  73.93%
Precision: 0.7630
Recall:    0.6200
F1 Score:  0.6841
```

### 3. Verify Saved-Model Inference

Run:

```powershell
python inference.py
```

This demonstrates that the trained model and tokenizer can be reloaded from disk and used for inference without retraining.

### 4. Run the Flask Application

Run:

```powershell
python run.py
```

Then navigate to:

```text
http://127.0.0.1:5000/will-you-get-in
```

---

## Screenshots

The `screenshots` directory contains evidence of the completed application and model evaluation:

```text
screenshots/
├── blank_prediction_page.png
├── completed_prediction_page.png
└── training_evaluation.png
```

These demonstrate:

- the prediction page before applicant information is submitted
- a completed model prediction through the Flask application
- the final held-out evaluation metrics and confusion matrix

---

## Limitations

Although the model achieves a held-out test accuracy of 73.93%, this result should not be interpreted as evidence that it can realistically predict graduate admissions decisions.

The available dataset does not contain many factors that may influence actual admissions decisions, including:

- recommendation letters
- research experience
- publications
- statement quality
- work experience
- faculty fit
- interviews
- funding availability
- program competitiveness
- broader applicant context

Several GRE-related fields are also highly sparse.

As a result, the model may learn patterns produced by missing data, historical reporting behavior, or other correlations in the dataset rather than meaningful admissions decision rules.

The model's tendency to predict `Rejected` more frequently than the actual test distribution also demonstrates why accuracy alone is not sufficient for evaluating a classification system.

---

## Ethical Considerations

The admissions dataset consists of historical, self-reported information and may contain reporting errors, missing information, selection bias, and historical institutional patterns.

A pretrained language model can learn statistical associations involving universities, academic programs, citizenship categories, degree types, and other applicant characteristics without understanding whether those relationships are fair, appropriate, or causal.

Deploying such a model as a real admissions decision system could therefore reinforce historical patterns or produce misleading conclusions about individual applicants.

For this reason, the application is intended strictly as an **educational demonstration of language-model fine-tuning and deployment**.

It should not be used to make, recommend, or influence actual university admissions decisions.

---

## Reflection

This assignment demonstrates the difference between building a neural network manually and adapting a pretrained language model.

Module 12 provided visibility into the mechanics of neural networks by implementing forward propagation, loss calculation, backpropagation, and parameter updates directly using NumPy.

Module 13 demonstrates a different machine-learning workflow: starting from a pretrained transformer and adapting it to a specific downstream classification task.

The pretrained model produced a modest improvement in held-out accuracy from **72.28% to 73.93%** and made it possible to incorporate program and university information naturally through text.

However, this improvement required substantially more computation and a more complex software stack.

The exercise therefore demonstrates that a more sophisticated model is not automatically a better practical solution. Predictive performance, computational cost, interpretability, data quality, deployment requirements, and the consequences of errors all need to be considered together.

Most importantly, model sophistication cannot compensate for limitations in the underlying data.

---

## Final Result

Module 13 successfully demonstrates an end-to-end pretrained language-model workflow:

**Data Preparation -> Unified Input -> Train/Test Split -> DistilBERT Fine-Tuning -> Evaluation -> Model Persistence -> Reload -> Flask Deployment**

Final held-out test performance:

```text
Held-out test examples: 2,543

Accuracy:  73.93%
Precision: 0.7630
Recall:    0.6200
F1 Score:  0.6841
```

The final model exceeds the 54.46% majority-class baseline and improves upon the Module 12 NumPy neural network by approximately **1.65 percentage points**.

The project also demonstrates how a trained transformer can be saved, reloaded without retraining, and integrated into a user-facing Flask application while clearly documenting the limitations and ethical concerns associated with the resulting predictions.