import inspect
import json
import os
import random
import subprocess
import time
from functools import lru_cache
from pathlib import Path

import emoji
import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

from rizzk_core import calculate_risk_reward, calculate_percentage_moves, calculate_risk_reward_ratio

st.set_page_config(page_title="(⌐■_■) RIZZK Calculator 🚀", page_icon="⌐■_■", layout="wide")

# Helper to parse boolean-like env / secret values
def _parse_bool(s):
    if s is None:
        return None
    if isinstance(s, bool):
        return s
    s = str(s).strip().lower()
    if s in ("1", "true", "t", "yes", "y", "on"):
        return True
    if s in ("0", "false", "f", "no", "n", "off"):
        return False
    return None

DEFAULT_FORM_VALUES = {
    "position_type": "Long",
    "risk_mode": "% of Account",
    "account_size": 25000.0,
    "risk_pct_value": 1.0,
    "risk_fixed_value": 250.0,
    "entry_price": 100.0,
    "stop_loss_long": 97.5,
    "stop_loss_short": 102.5,
}

POSITION_SLUGS = {
    "long": "Long",
    "short": "Short",
}
POSITION_LOOKUP = {label: slug for slug, label in POSITION_SLUGS.items()}

RISK_MODE_SLUGS = {
    "percent": "% of Account",
    "fixed": "Fixed $ Amount",
}
RISK_MODE_LOOKUP = {label: slug for slug, label in RISK_MODE_SLUGS.items()}


@lru_cache()
def _get_build_meta():
    version = (
        os.environ.get("RIZZK_APP_VERSION")
        or os.environ.get("APP_VERSION")
        or os.environ.get("RELEASE_VERSION")
    )
    sha = (
        os.environ.get("RIZZK_BUILD_SHA")
        or os.environ.get("BUILD_SHA")
        or os.environ.get("GITHUB_SHA")
        or os.environ.get("COMMIT_SHA")
    )

    if sha:
        sha = sha[:7]
    else:
        try:
            repo_root = Path(__file__).resolve().parent
            sha = subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=repo_root,
                stderr=subprocess.DEVNULL,
            ).decode("utf-8").strip()
        except Exception:
            sha = "local-dev"

    if not version:
        version = "dev"

    return version, sha


def _init_form_state():
    for key, default in DEFAULT_FORM_VALUES.items():
        if key not in st.session_state:
            st.session_state[key] = default


def _reset_form_values():
    for key, default in DEFAULT_FORM_VALUES.items():
        st.session_state[key] = default
    # Keep widget aliases aligned
    st.session_state["risk_pct_value"] = DEFAULT_FORM_VALUES["risk_pct_value"]
    st.session_state["risk_fixed_value"] = DEFAULT_FORM_VALUES["risk_fixed_value"]


def _parse_float_param(value, min_value=None, max_value=None):
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if min_value is not None and parsed < min_value:
        return None
    if max_value is not None and parsed > max_value:
        return None
    return parsed


def _format_float_for_query(value):
    if value is None:
        return None
    return f"{value:.6g}"


def _format_r_multiple(value):
    """Standardize R Multiple display as "x.xx:1" or em dash when unavailable."""
    if value is None:
        return "—"
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "—"
    return f"{v:.2f}:1"


def _load_state_from_query():
    """Load initial widget state from URL query parameters using st.query_params."""
    qp = st.query_params
    if not qp:
        return

    def _get(key):
        value = qp.get(key)
        if isinstance(value, list):
            return value[0] if value else None
        return value

    pt_slug = (_get("pt") or "").lower()
    if pt_slug in POSITION_SLUGS and "position_type" not in st.session_state:
        st.session_state["position_type"] = POSITION_SLUGS[pt_slug]

    rm_slug = (_get("rm") or "").lower()
    if rm_slug in RISK_MODE_SLUGS and "risk_mode" not in st.session_state:
        st.session_state["risk_mode"] = RISK_MODE_SLUGS[rm_slug]

    account_size_param = _parse_float_param(_get("acct"), min_value=0.0)
    if account_size_param is not None and "account_size" not in st.session_state:
        st.session_state["account_size"] = account_size_param

    risk_pct_param = _parse_float_param(_get("rp"), min_value=0.0)
    if risk_pct_param is not None and "risk_pct_value" not in st.session_state:
        st.session_state["risk_pct_value"] = risk_pct_param

    risk_fixed_param = _parse_float_param(_get("rf"), min_value=0.0)
    if risk_fixed_param is not None and "risk_fixed_value" not in st.session_state:
        st.session_state["risk_fixed_value"] = risk_fixed_param

    entry_param = _parse_float_param(_get("entry"), min_value=0.0)
    if entry_param is not None and "entry_price" not in st.session_state:
        st.session_state["entry_price"] = entry_param

    stop_param = _parse_float_param(_get("sl"), min_value=0.0)
    if stop_param is not None:
        # Initialize both long/short stop defaults only if not set yet
        if "stop_loss_long" not in st.session_state:
            st.session_state["stop_loss_long"] = stop_param
        if "stop_loss_short" not in st.session_state:
            st.session_state["stop_loss_short"] = stop_param


def _sync_query_params(position_type, risk_mode):
    """Keep st.query_params in sync with current inputs for shareable permalinks."""
    params = {}
    if position_type in POSITION_LOOKUP:
        params["pt"] = POSITION_LOOKUP[position_type]
    if risk_mode in RISK_MODE_LOOKUP:
        params["rm"] = RISK_MODE_LOOKUP[risk_mode]

    account_size = st.session_state.get("account_size")
    formatted_account = _format_float_for_query(account_size)
    if formatted_account is not None:
        params["acct"] = formatted_account

    risk_pct = st.session_state.get("risk_pct_value")
    formatted_risk_pct = _format_float_for_query(risk_pct)
    if formatted_risk_pct is not None:
        params["rp"] = formatted_risk_pct

    risk_fixed = st.session_state.get("risk_fixed_value")
    formatted_risk_fixed = _format_float_for_query(risk_fixed)
    if formatted_risk_fixed is not None:
        params["rf"] = formatted_risk_fixed

    entry_price = st.session_state.get("entry_price")
    formatted_entry = _format_float_for_query(entry_price)
    if formatted_entry is not None:
        params["entry"] = formatted_entry

    stop_key = "stop_loss_long" if position_type == "Long" else "stop_loss_short"
    stop_value = st.session_state.get(stop_key)
    formatted_stop = _format_float_for_query(stop_value)
    if formatted_stop is not None:
        params["sl"] = formatted_stop

    # Compare against current URL state (normalize list values to single values for comparison)
    current_qp = {k: (v[0] if isinstance(v, list) else v) for k, v in st.query_params.items()}
    if current_qp != params:
        # Assigning replaces the URL query params
        st.query_params = params


def render_copy_button(payload_text: str, label: str, element_id: str):
    """Render a styled copy-to-clipboard button with inline JS."""
    safe_payload = json.dumps(payload_text)
    safe_label = json.dumps(label)
    components.html(
        f"""
        <div class="copy-wrap">
            <button id="{element_id}" class="copy-btn" onclick='
                (async () => {{
                    try {{
                        await navigator.clipboard.writeText({safe_payload});
                        const btn = document.getElementById("{element_id}");
                        const original = {safe_label};
                        btn.dataset.label = original;
                        btn.innerText = "Copied!";
                        btn.classList.add("copied");
                        setTimeout(() => {{
                            btn.innerText = original;
                            btn.classList.remove("copied");
                        }}, 1600);
                    }} catch (err) {{
                        console.error(err);
                    }}
                }})();
            '>
                📋 {label}
            </button>
        </div>
        """,
        height=52,
    )


def render_copy_current_url(label: str = "Copy Shareable Link", element_id: str = "copy-link-btn"):
    """Render a copy button that copies the current page URL (including query params)."""
    components.html(
        """
        <div class="copy-wrap">
            <button id="copy-link-btn" class="copy-btn" onclick='
                (async () => {
                    try {
                        const url = window.location.href;
                        await navigator.clipboard.writeText(url);
                        const btn = document.getElementById("copy-link-btn");
                        const original = "Copy Shareable Link";
                        btn.dataset.label = original;
                        btn.innerText = "Copied!";
                        btn.classList.add("copied");
                        setTimeout(() => {
                            btn.innerText = original;
                            btn.classList.remove("copied");
                        }, 1600);
                    } catch (err) {
                        console.error(err);
                    }
                })();
            '>
                📎 Copy Shareable Link
            </button>
        </div>
        """,
        height=52,
    )

# Determine default for Edgy mode (priority: st.secrets -> env var -> fallback False)
edgy_default = None
if hasattr(st, "secrets"):
    try:
        edgy_default = st.secrets.get('EDGY_MODE_DEFAULT')
    except Exception:
        edgy_default = None

if edgy_default is None:
    edgy_default = os.environ.get('EDGY_MODE_DEFAULT')

edgy_default = _parse_bool(edgy_default)
if edgy_default is None:
    edgy_default = False

st.markdown("""
<style>
    :root {
        --bg-primary: #05070a;
        --bg-panel: rgba(14, 18, 26, 0.85);
        --bg-panel-alt: rgba(12, 16, 24, 0.95);
        --accent-teal: #14ffec;
        --accent-magenta: #ff6ec7;
        --accent-amber: #ffc23c;
        --text-primary: #f1f5f9;
        --text-secondary: #94a3b8;
        --border-soft: rgba(20, 255, 236, 0.25);
        --shadow-soft: 0 20px 40px rgba(0, 0, 0, 0.45);
    }

    .stApp {
        background: radial-gradient(circle at top right, rgba(20, 255, 236, 0.08), transparent 45%), var(--bg-primary);
        color: var(--text-primary);
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(10, 13, 20, 0.95) 0%, rgba(5, 7, 10, 0.95) 100%);
        border-right: 1px solid rgba(20, 255, 236, 0.08);
        backdrop-filter: blur(12px);
    }

    [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {
        color: var(--text-primary) !important;
    }

    /* Elevated typography */
    .main-header {
        font-size: 3.1rem;
        background: linear-gradient(90deg, var(--accent-teal), var(--accent-magenta));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        margin-bottom: 0.75rem;
        font-weight: 800;
        letter-spacing: 0.12em;
        text-transform: uppercase;
    }
    .sub-header {
        font-size: 1.05rem;
        color: var(--text-secondary);
        text-align: center;
        margin-bottom: 1.75rem;
        letter-spacing: 0.08em;
        font-style: normal;
        text-transform: uppercase;
    }

    /* Metric and panel treatments */
    .metric-card {
        background: var(--bg-panel-alt);
        padding: 1.4rem;
        border-radius: 1rem;
        text-align: center;
        margin: 0.6rem;
        border: 1px solid rgba(20, 255, 236, 0.08);
        box-shadow: var(--shadow-soft);
        transition: transform 0.25s ease, border 0.25s ease, box-shadow 0.25s ease;
    }
    .metric-card:hover {
        transform: translateY(-3px);
        border: 1px solid var(--accent-teal);
        box-shadow: 0 28px 40px rgba(20, 255, 236, 0.12);
    }

    .success-msg {
        background: linear-gradient(135deg, rgba(20, 255, 236, 0.12), rgba(255, 110, 199, 0.12));
        color: var(--accent-teal);
        padding: 1rem;
        border-radius: 0.75rem;
        margin: 1.5rem 0;
        border: 1px solid rgba(20, 255, 236, 0.35);
        font-weight: 600;
        text-align: center;
        box-shadow: var(--shadow-soft);
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    .stButton>button[data-testid="stBaseButton-primary"] {
        background: linear-gradient(135deg, var(--accent-teal), var(--accent-magenta)) !important;
        color: #05070a !important;
        border: none !important;
        border-radius: 0.6rem !important;
        padding: 0.85rem 2.2rem !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
        box-shadow: 0 18px 32px rgba(20, 255, 236, 0.18) !important;
        transition: all 0.25s ease !important;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    .stButton>button[data-testid="stBaseButton-primary"]:hover {
        filter: brightness(1.05) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 24px 36px rgba(255, 110, 199, 0.22) !important;
    }

    .form-container {
        background: var(--bg-panel);
        padding: 1.6rem;
        border-radius: 1.2rem;
        box-shadow: var(--shadow-soft);
        border: 1px solid var(--border-soft);
        color: var(--text-primary) !important;
        backdrop-filter: blur(10px);
    }

    .form-container .stText, .form-container label {
        color: var(--text-primary) !important;
        text-transform: uppercase;
        font-size: 0.85rem;
        letter-spacing: 0.08em;
    }

    .stNumberInput input, .stSelectbox select, .stRadio div {
        border-radius: 0.65rem !important;
        border: 1px solid rgba(148, 163, 184, 0.35) !important;
        padding: 0.6rem !important;
        background: rgba(9, 12, 18, 0.85) !important;
        color: var(--text-primary) !important;
    }
    .stNumberInput input:focus, .stSelectbox select:focus {
        border-color: var(--accent-teal) !important;
        box-shadow: 0 0 0 0.25rem rgba(20, 255, 236, 0.2) !important;
    }

    h3 {
        color: var(--accent-teal);
        border-bottom: 2px solid rgba(20, 255, 236, 0.25);
        padding-bottom: 0.4rem;
        margin-bottom: 1.25rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    .streamlit-expanderHeader {
        background: rgba(12, 16, 24, 0.92) !important;
        border-radius: 0.75rem !important;
        border: 1px solid rgba(20, 255, 236, 0.12) !important;
        font-weight: 600 !important;
        color: var(--text-primary) !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .stPlotlyChart {
        border-radius: 1rem;
        overflow: hidden;
        box-shadow: var(--shadow-soft);
        background: rgba(8, 11, 18, 0.9);
        border: 1px solid rgba(20, 255, 236, 0.1);
    }

    .info-box {
        background: rgba(255, 194, 60, 0.12);
        border: 1px solid rgba(255, 194, 60, 0.4);
        color: var(--accent-amber);
        padding: 0.85rem 1.1rem;
        border-radius: 0.75rem;
        margin-bottom: 1.4rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    .stRadio > div {
        background: rgba(9, 12, 18, 0.65);
        border-radius: 0.75rem;
        padding: 0.35rem;
        border: 1px solid rgba(148, 163, 184, 0.2);
    }

    /* Make radio buttons clickable */
    .stRadio label {
        cursor: pointer !important;
        pointer-events: auto !important;
    }

    .stRadio input[type="radio"] {
        cursor: pointer !important;
        pointer-events: auto !important;
    }

    /* Compact sections for tighter metrics spacing */
    .compact-section h3, .compact-section h4 { margin-bottom: 0.4rem; }
    .compact-section [data-testid="stMetric"] { margin: 0 !important; padding: 0.25rem 0 !important; }

    /* Status pill */
    .status-wrap { margin: 0.5rem 0 0.75rem; }
    .status-pill {
        display: inline-block;
        padding: 0.35rem 0.6rem;
        border-radius: 999px;
        font-weight: 700;
        font-size: 0.75rem;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        border: 1px solid rgba(148,163,184,0.35);
    }
    .status-ok { color: #10b981; background: rgba(16,185,129,.12); border-color: rgba(16,185,129,.35); }
    .status-warn { color: #f59e0b; background: rgba(245,158,11,.12); border-color: rgba(245,158,11,.35); }
    .status-bad { color: #f43f5e; background: rgba(244,63,94,.12); border-color: rgba(244,63,94,.35); }

    /* Subtle ad placeholders */
    .ad-box {
        background: linear-gradient(180deg, rgba(20,255,236,0.06), rgba(255,110,199,0.06));
        border: 1px dashed rgba(148, 163, 184, 0.35);
        color: var(--text-secondary);
        padding: 0.9rem 1rem;
        border-radius: 0.75rem;
        margin: 0.5rem 0 1rem;
    }
    .ad-box small {
        display: block;
        opacity: 0.85;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 0.35rem;
    }
    .inline-ad {
        background: rgba(255, 194, 60, 0.08);
        border: 1px dashed rgba(255, 194, 60, 0.35);
        color: var(--text-secondary);
        padding: 0.75rem 1rem;
        border-radius: 0.75rem;
        margin-top: 0.75rem;
    }
    .copy-wrap {
        display: flex;
        justify-content: flex-end;
        margin-top: 0.35rem;
    }
    .copy-btn {
        background: linear-gradient(135deg, var(--accent-teal), var(--accent-magenta));
        border: none;
        border-radius: 0.5rem;
        padding: 0.45rem 0.9rem;
        font-weight: 600;
        color: #05070a;
        cursor: pointer;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        box-shadow: 0 12px 22px rgba(20, 255, 236, 0.15);
    }
    .copy-btn:hover {
        transform: translateY(-1px);
        box-shadow: 0 16px 26px rgba(255, 110, 199, 0.25);
    }
    .copy-btn.copied {
        background: linear-gradient(135deg, var(--accent-amber), var(--accent-teal));
    }
    @media (max-width: 900px) {
        .stApp {
            padding: 0 0.65rem;
        }
        .block-container {
            padding: 0.75rem 0.25rem !important;
        }
        div[data-testid="stHorizontalBlock"] {
            flex-direction: column !important;
            gap: 0.75rem !important;
        }
        div[data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
        }
        .stButton>button {
            width: 100% !important;
        }
        .stNumberInput input {
            min-height: 48px;
            font-size: 1rem;
        }
        .stMetric {
            text-align: left !important;
        }
        .copy-wrap {
            justify-content: flex-start;
        }
    }
</style>
""", unsafe_allow_html=True)

if 'history' not in st.session_state:
    st.session_state.history = []

_load_state_from_query()

try:
    with st.sidebar:
        st.markdown("## Feedback & Support")
        st.markdown("**Found a bug?** Want a new feature?")
        st.markdown("📧 **Email:** GoblinOSRep@gmail.com")
        st.markdown("**Developer:** Fuaad Abdullah")
        st.markdown("---")
        st.markdown("💡 **We'd love to hear from you:**")
        st.markdown("• Bug reports help us improve")
        st.markdown("• Feature requests shape the roadmap")
        st.markdown("• General feedback is always welcome")
        st.markdown("---")
        # Toggle: 🦇 mode (ASCII emoticons) vs polished emoji UI
        # Default set to False so the polished emoji UI is the default experience.
        edgy_mode = st.checkbox("🦇 mode (ASCII emoticons)", value=edgy_default, help="Toggle ASCII emoticons vs polished emoji UI")

        # Sidebar flavor and helpers
        st.markdown("### Trading Humor")
        jokes = [
            "Risk small, sleep tall.",
            "Cut losers fast; they’re not NFTs.",
            "My stop hit so hard, it filed a police report.",
            "Risk:reward > ego:revenge.",
            "If FOMO had a ticker, I’d short it.",
            "Green day? Hydrate. Red day? Hydrate plus walk.",
        ]
        st.caption(random.choice(jokes))

        st.markdown("### Pro Tips")
        if hasattr(st, "popover"):
            with st.popover("Sizing wisdom"):
                st.write("1R should feel uncomfortable to lose, not devastating.")
                st.write("Keep risk per trade consistent for clarity and compounding.")
        else:
            with st.expander("Sizing wisdom"):
                st.write("1R should feel uncomfortable to lose, not devastating.")
                st.write("Keep risk per trade consistent for clarity and compounding.")

        st.markdown("### Common Setups")
        with st.expander("📈 Strategy Quick Ref"):
            st.markdown("**Micro Pullback**")
            st.caption("Entry: First bounce after initial move. Stop: Below pullback low.")

            st.markdown("**VWAP Bounce**")
            st.caption("Entry: Price tests VWAP, holds. Stop: Below VWAP.")

            st.markdown("**High of Day Break**")
            st.caption("Entry: Above HOD on volume. Stop: Below breakout candle.")

            st.markdown("**Failed Breakout (Short)**")
            st.caption("Entry: Price rejects resistance. Stop: Above rejection wick.")

            st.caption("*Reference patterns only. Confirm with your edge and context.*")

        st.markdown("### Trust & Transparency")
        st.markdown(
            '<div class="ad-box"><small>About RIZZK</small><b>Built for traders who respect risk.</b><br/>Transparent math, open workbook, no surprise fees.</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="ad-box"><small>Why trust RIZZK?</small><b>Evidence-based sizing.</b><br/>Risk controls come first. Formulas are published; decisions stay with you.</div>',
            unsafe_allow_html=True,
        )

        st.markdown("---")
        # st.checkbox("Debug mode", key="debug_mode", help="Show a status pill and input checks to quickly spot why results may be missing.")

    # Header: always show (⌐■_■) for that signature RIZZK style
    st.markdown(f'<h1 class="main-header">(⌐■_■) RIZZK Calculator {emoji.emojize(":rocket:")}</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Refined risk. Raw edge. Position sizing for traders who know their RIZZK.</p>', unsafe_allow_html=True)

    # Small helper note styled as an inline info box

    # Small helper note styled as an inline info box
    st.markdown(
        '<div class="info-box">Example numbers. Tune to your own playbook.</div>',
        unsafe_allow_html=True,
    )

    # Section title stays on-theme: bat only in edgy mode
    if 'edgy_mode' in globals() and edgy_mode:
        st.markdown("### 🦇 Risk-Reward Calculator")
    else:
        st.markdown("### Risk-Reward Calculator")

    st.markdown('<div class="form-container">', unsafe_allow_html=True)
    _init_form_state()
    radio_supports_horizontal = "horizontal" in inspect.signature(st.radio).parameters

    # Add spacing before Reset button
    st.markdown("<br>", unsafe_allow_html=True)

    control_col_left, control_col_right = st.columns([1, 9])
    with control_col_left:
        if st.button("Reset to Example", use_container_width=True):
            _reset_form_values()
            # Use non-experimental rerun API
            if hasattr(st, "rerun"):
                st.rerun()
            else:
                st.experimental_rerun()
    with control_col_right:
        st.caption("RIZZK values precision: numbers shown are examples—adjust to your playbook.")

    st.markdown("<br>", unsafe_allow_html=True)  # Add vertical spacing

    with st.form("rizzk_form"):

        # Row 1: Position Type | Account Size
        row1_col1, row1_col2 = st.columns(2)
        with row1_col1:
            if hasattr(st, "segmented_control"):
                position_type = st.segmented_control(
                    "Position Type",
                    options=["Long", "Short"],
                    key="position_type",
                )
            else:
                if radio_supports_horizontal:
                    position_type = st.radio(
                        "Position Type",
                        ["Long", "Short"],
                        index=["Long", "Short"].index(st.session_state.get("position_type", DEFAULT_FORM_VALUES["position_type"])),
                        horizontal=True,
                        key="position_type",
                    )
                else:
                    position_type = st.radio(
                        "Position Type",
                        ["Long", "Short"],
                        index=["Long", "Short"].index(st.session_state.get("position_type", DEFAULT_FORM_VALUES["position_type"])),
                        key="position_type",
                    )

        with row1_col2:
            account_size = st.number_input(
                "💰 Account Size ($)",
                min_value=0.0,
                step=100.0,
                help="Total capital available in your trading account",
                key="account_size",
            )

        # Always-visible Long/Short help
        if position_type == "Long":
            st.info("📈 Long: profit when price rises. Entry above stop. Stop must be BELOW entry.")
        else:
            st.info("📉 Short: profit when price falls. Entry above stop. Stop must be ABOVE entry.")

        # Row 2: Risk Sizing | Entry + Stop
        row2_col1, row2_col2 = st.columns(2)
        with row2_col1:
            st.markdown("#### Risk Mode")

            risk_mode_options = ["% of Account", "Fixed $ Amount"]
            default_risk_mode = st.session_state.get("risk_mode", DEFAULT_FORM_VALUES["risk_mode"])
            if hasattr(st, "segmented_control"):
                risk_mode = st.segmented_control(
                    "Risk Mode",
                    options=risk_mode_options,
                    key="risk_mode",
                )
            else:
                radio_index = risk_mode_options.index(default_risk_mode) if default_risk_mode in risk_mode_options else 0
                if radio_supports_horizontal:
                    risk_mode = st.radio(
                        "Risk Mode",
                        risk_mode_options,
                        index=radio_index,
                        horizontal=True,
                        key="risk_mode",
                    )
                else:
                    risk_mode = st.radio(
                        "Risk Mode",
                        risk_mode_options,
                        index=radio_index,
                        key="risk_mode",
                    )

            if risk_mode == "% of Account":
                risk_percentage = st.slider(
                    "📊 Risk Percentage",
                    min_value=0.1,
                    max_value=10.0,
                    step=0.1,
                    help="Percent of account you're willing to lose if the stop is hit",
                    key="risk_pct_value",
                )
                preview_risk = account_size * (risk_percentage / 100)
                if account_size <= 0:
                    st.error("Set account size above $0 to size risk by percentage.")
                else:
                    st.success(f"**Risking: ${preview_risk:,.2f}**")
                    st.caption("✓ Adapts as equity changes — good for compounding")
                risk_amount_input = float(st.session_state.get("risk_fixed_value", DEFAULT_FORM_VALUES["risk_fixed_value"]))
            else:
                risk_percentage = float(st.session_state.get("risk_pct_value", DEFAULT_FORM_VALUES["risk_pct_value"]))
                risk_amount_input = st.number_input(
                    "💵 Dollar Amount",
                    min_value=0.0,
                    step=10.0,
                    help="Fixed dollar amount you're comfortable putting on the line",
                    key="risk_fixed_value",
                )
                if risk_amount_input <= 0:
                    st.error("Risk amount must be greater than $0.")
                elif account_size <= 0:
                    st.error("Set account size above $0 to size risk accurately.")
                elif risk_amount_input > account_size:
                    st.error("⚠️ Risk exceeds account size!")
                else:
                    st.success(f"**Risking: ${risk_amount_input:,.2f}**")
                    if account_size > 0:
                        pct_hint = (risk_amount_input / account_size) * 100
                        st.caption(f"≈ {pct_hint:.2f}% of account at risk.")
                    else:
                        st.caption("✓ Same $ at risk each trade — steady drawdowns")

        with row2_col2:
            entry_price = st.number_input(
                "🎯 Entry Price ($)",
                min_value=0.0,
                step=0.1,
                help="Price at which you plan to enter the trade",
                key="entry_price",
            )

            # Dynamic stop-loss labeling and constraints
            epsilon = max(entry_price * 1e-6, 1e-9)
            if position_type == "Long":
                stop_label = "💥 Stop Loss Price ($)"
                stop_help = "For Longs: stop must be BELOW entry."
                stop_max = max(0.0, entry_price - epsilon)
                # Pre-constrain the session_state value to valid range
                default_stop = st.session_state.get("stop_loss_long", DEFAULT_FORM_VALUES["stop_loss_long"])
                if stop_max > 0:
                    constrained_stop = max(0.0, min(default_stop, stop_max))
                else:
                    constrained_stop = 0.0
                # Update session_state with constrained value before widget creation
                st.session_state["stop_loss_long"] = constrained_stop
                stop_loss = st.number_input(
                    stop_label,
                    min_value=0.0,
                    max_value=float(stop_max),
                    step=0.1,
                    help=stop_help,
                    key="stop_loss_long",
                )
                if stop_loss >= entry_price and entry_price > 0:
                    st.warning("For a long, stop should be below entry.")
            else:
                stop_label = "💥 Stop Loss Price ($)"
                stop_help = "For Shorts: stop must be ABOVE entry."
                stop_min = float(entry_price + epsilon)
                # Pre-constrain the session_state value to valid range
                default_stop = st.session_state.get("stop_loss_short", DEFAULT_FORM_VALUES["stop_loss_short"])
                constrained_stop = max(default_stop, stop_min)
                # Update session_state with constrained value before widget creation
                st.session_state["stop_loss_short"] = constrained_stop
                stop_loss = st.number_input(
                    stop_label,
                    min_value=float(stop_min),
                    step=0.1,
                    help=stop_help,
                    key="stop_loss_short",
                )
                if stop_loss <= entry_price and entry_price > 0:
                    st.warning("For a short, stop should be above entry.")

        # Add spacing before Calculate button
        st.markdown("<br>", unsafe_allow_html=True)

        # Add spinner and prevent double-click spam
        if 'calc_loading' not in st.session_state:
            st.session_state.calc_loading = False
        if 'calc_disabled_until' not in st.session_state:
            st.session_state.calc_disabled_until = 0

        now = time.time()
        calc_disabled = st.session_state.calc_loading or (now < st.session_state.calc_disabled_until)

        # Add spacing with columns
        btn_col1, btn_col2, btn_col3 = st.columns([1, 2, 1])
        with btn_col2:
            submitted = st.form_submit_button("Calculate", type="primary", disabled=calc_disabled, use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Add spacing after form
    st.markdown("<br>", unsafe_allow_html=True)

    _sync_query_params(position_type, risk_mode)

    # Pre-calc diagnostics and status
    warnings_list = []
    if account_size <= 0:
        warnings_list.append("Account size must be greater than 0.")
    if entry_price <= 0:
        warnings_list.append("Entry price must be greater than 0.")
    if stop_loss <= 0:
        warnings_list.append("Stop loss price must be greater than 0.")
    if position_type == "Long" and entry_price > 0 and stop_loss >= entry_price:
        warnings_list.append("For Longs, stop must be below entry.")
    if position_type == "Short" and entry_price > 0 and stop_loss <= entry_price:
        warnings_list.append("For Shorts, stop must be above entry.")
    if risk_mode == "% of Account":
        if not (0.1 <= risk_percentage <= 10.0):
            warnings_list.append("Risk % should be between 0.1 and 10.")
    else:
        if risk_amount_input <= 0:
            warnings_list.append("Risk amount must be greater than 0.")
        if account_size > 0 and risk_amount_input > account_size:
            warnings_list.append("Risk amount cannot exceed account size.")

    is_ready = len(warnings_list) == 0
    status_class = "status-ok" if is_ready else "status-warn"
    status_text = "Ready — press Calculate" if is_ready else "Fix inputs to calculate"
    st.markdown(f'<div class="status-wrap"><span class="status-pill {status_class}">{status_text}</span></div>', unsafe_allow_html=True)

    # Live summary preview so traders see sizing impact while tweaking inputs
    preview_results = None
    preview_rr = None
    if is_ready:
        st.markdown("#### 📊 Live Risk Preview")
        st.caption("Position sizing based on current inputs. Hit Calculate for full results & targets.")
        try:
            preview_risk_input = risk_percentage if risk_mode == "% of Account" else risk_amount_input
            preview_results = calculate_risk_reward(
                position_type, account_size, risk_mode, preview_risk_input, entry_price, stop_loss
            )
            preview_rr = calculate_risk_reward_ratio(
                entry_price, stop_loss, preview_results[3], position_type
            )
        except Exception:
            preview_results = None
            preview_rr = None

    risk_pct_preview = None
    if risk_mode == "% of Account":
        risk_pct_preview = risk_percentage
    elif account_size > 0 and risk_amount_input > 0:
        risk_pct_preview = (risk_amount_input / account_size) * 100

    pos_display = f"{preview_results[1]} shares" if preview_results else "—"
    risk_dollar_display = f"${preview_results[2]:,.2f}" if preview_results else "—"
    risk_pct_display = f"{risk_pct_preview:.2f}%" if risk_pct_preview is not None else "—"
    rr_display = _format_r_multiple(preview_rr)

    summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)
    with summary_col1:
        st.metric("Position Size", pos_display)
    with summary_col2:
        st.metric("Risk ($)", risk_dollar_display)
    with summary_col3:
        st.metric("Risk (%)", risk_pct_display)
    with summary_col4:
        st.metric("R Multiple", rr_display)
    if not preview_results:
        st.caption("Adjust inputs and resolve warnings to populate the live risk summary.")
    live_payload = "Complete inputs to populate summary."
    if preview_results and preview_rr is not None and risk_pct_preview is not None:
        live_payload = (
            f"Position Size (rounded): {preview_results[1]} shares\n"
            f"Dollar Risk: ${preview_results[2]:,.2f}\n"
            f"Risk Percent: {risk_pct_preview:.2f}%\n"
            f"R Multiple: {_format_r_multiple(preview_rr)}\n"
            f"Account Size: ${account_size:,.2f}\n"
            f"Entry: ${entry_price:.2f} | Stop: ${stop_loss:.2f}"
        )
    render_copy_button(live_payload, "Copy Summary", "live-summary-copy")
    render_copy_current_url()

    # Optional debug mode
    show_debug = False
    try:
        # If user enabled a secret flag, honor it; otherwise check sidebar state if added later
        show_debug = bool(st.session_state.get("debug_mode", False))
    except Exception:
        show_debug = False

    if show_debug:
        with st.expander("Debug: current inputs & checks"):
            st.write({
                "position_type": position_type,
                "risk_mode": risk_mode,
                "account_size": account_size,
                "risk_percentage": risk_percentage,
                "risk_amount_input": risk_amount_input,
                "entry_price": entry_price,
                "stop_loss": stop_loss,
                "ready": is_ready,
                "warnings": warnings_list,
            })

    if submitted:
        # Prevent double submit
        if st.session_state.calc_loading:
            st.stop()
        st.session_state.calc_loading = True
        st.session_state.calc_disabled_until = time.time() + 0.3
        with st.spinner("Calculating..."):
            # Input validation
            if account_size <= 0:
                st.error("Account size must be greater than 0.", icon="🚫")
                st.session_state.calc_loading = False
                st.stop()
            if entry_price <= 0:
                st.error("Entry price must be greater than 0.", icon="🚫")
                st.session_state.calc_loading = False
                st.stop()
            if stop_loss <= 0:
                st.error("Stop loss price must be greater than 0.", icon="🚫")
                st.session_state.calc_loading = False
                st.stop()
            if entry_price == stop_loss:
                st.error("Entry price and stop loss cannot be the same.", icon="🚫")
                st.session_state.calc_loading = False
                st.stop()
            if position_type == "Long" and stop_loss >= entry_price:
                st.error("For longs, stop must be BELOW entry.", icon="🚫")
                st.session_state.calc_loading = False
                st.stop()
            if position_type == "Short" and stop_loss <= entry_price:
                st.error("For shorts, stop must be ABOVE entry.", icon="🚫")
                st.session_state.calc_loading = False
                st.stop()

            # Calculate using centralized function
            risk_input = risk_percentage if risk_mode == "% of Account" else risk_amount_input
            position_size, position_size_rounded, risk_amount, profit_1_1, profit_2_1, stop_loss_amount = calculate_risk_reward(
                position_type, account_size, risk_mode, risk_input, entry_price, stop_loss
            )

            # Calculate percentage moves
            pct_drop_to_stop, pct_move_to_1_1 = calculate_percentage_moves(entry_price, stop_loss, profit_1_1, position_type)

            # Calculate R:R ratio
            rr_1_1 = calculate_risk_reward_ratio(entry_price, stop_loss, profit_1_1, position_type)

            st.markdown('<div class="success-msg">Calculation Complete!</div>', unsafe_allow_html=True)
        st.session_state.calc_loading = False

        # Results above the fold, right under button
        st.markdown('<div class="compact-section">', unsafe_allow_html=True)
        st.markdown(f"### {emoji.emojize(':fire:')} Key Metrics")
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Position Size", f"{position_size_rounded} shares")
            st.caption(f"Theoretical: {position_size:.2f} shares")
        with col2:
            st.metric("Dollar Risk", f"${risk_amount:.2f}")
        with col3:
            st.metric("1:1 Target", f"${profit_1_1:.2f}")
        with col4:
            st.metric("2:1 Target", f"${profit_2_1:.2f}")
        with col5:
            st.metric("R:R Multiple", _format_r_multiple(rr_1_1))

        st.caption("Position size rounded to whole shares (most brokers don't accept fractional shares).")
        result_risk_pct = risk_percentage if risk_mode == "% of Account" else ((risk_amount / account_size) * 100 if account_size else None)
        results_payload_lines = [
            f"Position Size (rounded): {position_size_rounded} shares",
            f"Position Size (theoretical): {position_size:.2f} shares",
            f"Dollar Risk: ${risk_amount:.2f}",
            f"Risk Percent: {result_risk_pct:.2f}%" if result_risk_pct is not None else "Risk Percent: n/a",
            f"1:1 Target: ${profit_1_1:.2f}",
            f"2:1 Target: ${profit_2_1:.2f}",
            f"R Multiple: {_format_r_multiple(rr_1_1)}",
            f"Account Size: ${account_size:,.2f}",
            f"Entry: ${entry_price:.2f}",
            f"Stop: ${stop_loss:.2f}",
        ]
        render_copy_button("\n".join(results_payload_lines), "Copy Results", "calc-results-copy")

        # Percentage Moves
        st.markdown("### Percentage Moves")
        pct_col1, pct_col2 = st.columns(2)
        with pct_col1:
            st.metric("% Drop to Stop", f"{pct_drop_to_stop:.2f}%")
        with pct_col2:
            st.metric("% Move to 1:1 Target", f"{pct_move_to_1_1:.2f}%")
        st.markdown('</div>', unsafe_allow_html=True)

        # Chart
        chart_data = pd.DataFrame({
            'Scenario': ['Risk', '1:1 Profit', '2:1 Profit'],
            'Amount': [risk_amount, abs(profit_1_1 - entry_price) * position_size, abs(profit_2_1 - entry_price) * position_size]
        })
        fig = px.bar(chart_data, x='Scenario', y='Amount', color_discrete_sequence=['#14ffec', '#ff6ec7', '#ffc23c'])
        st.plotly_chart(fig, use_container_width=True)

        # Inline ad placeholder under chart
        st.markdown('<div class="inline-ad"><small>Ad • Education</small><b>Deep-dive Risk Modules</b><br/>Sharpen R:R intuition with short, practical videos. Placeholder content.</div>', unsafe_allow_html=True)

        # Export results
        results_df = pd.DataFrame({
            'Metric': ['Theoretical Position Size', 'Rounded Position Size', 'Risk Amount', 'Stop Loss Impact', 'Profit 1:1', 'Profit 2:1'],
            'Value': [f"{position_size:.2f} shares", f"{position_size_rounded} shares", f"${risk_amount:.2f}", f"${stop_loss_amount:.2f}", f"${profit_1_1:.2f}", f"${profit_2_1:.2f}"]
        })
        csv = results_df.to_csv(index=False)
        st.download_button("Download Results as CSV", csv, "rizzk_results.csv", "text/csv")

        # Save to history
        calc = {
            'position_type': position_type,
            'account_size': account_size,
            'risk_mode': risk_mode,
            'risk_input': risk_percentage if risk_mode == "% of Account" else risk_amount_input,
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'position_size': position_size,
            'position_size_rounded': position_size_rounded,
            'risk_amount': risk_amount,
            'profit_1_1': profit_1_1,
            'profit_2_1': profit_2_1
        }
        st.session_state.history.append(calc)
    else:
        st.markdown("### Results Preview (⌐■_■)")
        st.markdown("Fill the form and hit Calculate — results show here: position size, dollar risk, targets, and R:R.")
        st.markdown("---")
        st.markdown(f"**{emoji.emojize(':fire:')} Key Metrics** will show: Position Size, Dollar Risk, Profit Targets, R:R Ratio")
        st.markdown("**Percentage Moves** will display: % Drop to Stop, % Move to 1:1 Target")
        st.markdown("**Risk/Reward Chart** will visualize the scenarios")

    st.markdown("---")
    st.header(f"{emoji.emojize(':brain:')} Calculation History")
    if st.session_state.history:
        recent = st.session_state.history[-5:]
        for i, h in enumerate(reversed(recent), start=1):
            with st.expander(f"Calc {i}: {h['position_type']}"):
                # Calculate additional metrics using centralized functions
                pct_drop_to_stop, pct_move_to_1_1 = calculate_percentage_moves(h['entry_price'], h['stop_loss'], h['profit_1_1'], h['position_type'])
                rr_ratio = calculate_risk_reward_ratio(h['entry_price'], h['stop_loss'], h['profit_1_1'], h['position_type'])

                hist_col1, hist_col2, hist_col3, hist_col4 = st.columns(4)
                with hist_col1:
                    st.metric("Account", f"${h['account_size']}")
                    st.metric("Entry", f"${h['entry_price']}")
                with hist_col2:
                    risk_label = "%" if h.get('risk_mode', '% of Account') == '% of Account' else "$"
                    st.metric("Risk", f"{h['risk_input']}{risk_label}")
                    st.metric("Stop", f"${h['stop_loss']}")
                with hist_col3:
                    position_size_rounded = h.get('position_size_rounded', int(h['position_size']))
                    st.metric("Position", f"{position_size_rounded} shares")
                    st.caption(f"Theoretical: {h['position_size']:.2f} shares")
                    st.metric("Profit 1:1", f"${h['profit_1_1']:.2f}")
                with hist_col4:
                    st.metric("Dollar Risk", f"${h['risk_amount']:.2f}")
                    st.metric("R:R Ratio", _format_r_multiple(rr_ratio))

                # Additional metrics row
                add_col1, add_col2 = st.columns(2)
                with add_col1:
                    st.metric("% Drop to Stop", f"{pct_drop_to_stop:.2f}%")
                with add_col2:
                    st.metric("% Move to 1:1 Target", f"{pct_move_to_1_1:.2f}%")
    else:
        st.write("No calculations yet. Run one and flex it here.")
        st.caption("If this list is empty, either you're disciplined… or you're procrastinating.")
    if st.button("Clear All History"):
        st.session_state.history = []
        st.rerun()
    st.caption("This only clears local session history, not your broker. Sadly.")

    st.markdown("---")
    st.caption("Educational; not financial advice.")
    st.markdown("*Developed by Fuaad Abdullah | Powered by Streamlit*")

except Exception as e:
    st.error("Something went wrong with the calculation. Check your inputs and try again.")
    st.exception(e)  # Show full traceback for debugging
