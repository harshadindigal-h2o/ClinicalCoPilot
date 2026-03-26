from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv

load_dotenv()

_H2OGPTE_ADDRESS = os.getenv("H2OGPTE_ADDRESS", "https://h2ogpte.genai.h2o.ai")
_H2OGPTE_API_KEY = os.getenv("H2OGPTE_API_KEY", "")

_client = None


def get_client():
    global _client
    if _client is None:
        from h2ogpte import H2OGPTE
        _client = H2OGPTE(address=_H2OGPTE_ADDRESS, api_key=_H2OGPTE_API_KEY)
    return _client


# ── Guided JSON schemas ───────────────────────────────────────────────────────

_TRANSCRIPT_SCHEMA = {
    "type": "object",
    "properties": {
        "transcript": {"type": "string"},
    },
    "required": ["transcript"],
}

_CLINICAL_SCHEMA = {
    "type": "object",
    "properties": {
        "symptoms": {"type": "array", "items": {"type": "string"}},
        "duration": {"type": "string"},
        "vitals": {"type": "object", "additionalProperties": {"type": "string"}},
        "medications": {"type": "array", "items": {"type": "string"}},
        "diagnosis": {"type": "string"},
    },
    "required": ["symptoms", "vitals", "medications"],
}

_BILLING_SCHEMA = {
    "type": "object",
    "properties": {
        "icd10": {"type": "array", "items": {"type": "string"}},
        "cpt": {"type": "array", "items": {"type": "string"}},
        "rationale": {"type": "string"},
        "confidence": {"type": "number"},
    },
    "required": ["icd10", "cpt"],
}

_RISK_SCHEMA = {
    "type": "object",
    "properties": {
        "high_risk_conditions": {"type": "array", "items": {"type": "string"}},
        "follow_up_recommendations": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["high_risk_conditions", "follow_up_recommendations"],
}

_SOAP_SCHEMA = {
    "type": "object",
    "properties": {
        "subjective": {"type": "string"},
        "objective": {"type": "string"},
        "assessment": {"type": "string"},
        "plan": {"type": "string"},
    },
    "required": ["subjective", "objective", "assessment", "plan"],
}


# ── Collection management ─────────────────────────────────────────────────────

def ingest_file(filepath: Path, filename: str) -> str:
    """Upload and ingest a file (.txt or .wav) into H2O GPTe.

    H2O GPTe natively handles both text and audio formats — no external
    transcription library needed. Returns the collection_id.
    """
    client = get_client()
    collection_id = client.create_collection(
        name=f"clinical_note_{filename}",
        description=f"Clinical documentation: {filename}",
    )
    with open(filepath, "rb") as f:
        upload_id = client.upload(filename, f)
    client.ingest_uploads(collection_id, [upload_id])
    return collection_id


def delete_collection(collection_id: str) -> None:
    """Delete a collection to clean up after switching files."""
    try:
        get_client().delete_collections([collection_id])
    except Exception:
        pass


# ── Core query helper ─────────────────────────────────────────────────────────

def _query_once(
    collection_id: str,
    prompt: str,
    guided_json: Optional[Dict] = None,
    max_retries: int = 3,
) -> str:
    """Open a fresh RAG chat session, run one query, return raw content."""
    client = get_client()
    for attempt in range(max_retries):
        try:
            chat_session_id = client.create_chat_session(collection_id)
            llm_args: Dict[str, Any] = {
                "temperature": 0.1,
                "max_new_tokens": 2048,
            }
            if guided_json:
                llm_args["response_format"] = "json_object"
                llm_args["guided_json"] = guided_json
            with client.connect(chat_session_id) as session:
                reply = session.query(
                    prompt,
                    llm="auto",
                    llm_args=llm_args,
                    timeout=120,
                )
            return reply.content
        except Exception as exc:
            if attempt == max_retries - 1:
                raise RuntimeError(
                    f"H2O GPTe query failed after {max_retries} attempts: {exc}"
                ) from exc
            time.sleep(2 ** attempt)
    return ""


def _parse_json(raw: str) -> Dict[str, Any]:
    """Strip markdown fences and parse JSON, with empty-dict fallback."""
    raw = raw.strip()
    if raw.startswith("```"):
        lines = [l for l in raw.split("\n") if not l.strip().startswith("```")]
        raw = "\n".join(lines).strip()
    start, end = raw.find("{"), raw.rfind("}")
    if start != -1 and end != -1:
        try:
            return json.loads(raw[start : end + 1])
        except json.JSONDecodeError:
            pass
    return {}


# ── Public extraction API ─────────────────────────────────────────────────────

def get_transcript(collection_id: str) -> str:
    """Retrieve a plain-text transcript from an ingested audio file."""
    raw = _query_once(
        collection_id,
        "Transcribe the full audio content verbatim as plain text.",
        guided_json=_TRANSCRIPT_SCHEMA,
    )
    result = _parse_json(raw)
    return result.get("transcript", raw)


def extract_clinical_data(collection_id: str) -> Dict[str, Any]:
    raw = _query_once(
        collection_id,
        "Extract all clinical data from this document: symptoms, duration, "
        "vitals, medications, and primary diagnosis.",
        guided_json=_CLINICAL_SCHEMA,
    )
    return _parse_json(raw)


def generate_billing_codes(collection_id: str) -> Dict[str, Any]:
    raw = _query_once(
        collection_id,
        "Generate appropriate ICD-10 diagnosis codes and CPT procedure codes "
        "for this clinical encounter. Include rationale and a confidence score "
        "between 0.0 and 1.0.",
        guided_json=_BILLING_SCHEMA,
    )
    return _parse_json(raw)


def analyze_risk_flags(collection_id: str) -> Dict[str, Any]:
    raw = _query_once(
        collection_id,
        "Identify all high-risk medical conditions and provide specific "
        "follow-up recommendations based on this clinical note.",
        guided_json=_RISK_SCHEMA,
    )
    return _parse_json(raw)


def generate_soap_note(collection_id: str) -> Dict[str, Any]:
    raw = _query_once(
        collection_id,
        "Generate a structured SOAP note (Subjective, Objective, Assessment, "
        "Plan) from this clinical document.",
        guided_json=_SOAP_SCHEMA,
    )
    return _parse_json(raw)
