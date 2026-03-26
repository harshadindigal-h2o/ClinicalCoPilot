from __future__ import annotations

import json
from typing import Any, Dict, List

import reflex as rx
from pydantic import ValidationError

from .file_loader import get_available_files, read_text_file, file_path
from .models import ClinicalData, BillingCodes, RiskFlags, SOAPNote
from .llm_client import (
    ingest_file,
    delete_collection,
    get_transcript,
    extract_clinical_data,
    generate_billing_codes,
    analyze_risk_flags,
    generate_soap_note,
)
from .fhir_mapper import build_fhir_bundle


class AppState(rx.State):
    # ── File selection ────────────────────────────────────────────────────────
    available_files: List[str] = []
    selected_file: str = ""
    raw_text: str = ""

    # ── H2O GPTe collection for the currently loaded file ────────────────────
    collection_id: str = ""

    # ── Processing flags ──────────────────────────────────────────────────────
    is_loading: bool = False
    is_ingesting: bool = False
    is_extracting: bool = False
    is_billing: bool = False
    is_risk: bool = False
    is_soap: bool = False
    is_fhir: bool = False
    error_message: str = ""
    success_message: str = ""

    # ── Outputs (stored as JSON strings for editability) ──────────────────────
    clinical_data_json: str = "{}"
    billing_json: str = "{}"
    risk_json: str = "{}"
    soap_json: str = "{}"
    fhir_json: str = "{}"

    # ── UI ────────────────────────────────────────────────────────────────────
    active_tab: str = "clinical"

    # ── File management ───────────────────────────────────────────────────────
    def load_files(self):
        self.available_files = get_available_files()
        if self.available_files:
            self.selected_file = self.available_files[0]
        self.error_message = ""
        self.success_message = f"Found {len(self.available_files)} file(s)."

    def set_selected_file(self, filename: str):
        # Clean up previous H2O GPTe collection
        if self.collection_id:
            delete_collection(self.collection_id)
            self.collection_id = ""
        self.selected_file = filename
        self.raw_text = ""
        self._clear_outputs()

    def _clear_outputs(self):
        self.clinical_data_json = "{}"
        self.billing_json = "{}"
        self.risk_json = "{}"
        self.soap_json = "{}"
        self.fhir_json = "{}"
        self.error_message = ""
        self.success_message = ""

    # ── File ingestion ────────────────────────────────────────────────────────
    def load_file_content(self):
        """Upload the selected file to H2O GPTe and ingest it.

        H2O GPTe natively supports both .txt and .wav — no external
        transcription step needed. For .txt files we also read the content
        locally so the raw note is visible in the editor.
        """
        if not self.selected_file:
            self.error_message = "No file selected."
            return

        # Clean up any previous collection for this session
        if self.collection_id:
            delete_collection(self.collection_id)
            self.collection_id = ""

        self.is_ingesting = True
        self.error_message = ""
        self.success_message = ""
        yield

        try:
            fp = file_path(self.selected_file)

            # Ingest into H2O GPTe (handles .txt and .wav natively)
            self.collection_id = ingest_file(fp, self.selected_file)

            if self.selected_file.lower().endswith(".wav"):
                # Retrieve transcript from H2O GPTe for display
                self.raw_text = get_transcript(self.collection_id)
                self.success_message = "Audio ingested and transcribed via H2O GPTe."
            else:
                # Read text locally for the editor panel
                self.raw_text = read_text_file(self.selected_file)
                self.success_message = "File ingested into H2O GPTe."

        except Exception as e:
            self.error_message = f"Ingestion failed: {e}"
        finally:
            self.is_ingesting = False

    # ── Full pipeline ─────────────────────────────────────────────────────────
    def process_note(self):
        if not self.collection_id:
            self.error_message = "Load a file first."
            return
        self._clear_outputs()
        self.is_loading = True
        yield

        try:
            # Step 1: Clinical extraction
            self.is_extracting = True
            yield
            clinical_raw = extract_clinical_data(self.collection_id)
            try:
                ClinicalData(**clinical_raw)
            except ValidationError:
                pass
            self.clinical_data_json = json.dumps(clinical_raw, indent=2)
            self.is_extracting = False
            yield

            # Step 2: Billing codes
            self.is_billing = True
            yield
            billing_raw = generate_billing_codes(self.collection_id)
            try:
                BillingCodes(**billing_raw)
            except ValidationError:
                pass
            self.billing_json = json.dumps(billing_raw, indent=2)
            self.is_billing = False
            yield

            # Step 3: Risk flags
            self.is_risk = True
            yield
            risk_raw = analyze_risk_flags(self.collection_id)
            try:
                RiskFlags(**risk_raw)
            except ValidationError:
                pass
            self.risk_json = json.dumps(risk_raw, indent=2)
            self.is_risk = False
            yield

            # Step 4: SOAP note
            self.is_soap = True
            yield
            soap_raw = generate_soap_note(self.collection_id)
            try:
                SOAPNote(**soap_raw)
            except ValidationError:
                pass
            self.soap_json = json.dumps(soap_raw, indent=2)
            self.is_soap = False
            yield

            # Step 5: FHIR bundle (local, no LLM call)
            self.is_fhir = True
            yield
            fhir_bundle = build_fhir_bundle(clinical_raw, billing_raw, risk_raw)
            self.fhir_json = json.dumps(fhir_bundle, indent=2)
            self.is_fhir = False
            yield

            self.success_message = "Processing complete."

        except Exception as e:
            self.error_message = f"Processing error: {e}"
        finally:
            self.is_loading = False
            self.is_extracting = False
            self.is_billing = False
            self.is_risk = False
            self.is_soap = False
            self.is_fhir = False

    # ── Individual regeneration ───────────────────────────────────────────────
    def regenerate_clinical(self):
        if not self.collection_id:
            self.error_message = "Load a file first."
            return
        self.is_extracting = True
        yield
        try:
            raw = extract_clinical_data(self.collection_id)
            self.clinical_data_json = json.dumps(raw, indent=2)
            self.success_message = "Clinical data regenerated."
        except Exception as e:
            self.error_message = f"Error: {e}"
        finally:
            self.is_extracting = False

    def regenerate_billing(self):
        if not self.collection_id:
            self.error_message = "Load a file first."
            return
        self.is_billing = True
        yield
        try:
            raw = generate_billing_codes(self.collection_id)
            self.billing_json = json.dumps(raw, indent=2)
            self.success_message = "Billing codes regenerated."
        except Exception as e:
            self.error_message = f"Error: {e}"
        finally:
            self.is_billing = False

    def regenerate_risk(self):
        if not self.collection_id:
            self.error_message = "Load a file first."
            return
        self.is_risk = True
        yield
        try:
            raw = analyze_risk_flags(self.collection_id)
            self.risk_json = json.dumps(raw, indent=2)
            self.success_message = "Risk flags regenerated."
        except Exception as e:
            self.error_message = f"Error: {e}"
        finally:
            self.is_risk = False

    def regenerate_soap(self):
        if not self.collection_id:
            self.error_message = "Load a file first."
            return
        self.is_soap = True
        yield
        try:
            raw = generate_soap_note(self.collection_id)
            self.soap_json = json.dumps(raw, indent=2)
            self.success_message = "SOAP note regenerated."
        except Exception as e:
            self.error_message = f"Error: {e}"
        finally:
            self.is_soap = False

    def regenerate_fhir(self):
        self.is_fhir = True
        yield
        try:
            clinical = json.loads(self.clinical_data_json or "{}")
            billing = json.loads(self.billing_json or "{}")
            risk = json.loads(self.risk_json or "{}")
            fhir_bundle = build_fhir_bundle(clinical, billing, risk)
            self.fhir_json = json.dumps(fhir_bundle, indent=2)
            self.success_message = "FHIR bundle regenerated."
        except Exception as e:
            self.error_message = f"Error: {e}"
        finally:
            self.is_fhir = False

    # ── Inline edits ──────────────────────────────────────────────────────────
    def set_raw_text(self, value: str):
        self.raw_text = value

    def set_clinical_data_json(self, value: str):
        self.clinical_data_json = value

    def set_billing_json(self, value: str):
        self.billing_json = value

    def set_risk_json(self, value: str):
        self.risk_json = value

    def set_soap_json(self, value: str):
        self.soap_json = value

    def set_active_tab(self, tab: str):
        self.active_tab = tab

    # ── Export ────────────────────────────────────────────────────────────────
    @rx.var
    def export_payload(self) -> str:
        import json as _json
        try:
            return _json.dumps(
                {
                    "raw_text": self.raw_text,
                    "clinical_data": _json.loads(self.clinical_data_json or "{}"),
                    "billing_codes": _json.loads(self.billing_json or "{}"),
                    "risk_flags": _json.loads(self.risk_json or "{}"),
                    "soap_note": _json.loads(self.soap_json or "{}"),
                    "fhir_bundle": _json.loads(self.fhir_json or "{}"),
                },
                indent=2,
            )
        except Exception:
            return "{}"

    def download_export(self):
        return rx.download(
            data=self.export_payload,
            filename="clinical_copilot_export.json",
        )

    @rx.var
    def processing_status(self) -> str:
        if self.is_ingesting:
            return "Uploading & ingesting into H2O GPTe..."
        if self.is_extracting:
            return "Extracting clinical data..."
        if self.is_billing:
            return "Generating billing codes..."
        if self.is_risk:
            return "Analyzing risk flags..."
        if self.is_soap:
            return "Generating SOAP note..."
        if self.is_fhir:
            return "Building FHIR bundle..."
        if self.is_loading:
            return "Processing..."
        return ""

    @rx.var
    def file_is_ready(self) -> bool:
        return self.collection_id != ""
