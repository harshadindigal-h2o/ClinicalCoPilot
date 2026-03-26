# ClinicalCoPilot

A full-stack Clinical Documentation AI web application

ClinicalCoPilot ingests clinical notes and audio recordings, then usesa RAG pipeline to automatically extract structured clinical data, generate SOAP notes, produce ICD-10/CPT billing codes, flag patient risks, and output FHIR R4-compliant JSON bundles — all within an interactive, editable UI.

---

## Features

| Capability | Description |
|---|---|
| **File Ingestion** | Uploads `.txt` and `.wav` files natively into H2O GPTe (no external transcription needed) |
| **Clinical Extraction** | Symptoms, vitals, medications, diagnosis — extracted via guided JSON schema |
| **SOAP Notes** | Auto-generated Subjective / Objective / Assessment / Plan |
| **Billing Codes** | ICD-10 and CPT codes with rationale and confidence score |
| **Risk Flags** | High-risk conditions and follow-up recommendations |
| **FHIR R4 Bundle** | Condition, Observation, MedicationRequest, Encounter, ClinicalImpression resources |
| **Editable Outputs** | All outputs are editable in-place with per-section regeneration |
| **Export** | Download full JSON payload with one click |

---

## Tech Stack

- **Frontend + Backend**: [Reflex](https://reflex.dev) (Python full-stack)
- **LLM + RAG**: [H2O GPTe](https://h2o.ai/platform/h2ogpte/) — upload, ingest, and query with `guided_json` structured output
- **Data Validation**: Pydantic v2
- **FHIR Mapping**: Custom FHIR R4 builder (no external library)

---

## Project Structure

```
clinical_copilot/
├── rxconfig.py                        # Reflex config
├── requirements.txt                   # Dependencies
├── .env.example                       # Credentials template
└── clinical_copilot/
    ├── clinical_copilot.py            # UI (two-panel layout with tabs)
    ├── state.py                       # Reflex state + full processing pipeline
    ├── models.py                      # Pydantic schemas
    ├── llm_client.py                  # H2O GPTe client (ingest + guided JSON queries)
    ├── fhir_mapper.py                 # FHIR R4 Bundle builder
    └── file_loader.py                 # Local filesystem scanner
```

---

## Setup

### 1. Prerequisites

- Python 3.11+
- An H2O GPTe instance with API access

### 2. Clone & install

```bash
git clone https://github.com/harshadindigal-h2o/ClinicalCoPilot.git
cd ClinicalCoPilot
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure credentials

```bash
cp .env.example .env
```

Edit `.env`:

```env
H2OGPTE_ADDRESS=https://your-h2ogpte-instance.h2o.ai
H2OGPTE_API_KEY=your_api_key_here
DATA_DIR=/path/to/your/clinical/notes
```

### 4. Run

```bash
reflex init   # first time only
reflex run
```

Open **http://localhost:3000**

---

## Workflow

```
Select file → Ingest File → Process All
                  ↓               ↓
          Uploads to H2O    1. Clinical Extraction
          GPTe collection   2. Billing Codes
          (txt or wav)      3. Risk Flags
                            4. SOAP Note
                            5. FHIR R4 Bundle
```

1. **Scan Files** — discovers `.txt` and `.wav` files from your configured `DATA_DIR`
2. **Ingest File** — uploads the file to H2O GPTe; audio is transcribed natively
3. **Process All** — runs all 5 extractions sequentially with live status updates
4. Edit any output in-place, or hit **Regenerate** per section
5. **Download JSON** — exports the complete result as a single JSON file

---

## Data Source

By default, the app reads from `~/Desktop/autonomize_demo_data`. Override with the `DATA_DIR` environment variable.

Supported formats: `.txt`, `.wav`

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `H2OGPTE_ADDRESS` | H2O GPTe server URL | `https://h2ogpte.genai.h2o.ai` |
| `H2OGPTE_API_KEY` | H2O GPTe API key | *(required)* |
| `H2OGPTE_LLM` | LLM name (leave blank for auto-select) | auto |
| `DATA_DIR` | Path to clinical notes directory | `~/Desktop/autonomize_demo_data` |

---

## License

MIT
