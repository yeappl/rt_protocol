# Breast Radiotherapy Decision Support Tool

## Overview

The Breast Radiotherapy Decision Support Tool is a lightweight, locally deployable clinical decision-support application that combines a Large Language Model (LLM) with a rule-based decision engine to extract structured clinical information from breast cancer clinic letters and recommend appropriate radiotherapy planning techniques.

The system is designed to:

1. Process unstructured clinical correspondence.
2. Extract clinically relevant features using a local LLM.
3. Convert extracted information into a structured JSON format.
4. Apply deterministic protocol-based decision logic.
5. Recommend an appropriate radiotherapy technique and fractionation schedule.
6. Generate a concise clinical summary and rationale for clinician review.

The application is intended for research, workflow automation, and decision-support purposes. It is not intended to replace clinical judgement.

---

## Features

### Natural Language Processing

The system uses a locally hosted LLM via Ollama to extract structured information from free-text clinic letters.

Examples of extracted fields include:

* Patient age
* Tumour laterality
* Tumour size
* Histological subtype
* Tumour grade
* ER status
* PR status
* HER2 status
* Nodal status
* Surgical information
* Margin status
* Lymphovascular invasion
* Multicentric disease
* Immunosuppression status
* Distance from treatment centre

### Structured Output

Clinical letters are converted into JSON objects:

```json
{
  "patient_age": 62,
  "laterality": "left",
  "tumour_size_cm": 1.8,
  "grade": 2,
  "er_positive": true,
  "pr_positive": true,
  "her2_positive": false,
  "nodal_status": null,
  "margins_positive": false,
  "lymphovascular_invasion": false,
  "dcis_present": false,
  "multicentric": false,
  "histology": {
    "type": "invasive ductal carcinoma",
    "grade": 2
  }
}
```

### Decision Support

The extracted data are evaluated using a deterministic decision tree derived from institutional breast radiotherapy protocols.

Supported recommendations include:

* Partial Breast Irradiation (PBI)
* Three-Dimensional Conformal Radiotherapy (3DCRT)
* Volumetric Modulated Arc Therapy (VMAT)

### Output Report

The application generates:

* Clinical summary
* Recommended radiotherapy technique
* Recommended fractionation
* Clinical rationale
* Special considerations

---

## System Architecture

```text
Clinical Letter
       │
       ▼
 Local LLM (Ollama)
       │
       ▼
 Structured JSON
       │
       ▼
 Pydantic Validation
       │
       ▼
 Decision Tree Engine
       │
       ▼
 Recommendation Report
```

---

## Installation

### Prerequisites

* Python 3.10+
* Ollama
* Llama 3.2 1B model

### Install Ollama

Linux/macOS:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Windows:

Download and install Ollama from:

https://ollama.com

### Download Model

```bash
ollama pull llama3.2:1b
```

### Install Python Dependencies

```bash
pip install ollama
pip install pydantic
```

Optional:

```bash
pip install pandas
pip install fastapi
pip install uvicorn
```

---

## Usage

### Extract Structured Data

```python
from rt_protocol import extract_structured_data

letter = open("clinic_letter.txt").read()

data = extract_structured_data(letter)

print(data)
```

### Run Decision Engine

```python
from rt_protocol import recommend_radiotherapy

recommend_radiotherapy(data)
```

### Or run from terminal
```console
python ./rt_protocol.py
Enter clinical letter, or press <Enter> to use template letter:

```

---

## Example Output

```text
Clinical Summary
----------------
Age: 62
Tumour size: 1.8 cm
Grade: 2
ER+: True
PR+: True
HER2+: False
Nodal status: N0

Recommended Technique
---------------------
Partial Breast Irradiation (PBI)

Fractionation
-------------
PTV_High: 320 cGy × 15 fractions
PTV_Low : 267 cGy × 15 fractions

Rationale
---------
- Small low-risk tumour
- Node negative
- ER positive
- No lymphovascular invasion
- Clear surgical margins
```

---

## Decision Logic

### Partial Breast Irradiation (PBI)

Generally recommended for patients with:

* Age ≥ 50 years
* Small tumour burden
* Node-negative disease
* ER-positive disease
* Negative margins
* No lymphovascular invasion
* No multicentric disease

### 3DCRT

Preferred for:

* Standard whole-breast irradiation
* Patients without complex anatomy
* Cases where dose constraints can be achieved using conformal planning

### VMAT

Recommended for:

* Positive lymph nodes
* Larger tumours
* Multicentric disease
* Complex anatomy
* Situations where 3DCRT dose constraints cannot be met
* Integrated boost techniques

---

## Validation

The application performs schema validation using Pydantic before any clinical decision logic is executed.

Required fields are enforced to ensure that incomplete LLM outputs are detected before recommendation generation.

---

## Limitations

* Recommendations are based solely on extracted information available in clinic letters.
* Dosimetric considerations are not assessed.
* Cardiac anatomy and treatment planning metrics are not evaluated.
* Physician review remains mandatory.
* The application should not be used as an autonomous clinical decision-making system.

---

## Future Development

Planned enhancements include:

* ASTRO PBI suitability classification
* NCCN guideline integration
* Confidence scoring
* Explainable AI outputs
* Dosimetric prediction models
* Integration with APOLLO
* FastAPI web interface
* DICOM RT interoperability
* Multi-centre protocol support

---

## Disclaimer

This software is intended for research and clinical workflow support purposes only.

The recommendations generated by the application do not constitute medical advice and must be reviewed by a qualified radiation oncologist before implementation. Clinical responsibility remains with the treating physician.
