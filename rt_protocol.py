import ollama 
import json
from pydantic import BaseModel
import gradio as gr
from typing import Optional, Union

class OncologyLetter(BaseModel):
    patient_age: Optional[int]
    disease_site: Optional[str]
    side: Optional[str]
    tumour_size_cm: Optional[float]
    grade: Optional[int]
    er_positive: Optional[bool]
    pr_positive: Optional[bool]
    her2_positive: Optional[bool]
    nodal_status: Optional[str]
    surgery_type: Optional[str]
    margins_positive: Optional[bool]
    lymphovascular_invasion: Optional[bool]
    ductal_carcinoma_in_situ_present: Optional[bool]
    multicentric: Optional[str]
    immunosuppression: Optional[str]
    long_distance: Optional[str]
    histology: Optional[Union[str, dict]]

# SYSTEM_PROMPT = """
# You are a medical information extraction system.

# Extract structured data from clinical letters. 

# Return ONLY valid JSON.
# Do not include explanations.
# If a field is not found, return null.

# Side refers to left or right sided and cannot be None. 
# Age or patient_age may be given as <age>-year-old.  

# Use centimetres (cm) for tumour size.
# Convert mm to cm if necessary. 
# """

SYSTEM_PROMPT = """
You are a medical information extraction system specialised in oncology letters.
Extract structured data and return ONLY a valid JSON object. No explanations, no markdown, no code fences.
EXTRACTION RULES:
patient_age: Extract from phrases like "X-year-old", "age X", "aged X", "DOB" (calculate if today's date given).
disease_site: Extract anatomical site e.g. "breast", "lung", "prostate". Never null if letter mentions a tumour.
side: Extract "left" or "right". Look for "left", "right", "L ", "R ", "left-sided", "right-sided", "left breast", "right breast". Never return null — if truly absent return "not specified".
tumour_size_cm: Convert all sizes to cm. 10mm = 1.0, 25mm = 2.5, 0.5cm = 0.5. Look for "tumour", "lesion", "mass", "measuring", "size".
grade: Extract 1, 2, or 3 from "grade 1/2/3", "G1/G2/G3", "well/moderately/poorly differentiated" (1/2/3 respectively).
er_positive: true if "ER+", "ER positive", "oestrogen receptor positive". false if "ER-", "ER negative". Look in pathology/histology sections.
pr_positive: true if "PR+", "PR positive", "progesterone receptor positive". false if "PR-", "PR negative".
her2_positive: true if "HER2+", "HER2 positive", "HER2 3+", "HER2 amplified". false if "HER2-", "HER2 negative", "HER2 1+", "HER2 2+ not amplified".
nodal_status: Extract as string e.g. "N0", "node negative", "1/3 nodes positive", "sentinel node negative". Never null if nodal information present.
surgery_type: Look for "mastectomy", "wide local excision", "WLE", "lumpectomy", "wide excision", "segmentectomy", "axillary node clearance", "sentinel lymph node biopsy", "SLNB". Combine if multiple e.g. "WLE and SLNB".
margins_positive: true if "positive margins", "involved margins", "margins not clear", "R1". false if "clear margins", "negative margins", "margins clear", "R0".
lymphovascular_invasion: true if "LVI present", "lymphovascular invasion present/seen/identified". false if "LVI absent", "no lymphovascular invasion", "LVI not seen".
ductal_carcinoma_in_situ_present: true if "DCIS", "ductal carcinoma in situ" mentioned. false if explicitly stated absent.
multicentric: Extract as string. Look for "multicentric", "multifocal", "multiple foci". Return "yes", "no", or describe if present.
immunosuppression: Extract as string. Look for immunosuppressive drugs, transplant history, HIV, long-term steroids. Return "yes" with details or "no" if not mentioned.
long_distance: Extract as string. Look for travel distance, rurality, patient living far from treatment centre. Return "yes" with details or "no" if not mentioned.
histology: Extract full histological type e.g. "invasive ductal carcinoma", "invasive lobular carcinoma", "IDC", "ILC". Include grade if embedded in histology description.
IMPORTANT:
- Infer where clinically reasonable (e.g. "poorly differentiated" = grade 3)
- Never leave side null — use "not specified" as fallback
- Return ONLY the JSON object, nothing else
"""

def build_prompt(letter: str):
    return f"""
Extract the following fields and return ONLY JSON:

{{
    'patient_age': null,
    'disease_site': null,
    'side': null,
    'tumour_size_cm': null,
    'grade': null,
    'er_positive': null,
    'pr_positive': null,
    'her2_positive': null,
    'nodal_status': null,
    'surgery_type': null,
    'margins_positive': null,
    'lymphovascular_invasion': null,
    'ductal_carcinoma_in_situ_present': null,
    'multicentric': null,
    'immunosuppression': null,
    'long_distance': null,
    'histology': null
}}

Clinical letter:
\"\"\"
{letter}
\"\"\"
"""

def extract_structured_data(letter: str):
    response = ollama.chat(
        # model="llama3.2:1b",
        model="qwen2.5:3b",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_prompt(letter)}
        ],
        options={
            "temperature": 0,   # IMPORTANT for extraction
        }
    )

    raw_output = response["message"]["content"]

    # Attempt JSON parsing
    try:
        parsed = json.loads(raw_output)
        validated = OncologyLetter.model_validate(parsed)
        return validated
    except Exception as e:
        print("Parsing failed:", e)
        print("Raw output:", raw_output)
        return None

def recommend_radiotherapy(plan_data: dict):
    """
    Determines radiotherapy technique (3DCRT, PBI, VMAT)
    based on extracted oncology letter JSON.
    """

    # -----------------------------
    # Extract variables safely
    # -----------------------------
    age = plan_data.get("patient_age")
    disease_site = plan_data.get("disease_site")
    laterality = plan_data.get("side")
    tumour_size = plan_data.get("tumour_size_cm")
    grade = plan_data.get("grade")
    er = plan_data.get("er_positive")
    pr = plan_data.get("pr_positive")
    her2 = plan_data.get("her2_positive")
    nodal_status = plan_data.get("nodal_status")
    surgery_type = plan_data.get("surgery_type")
    margins_positive = plan_data.get("margins_positive")
    lvi = plan_data.get("lymphovascular_invasion")
    ductal_carcinoma_in_situ_present = plan_data.get("ductal_carcinoma_in_situ_present")
    multicentric = plan_data.get("multicentric")
    immunosuppression = plan_data.get("immunosuppression")
    try:
        histology = plan_data.get("histology")
    except:
        histology = plan_data.get("histology", {}).get("type", "").lower()

    # -----------------------------
    # Build clinical summary
    # -----------------------------
    summary = f"""
    Clinical Summary:
    -----------------
    Age: {age}
    Disease site: {disease_site}
    Laterality: {laterality}
    Tumour size: {tumour_size} cm
    Grade: {grade}
    ER+: {er}
    PR+: {pr}
    HER2+: {her2}
    Nodal status: {nodal_status}
    Surgery type: {surgery_type}
    Margins positive: {margins_positive}
    LVI present: {lvi}
    DCIS present: {ductal_carcinoma_in_situ_present}
    Immunosuppression: {immunosuppression}
    Multicentric: {multicentric}
    Histology: {histology}
    """

    # -----------------------------
    # Decision Logic
    # -----------------------------

    technique = None
    fractionation = None
    rationale = []
    special = []

    # ---- PBI ----
    if (
        tumour_size is not None and tumour_size <= 2
        and grade <= 2
        and nodal_status in [0, "N0", "pN0", None]
        and er is True
        and age is not None and age >= 40
    ):
        technique = "Partial Breast Irradiation (PBI)"

        fractionation = """
        Standard Prescription (UNC):
            - 600 cGy x 5 = 3000 cGy - QOD (every other day preferred/standard) (daily also acceptable but consider OPAR for daily)

        Also allowable:
            - 550 cGy x 5 = 2750 cGy - daily (OPAR) 
            - 270 cGy x 15 = 4050 cGy - daily (Import Low) 
        """

        rationale.append(
            " PBI is preferred over whole breast RT for most patients with early stage breast cancer who are considered candidates according to the ASTRO PBI guideline (Grade 1-2, ER-positive histology, age ≥40 years, tumor size ≤2 cm, pN0), " \
            "recognizing whole breast RT may be appropriate at MD discretion and through shared decision-making. "
        )
        rationale.append(
            "PBI can be considered for other cases per ASTRO guideline and MD discretion. In patients over 65 who are cN0, PBI is appropriate when SLNB is omitted.  " \
            "In patients 50-65 who do not have SLNB, most patients should have whole breast RT and PBI can be considered on a case-by-case basis. "
        )

    # ---- VMAT ----
    elif (
        laterality in ["left"]
    ):
        technique = "Whole Breast VMAT"

        fractionation = """
        Whole Breast/Chest Wall ± Nodes:
            - 266 cGy x 16 = 4256 cGy
            Sequential boost: 1000–2000 cGy
        OR
            - 200 cGy x 25 = 5000 cGy
            Sequential boost: 1000–2000 cGy

        Moderate Hypofractionation with SIB (RTOG-1005):
            - PTV_High: 320 cGy x 15 = 4800 cGy
            - PTV_Low:  267 cGy x 15 = 4005 cGy
        """

        rationale.append(
            "VMAT can be considered in cases where, due to cardiac position, 3D plans would require beams passing directly through the heart or " \
            "where dose objectives cannot be met with 3D planning, or where patient setup requires IMRT. "
        )
        rationale.append(
            " The other scenario for VMAT is the case of an integrated boost which may be offered to patients who require a boost and will benefit from a shorter course of treatment. "
        )

    # ---- 3DCRT ----
    else:
        technique = "Whole Breast 3D Conformal Radiotherapy (3DCRT)"

        fractionation = """
        Whole Breast Only (No Nodes): Moderate hypofractionation :
            - Initial tangent dose: 266 cGy x 16 = 4256 cGy 
            - Tumor bed boost dose: 250 cGy x 4 = 1000 cGy 
            - Total dose = 5256 cGy  
        """

        rationale.append(
            "For most cases of whole breast treatment without nodal irradiation, 3D conformal technique is preferred. "
        )
        rationale.append(
            "For most cases of whole breast treatment, moderate hypofractionation is the preferred fractionation schedule. "
        )

    # -----------------------------
    # Special Considerations
    # -----------------------------
    if age is not None and age < 40:
        special.append("Young age – consider conventional fractionation.")

    if her2:
        special.append("HER2 positive – ensure systemic therapy coordination.")

    if lvi:
        special.append("Lymphovascular invasion present – consider nodal irradiation.")

    if margins_positive:
        special.append("Positive margins – boost strongly recommended.")

    # -----------------------------
    # Output
    # -----------------------------
    print(summary)
    print("\nRecommended Technique:")
    print("----------------------")
    print(technique)

    print("\nFractionation:")
    print("--------------")
    print(fractionation)

    print("\nRationale:")
    print("----------")
    for r in rationale:
        print(f"- {r}")

    if special:
        print("\nSpecial Considerations:")
        print("----------------------")
        for s in special:
            print(f"- {s}")

    print("\n--------------------------------------------------\n")

if __name__ == "__main__":
    
    letter = input("Enter clinical letter, or press <Enter> to use template letter: ")

    if letter == "":
        # Use template letter
        letter = """
            Patient is a 62-year-old female with left breast cancer. 
            She underwent lumpectomy surgery for a 1.8 cm tumor. 
            Pathology shows Grade 2 invasive ductal carcinoma, ER positive, PR positive, HER2 negative. 
            Margins are negative. Sentinel lymph node biopsy is negative (pN0). 
            No lymphovascular invasion. Patient is otherwise healthy with no comorbidities.
        """

    result = extract_structured_data(letter)
    print(result.model_dump())
    recommend_radiotherapy(result.model_dump())