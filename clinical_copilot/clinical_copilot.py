from __future__ import annotations

import reflex as rx

from .state import AppState

# ── Color palette ─────────────────────────────────────────────────────────────
BLUE = "#2563EB"
BLUE_LIGHT = "#EFF6FF"
DARK = "#111827"
GRAY = "#6B7280"
GRAY_LIGHT = "#F9FAFB"
GREEN = "#059669"
RED = "#DC2626"
BORDER = "#E5E7EB"
WHITE = "#FFFFFF"


# ── Reusable helpers ──────────────────────────────────────────────────────────

def section_header(title: str) -> rx.Component:
    return rx.text(
        title,
        font_size="0.75rem",
        font_weight="600",
        color=GRAY,
        text_transform="uppercase",
        letter_spacing="0.05em",
        margin_bottom="0.5rem",
    )


def action_button(
    label: str,
    on_click,
    color: str = BLUE,
    is_loading: bool = False,
    disabled: bool = False,
) -> rx.Component:
    return rx.button(
        label,
        on_click=on_click,
        background_color=color,
        color=WHITE,
        font_size="0.8rem",
        font_weight="600",
        padding="0.4rem 0.9rem",
        border_radius="6px",
        cursor="pointer",
        _hover={"opacity": "0.85"},
        loading=is_loading,
        disabled=disabled,
    )


def regen_button(label: str, on_click, is_loading: bool = False) -> rx.Component:
    return rx.button(
        label,
        on_click=on_click,
        background_color=WHITE,
        color=BLUE,
        border=f"1.5px solid {BLUE}",
        font_size="0.75rem",
        font_weight="600",
        padding="0.3rem 0.75rem",
        border_radius="6px",
        cursor="pointer",
        _hover={"background_color": BLUE_LIGHT},
        loading=is_loading,
    )


def json_textarea(value: str, on_change, height: str = "340px") -> rx.Component:
    return rx.text_area(
        value=value,
        on_change=on_change,
        font_family="monospace",
        font_size="0.78rem",
        background_color=GRAY_LIGHT,
        border=f"1px solid {BORDER}",
        border_radius="6px",
        padding="0.75rem",
        height=height,
        width="100%",
        resize="vertical",
    )


def readonly_json(value: str, height: str = "340px") -> rx.Component:
    return rx.text_area(
        value=value,
        font_family="monospace",
        font_size="0.78rem",
        background_color="#F0FDF4",
        border=f"1px solid {BORDER}",
        border_radius="6px",
        padding="0.75rem",
        height=height,
        width="100%",
        read_only=True,
        resize="vertical",
    )


# ── Left panel ────────────────────────────────────────────────────────────────

def left_panel() -> rx.Component:
    return rx.vstack(
        # Header
        rx.vstack(
            rx.text(
                "Clinical Copilot",
                font_size="1.25rem",
                font_weight="700",
                color=DARK,
            ),
            rx.text("Powered by Autonomize AI", font_size="0.75rem", color=GRAY),
            align_items="start",
            spacing="1",
            margin_bottom="1.5rem",
        ),

        # File management section
        rx.vstack(
            section_header("Data Source"),
            action_button("Scan Files", AppState.load_files, color="#4F46E5"),
            align_items="start",
            width="100%",
            spacing="2",
        ),

        rx.vstack(
            section_header("Select File"),
            rx.select(
                AppState.available_files,
                value=AppState.selected_file,
                on_change=AppState.set_selected_file,
                width="100%",
            ),
            rx.hstack(
                action_button(
                    "Ingest File",
                    AppState.load_file_content,
                    is_loading=AppState.is_ingesting,
                ),
                action_button(
                    "Process All",
                    AppState.process_note,
                    color=GREEN,
                    is_loading=AppState.is_loading,
                    disabled=~AppState.file_is_ready,
                ),
                spacing="2",
            ),
            align_items="start",
            width="100%",
            spacing="2",
        ),

        # Status messages
        rx.cond(
            AppState.processing_status != "",
            rx.hstack(
                rx.spinner(size="2"),
                rx.text(
                    AppState.processing_status,
                    font_size="0.8rem",
                    color=BLUE,
                ),
                spacing="2",
            ),
            rx.fragment(),
        ),
        rx.cond(
            AppState.error_message != "",
            rx.text(AppState.error_message, color=RED, font_size="0.8rem"),
            rx.fragment(),
        ),
        rx.cond(
            AppState.success_message != "",
            rx.text(AppState.success_message, color=GREEN, font_size="0.8rem"),
            rx.fragment(),
        ),

        # Raw note editor
        rx.vstack(
            section_header("Raw Note / Transcript"),
            rx.text_area(
                value=AppState.raw_text,
                on_change=AppState.set_raw_text,
                placeholder="Load a file or paste clinical note here...",
                font_size="0.8rem",
                height="280px",
                border=f"1px solid {BORDER}",
                border_radius="6px",
                padding="0.75rem",
                background_color=WHITE,
                width="100%",
                resize="vertical",
            ),
            align_items="start",
            width="100%",
            spacing="2",
        ),

        align_items="start",
        width="280px",
        min_width="280px",
        height="100vh",
        overflow_y="auto",
        background_color=GRAY_LIGHT,
        border_right=f"1px solid {BORDER}",
        padding="1.5rem",
        spacing="4",
    )


# ── Tab contents ──────────────────────────────────────────────────────────────

def clinical_tab() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text(
                "Clinical Data Extraction",
                font_size="1rem",
                font_weight="600",
                color=DARK,
            ),
            rx.spacer(),
            regen_button(
                "Regenerate",
                AppState.regenerate_clinical,
                is_loading=AppState.is_extracting,
            ),
            width="100%",
            align_items="center",
        ),
        rx.text(
            "Edit extracted clinical data below. Changes are saved automatically.",
            font_size="0.8rem",
            color=GRAY,
        ),
        json_textarea(AppState.clinical_data_json, AppState.set_clinical_data_json),
        align_items="start",
        width="100%",
        spacing="3",
        padding="1.5rem",
    )


def billing_tab() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text(
                "Billing Codes (ICD-10 / CPT)",
                font_size="1rem",
                font_weight="600",
                color=DARK,
            ),
            rx.spacer(),
            regen_button(
                "Regenerate",
                AppState.regenerate_billing,
                is_loading=AppState.is_billing,
            ),
            width="100%",
            align_items="center",
        ),
        rx.text(
            "Review and edit ICD-10 and CPT codes with rationale and confidence score.",
            font_size="0.8rem",
            color=GRAY,
        ),
        json_textarea(AppState.billing_json, AppState.set_billing_json),
        align_items="start",
        width="100%",
        spacing="3",
        padding="1.5rem",
    )


def soap_tab() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text(
                "SOAP Note",
                font_size="1rem",
                font_weight="600",
                color=DARK,
            ),
            rx.spacer(),
            regen_button(
                "Regenerate",
                AppState.regenerate_soap,
                is_loading=AppState.is_soap,
            ),
            width="100%",
            align_items="center",
        ),
        rx.text(
            "Edit the generated SOAP note sections. Saved as JSON with "
            "Subjective / Objective / Assessment / Plan keys.",
            font_size="0.8rem",
            color=GRAY,
        ),
        json_textarea(AppState.soap_json, AppState.set_soap_json, height="400px"),
        align_items="start",
        width="100%",
        spacing="3",
        padding="1.5rem",
    )


def fhir_tab() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text(
                "FHIR R4 Bundle",
                font_size="1rem",
                font_weight="600",
                color=DARK,
            ),
            rx.spacer(),
            regen_button(
                "Rebuild Bundle",
                AppState.regenerate_fhir,
                is_loading=AppState.is_fhir,
            ),
            width="100%",
            align_items="center",
        ),
        rx.text(
            "Read-only FHIR R4 Bundle generated from clinical data, vitals, "
            "medications, and billing codes.",
            font_size="0.8rem",
            color=GRAY,
        ),
        readonly_json(AppState.fhir_json, height="400px"),
        align_items="start",
        width="100%",
        spacing="3",
        padding="1.5rem",
    )


def risk_tab() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text(
                "Risk Flags & Follow-Up",
                font_size="1rem",
                font_weight="600",
                color=DARK,
            ),
            rx.spacer(),
            regen_button(
                "Regenerate",
                AppState.regenerate_risk,
                is_loading=AppState.is_risk,
            ),
            width="100%",
            align_items="center",
        ),
        rx.text(
            "High-risk conditions and follow-up recommendations identified by the AI.",
            font_size="0.8rem",
            color=GRAY,
        ),
        readonly_json(AppState.risk_json, height="340px"),
        align_items="start",
        width="100%",
        spacing="3",
        padding="1.5rem",
    )


# ── Right panel ───────────────────────────────────────────────────────────────

def right_panel() -> rx.Component:
    return rx.vstack(
        # Top bar with export
        rx.hstack(
            rx.text(
                "Output Workspace",
                font_size="1rem",
                font_weight="600",
                color=DARK,
            ),
            rx.spacer(),
            rx.button(
                "Download JSON",
                on_click=AppState.download_export,
                background_color=WHITE,
                color=DARK,
                border=f"1px solid {BORDER}",
                font_size="0.8rem",
                font_weight="600",
                padding="0.4rem 0.9rem",
                border_radius="6px",
                cursor="pointer",
                _hover={"background_color": GRAY_LIGHT},
            ),
            width="100%",
            align_items="center",
            padding="1rem 1.5rem",
            border_bottom=f"1px solid {BORDER}",
            background_color=WHITE,
        ),

        # Tabs
        rx.tabs.root(
            rx.tabs.list(
                rx.tabs.trigger(
                    "Clinical Data",
                    value="clinical",
                    font_size="0.85rem",
                    font_weight="500",
                    padding="0.5rem 1rem",
                ),
                rx.tabs.trigger(
                    "Billing",
                    value="billing",
                    font_size="0.85rem",
                    font_weight="500",
                    padding="0.5rem 1rem",
                ),
                rx.tabs.trigger(
                    "SOAP Note",
                    value="soap",
                    font_size="0.85rem",
                    font_weight="500",
                    padding="0.5rem 1rem",
                ),
                rx.tabs.trigger(
                    "FHIR Output",
                    value="fhir",
                    font_size="0.85rem",
                    font_weight="500",
                    padding="0.5rem 1rem",
                ),
                rx.tabs.trigger(
                    "Risk Flags",
                    value="risk",
                    font_size="0.85rem",
                    font_weight="500",
                    padding="0.5rem 1rem",
                ),
                border_bottom=f"1px solid {BORDER}",
                background_color=WHITE,
                padding_x="0.5rem",
            ),
            rx.tabs.content(clinical_tab(), value="clinical"),
            rx.tabs.content(billing_tab(), value="billing"),
            rx.tabs.content(soap_tab(), value="soap"),
            rx.tabs.content(fhir_tab(), value="fhir"),
            rx.tabs.content(risk_tab(), value="risk"),
            default_value="clinical",
            width="100%",
            flex="1",
        ),

        width="100%",
        flex="1",
        height="100vh",
        overflow_y="auto",
        background_color=WHITE,
        align_items="start",
        spacing="0",
    )


# ── Root page ─────────────────────────────────────────────────────────────────

def index() -> rx.Component:
    return rx.hstack(
        left_panel(),
        right_panel(),
        width="100vw",
        height="100vh",
        overflow="hidden",
        spacing="0",
        background_color=WHITE,
        on_mount=AppState.load_files,
    )


# ── App setup ─────────────────────────────────────────────────────────────────

app = rx.App(
    style={
        "font_family": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        "font_size": "14px",
        "color": "#111827",
    }
)
app.add_page(index, route="/", title="Clinical Documentation Copilot")
