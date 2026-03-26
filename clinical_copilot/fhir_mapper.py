from __future__ import annotations
from typing import Any, Dict, List


def _condition_resource(diagnosis: str) -> Dict[str, Any]:
    return {
        "resourceType": "Condition",
        "id": "condition-1",
        "clinicalStatus": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                    "code": "active",
                }
            ]
        },
        "code": {"text": diagnosis},
        "subject": {"reference": "Patient/unknown"},
    }


def _observation_resources(vitals: Dict[str, str]) -> List[Dict[str, Any]]:
    resources = []
    loinc_map = {
        "bp": ("55284-4", "Blood Pressure"),
        "blood pressure": ("55284-4", "Blood Pressure"),
        "hr": ("8867-4", "Heart Rate"),
        "heart rate": ("8867-4", "Heart Rate"),
        "pulse": ("8867-4", "Heart Rate"),
        "temp": ("8310-5", "Body Temperature"),
        "temperature": ("8310-5", "Body Temperature"),
        "rr": ("9279-1", "Respiratory Rate"),
        "respiratory rate": ("9279-1", "Respiratory Rate"),
        "spo2": ("59408-5", "Oxygen Saturation"),
        "weight": ("29463-7", "Body Weight"),
        "bmi": ("39156-5", "Body Mass Index"),
    }
    for i, (key, val) in enumerate(vitals.items()):
        key_lower = key.lower()
        loinc_code, display = loinc_map.get(key_lower, ("vital-sign", key))
        resources.append(
            {
                "resourceType": "Observation",
                "id": f"observation-{i + 1}",
                "status": "final",
                "category": [
                    {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                "code": "vital-signs",
                            }
                        ]
                    }
                ],
                "code": {
                    "coding": [
                        {
                            "system": "http://loinc.org",
                            "code": loinc_code,
                            "display": display,
                        }
                    ],
                    "text": key,
                },
                "valueString": val,
                "subject": {"reference": "Patient/unknown"},
            }
        )
    return resources


def _medication_request_resources(medications: List[str]) -> List[Dict[str, Any]]:
    resources = []
    for i, med in enumerate(medications):
        resources.append(
            {
                "resourceType": "MedicationRequest",
                "id": f"med-request-{i + 1}",
                "status": "active",
                "intent": "order",
                "medicationCodeableConcept": {"text": med},
                "subject": {"reference": "Patient/unknown"},
            }
        )
    return resources


def _encounter_resource(billing: Dict[str, Any]) -> Dict[str, Any]:
    icd10 = billing.get("icd10", [])
    cpt = billing.get("cpt", [])
    reason_codes = [{"text": code} for code in icd10]
    type_codes = [{"text": code} for code in cpt]
    return {
        "resourceType": "Encounter",
        "id": "encounter-1",
        "status": "finished",
        "class": {
            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
            "code": "AMB",
            "display": "ambulatory",
        },
        "type": type_codes if type_codes else [{"text": "Office Visit"}],
        "reasonCode": reason_codes,
        "subject": {"reference": "Patient/unknown"},
    }


def build_fhir_bundle(
    clinical_data: Dict[str, Any],
    billing_codes: Dict[str, Any],
    risk_flags: Dict[str, Any],
) -> Dict[str, Any]:
    entries = []

    diagnosis = clinical_data.get("diagnosis")
    if diagnosis:
        entries.append({"resource": _condition_resource(diagnosis)})

    vitals = clinical_data.get("vitals", {})
    if vitals:
        for obs in _observation_resources(vitals):
            entries.append({"resource": obs})

    medications = clinical_data.get("medications", [])
    if medications:
        for med in _medication_request_resources(medications):
            entries.append({"resource": med})

    entries.append({"resource": _encounter_resource(billing_codes)})

    # Risk flags as a ClinicalImpression resource
    high_risk = risk_flags.get("high_risk_conditions", [])
    follow_ups = risk_flags.get("follow_up_recommendations", [])
    if high_risk or follow_ups:
        entries.append(
            {
                "resource": {
                    "resourceType": "ClinicalImpression",
                    "id": "clinical-impression-1",
                    "status": "completed",
                    "subject": {"reference": "Patient/unknown"},
                    "summary": "; ".join(high_risk),
                    "note": [{"text": rec} for rec in follow_ups],
                }
            }
        )

    return {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": entries,
    }
