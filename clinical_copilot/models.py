from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class ClinicalData(BaseModel):
    symptoms: List[str] = Field(default_factory=list)
    duration: Optional[str] = None
    vitals: Dict[str, str] = Field(default_factory=dict)
    medications: List[str] = Field(default_factory=list)
    diagnosis: Optional[str] = None


class BillingCodes(BaseModel):
    icd10: List[str] = Field(default_factory=list)
    cpt: List[str] = Field(default_factory=list)
    rationale: Optional[str] = None
    confidence: Optional[float] = None


class RiskFlags(BaseModel):
    high_risk_conditions: List[str] = Field(default_factory=list)
    follow_up_recommendations: List[str] = Field(default_factory=list)


class SOAPNote(BaseModel):
    subjective: str = ""
    objective: str = ""
    assessment: str = ""
    plan: str = ""


class ProcessingResult(BaseModel):
    raw_text: str = ""
    clinical_data: ClinicalData = Field(default_factory=ClinicalData)
    billing_codes: BillingCodes = Field(default_factory=BillingCodes)
    risk_flags: RiskFlags = Field(default_factory=RiskFlags)
    soap_note: SOAPNote = Field(default_factory=SOAPNote)
    fhir_output: Dict[str, Any] = Field(default_factory=dict)
