"""Design tokens for the Claims Processing UI.

Every component must resolve colors through the semantic maps below instead
of calling st.success/st.error/st.warning ad hoc or hardcoding hex values.
This is what keeps "green" meaning the same thing (a good outcome) whether
it's labeling a fraud risk, a recommendation, or an agent status.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Tone:
    fg: str
    bg: str
    border: str
    icon: str


# Restrained palette: neutral base + one brand accent (config.toml), with
# red/amber/green reserved only for risk semantics, never decoration.
TONES = {
    "success": Tone(fg="#0F5132", bg="#E8F5EE", border="#A8D5BC", icon="✓"),
    "danger": Tone(fg="#7A1F1F", bg="#FBEAEA", border="#E8B4B4", icon="✕"),
    "warning": Tone(fg="#7A5A00", bg="#FFF6DE", border="#E8D48A", icon="⚠"),
    "info": Tone(fg="#1D4E5F", bg="#EAF2F4", border="#B7D3DA", icon="•"),
    "neutral": Tone(fg="#4B5563", bg="#F4F6F7", border="#D8DEE1", icon="○"),
}

# Recommendation -> tone
RECOMMENDATION_TONE = {
    "APPROVE": "success",
    "REJECT": "danger",
    "REVIEW": "warning",
}

# Fraud/risk level -> tone
RISK_TONE = {
    "LOW": "success",
    "MEDIUM": "warning",
    "HIGH": "danger",
}

# AgentStatus (agents/base_agent.py) -> tone
AGENT_STATUS_TONE = {
    "initialized": "neutral",
    "processing": "info",
    "completed": "success",
    "failed": "danger",
    "paused": "neutral",
}

SPACING = {
    "xs": "0.25rem",
    "sm": "0.5rem",
    "md": "1rem",
    "lg": "1.5rem",
    "xl": "2.5rem",
}


def tone_key_for_recommendation(value: str) -> str:
    return RECOMMENDATION_TONE.get((value or "").upper(), "neutral")


def tone_key_for_risk(value: str) -> str:
    return RISK_TONE.get((value or "").upper(), "neutral")


def tone_key_for_agent_status(value: str) -> str:
    return AGENT_STATUS_TONE.get((value or "").lower(), "neutral")


def tone_for_recommendation(value: str) -> Tone:
    return TONES[tone_key_for_recommendation(value)]


def tone_for_risk(value: str) -> Tone:
    return TONES[tone_key_for_risk(value)]


def tone_for_agent_status(value: str) -> Tone:
    return TONES[tone_key_for_agent_status(value)]


_CSS = f"""
<style>
.cf-card {{
    background: {TONES['neutral'].bg};
    border: 1px solid {TONES['neutral'].border};
    border-radius: 10px;
    padding: {SPACING['md']};
    margin-bottom: {SPACING['md']};
}}

.cf-pill {{
    display: inline-flex;
    align-items: center;
    gap: {SPACING['xs']};
    padding: 0.15rem 0.65rem;
    border-radius: 999px;
    font-size: 0.85rem;
    font-weight: 600;
    line-height: 1.6;
    white-space: nowrap;
}}

.cf-metric-card {{
    background: #FFFFFF;
    border: 1px solid {TONES['neutral'].border};
    border-radius: 10px;
    padding: {SPACING['md']};
    text-align: left;
}}
.cf-metric-card .cf-metric-label {{
    font-size: 0.8rem;
    color: {TONES['neutral'].fg};
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: {SPACING['xs']};
}}
.cf-metric-card .cf-metric-value {{
    font-size: 1.6rem;
    font-weight: 700;
    color: #1A2226;
}}

.cf-empty-state {{
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: {SPACING['sm']};
    padding: {SPACING['xl']} {SPACING['md']};
    color: {TONES['neutral'].fg};
    border: 1px dashed {TONES['neutral'].border};
    border-radius: 12px;
    text-align: center;
}}
.cf-empty-state .cf-empty-icon {{
    font-size: 2rem;
}}

.cf-skeleton {{
    border-radius: 8px;
    height: 1rem;
    margin-bottom: {SPACING['sm']};
    background: linear-gradient(90deg, {TONES['neutral'].bg} 25%, #ECEFF0 37%, {TONES['neutral'].bg} 63%);
    background-size: 400% 100%;
    animation: cf-shimmer 1.4s ease infinite;
}}
@keyframes cf-shimmer {{
    0% {{ background-position: 100% 50%; }}
    100% {{ background-position: 0 50%; }}
}}

</style>
"""


def inject_css():
    import streamlit as st
    st.markdown(_CSS, unsafe_allow_html=True)
