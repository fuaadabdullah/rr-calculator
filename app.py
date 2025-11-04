import streamlit as st
import pandas as pd
import plotly.express as px
import emoji
import os
from rizzk_core import calculate_risk_reward, calculate_percentage_moves, calculate_risk_reward_ratio

st.set_page_config(page_title="RIZZK Calculator", page_icon=emoji.emojize(":rocket:"), layout="wide")

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
        margin-bottom: 2.5rem;
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
        padding: 2rem;
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
</style>
""", unsafe_allow_html=True)

if 'history' not in st.session_state:
    st.session_state.history = []

try:
    with st.sidebar:
        st.markdown("## About")
        st.markdown("**Fuaad Abdullah** — Builder, trader, & GoblinOS rep")
        st.markdown("[¯\_(ツ)_/¯ GoblinOSRep@gmail.com](mailto:GoblinOSRep@gmail.com)")
        st.markdown("Built by a day trader to turn risk management into a first-class habit.")
        st.markdown("---")
        st.markdown("_🦇, refined, numbers-first. RIZZK is for traders who keep it sharp._")
        # Toggle: 🦇 mode (ASCII emoticons) vs polished emoji UI
        # Default set to False so the polished emoji UI is the default experience.
        edgy_mode = st.checkbox("🦇 mode (ASCII emoticons)", value=edgy_default, help="Toggle ASCII emoticons vs polished emoji UI")

    # Header: show ASCII + subtle emoji when edgy_mode enabled, otherwise polished header with emoji
    if 'edgy_mode' in globals() and edgy_mode:
        st.markdown('<h1 class="main-header">(⌐■_■) RIZZK Calculator ' + emoji.emojize(':rocket:') + '</h1>', unsafe_allow_html=True)
    else:
        st.markdown(f'<h1 class="main-header">RIZZK Calculator {emoji.emojize(":rocket:")}</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Refined risk. Raw edge. Position sizing for traders who know their RIZZ.</p>', unsafe_allow_html=True)

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
    with st.form("rizzk_form"):
        # Add position type selector
        position_type = st.selectbox("Position Type", ["Long", "Short"], index=0)

        # Risk mode toggle
        risk_mode = st.radio("Risk Mode", ["% of Account", "Fixed $ Amount"], index=0, horizontal=True)

        col1, col2 = st.columns(2)

        with col1:
            account_size = st.number_input("Account Size ($)", min_value=0.0, value=10000.0, step=100.0, help="Total trading account balance")
            # Initialize both variables with defaults
            risk_percentage = 1.0
            risk_amount_input = 100.0
            if risk_mode == "% of Account":
                risk_percentage = st.number_input("Risk Percentage (%)", min_value=0.0, max_value=100.0, value=1.0, step=0.1, help="Percentage of account to risk per trade")
            else:
                risk_amount_input = st.number_input("Risk Amount ($)", min_value=0.0, value=100.0, step=10.0, help="Fixed dollar amount to risk per trade")

        with col2:
            entry_price = st.number_input(
                "Entry Price ($)",
                min_value=0.0,
                value=100.0,
                step=0.1,
                help="Price at which you plan to enter the trade",
            )

            # Dynamic stop-loss labeling and constraints to make intent clear
            epsilon = max(entry_price * 1e-6, 1e-9)
            if position_type == "Long":
                stop_label = "💥 Stop Loss Price ($)"
                stop_help = "For Longs: stop must be BELOW entry."
                stop_max = max(0.0, entry_price - epsilon)
                # Choose a sensible default that respects the constraint
                default_stop = stop_max - 0.01 if stop_max >= 0.02 else max(0.0, entry_price * 0.5)
                stop_loss = st.number_input(
                    stop_label,
                    min_value=0.0,
                    max_value=float(stop_max),
                    value=float(default_stop),
                    step=0.1,
                    help=stop_help,
                )
            else:
                stop_label = "💥 Stop Loss Price ($)"
                stop_help = "For Shorts: stop must be ABOVE entry."
                stop_min = float(entry_price + epsilon)
                default_stop = max(stop_min + 0.01, entry_price + 0.01)
                stop_loss = st.number_input(
                    stop_label,
                    min_value=float(stop_min),
                    value=float(default_stop),
                    step=0.1,
                    help=stop_help,
                )

        submitted = st.form_submit_button("Calculate", type="primary")
    st.markdown('</div>', unsafe_allow_html=True)

    if submitted:
            # Input validation
            if account_size <= 0:
                st.error("Account size must be greater than 0.")
                st.stop()
            if entry_price <= 0:
                st.error("Entry price must be greater than 0.")
                st.stop()
            if stop_loss <= 0:
                st.error("Stop loss price must be greater than 0.")
                st.stop()
            if entry_price == stop_loss:
                st.error("Entry price and stop loss cannot be the same.")
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

            # KPI Dashboard
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
                st.metric("R:R Multiple", f"{rr_1_1:.1f}:1")  # Show for 1:1

            st.caption("Position size rounded to whole shares (most brokers don't accept fractional shares).")

            # Percentage Moves
            st.markdown("### Percentage Moves")
            pct_col1, pct_col2 = st.columns(2)
            with pct_col1:
                st.metric("% Drop to Stop", f"{pct_drop_to_stop:.2f}%")
            with pct_col2:
                st.metric("% Move to 1:1 Target", f"{pct_move_to_1_1:.2f}%")

            # Chart
            chart_data = pd.DataFrame({
                'Scenario': ['Risk', '1:1 Profit', '2:1 Profit'],
                'Amount': [risk_amount, abs(profit_1_1 - entry_price) * position_size, abs(profit_2_1 - entry_price) * position_size]
            })
            fig = px.bar(chart_data, x='Scenario', y='Amount', color_discrete_sequence=['#14ffec', '#ff6ec7', '#ffc23c'])
            st.plotly_chart(fig, use_container_width=True)

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
        st.markdown("### Results Preview")
        st.markdown("Fill the form on the left and hit Calculate to see your position sizing, risk metrics, and percentage moves here.")
        st.markdown("---")
        st.markdown(f"** {emoji.emojize(':fire:')} Key Metrics** will show: Position Size, Dollar Risk, Profit Targets, R:R Ratio")
        st.markdown("** Percentage Moves** will display: % Drop to Stop, % Move to 1:1 Target")
        st.markdown("** Risk/Reward Chart** will visualize the scenarios")

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
                    st.metric("R:R Ratio", f"{rr_ratio:.1f}:1")
                
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
    st.caption("RIZZK is a calculator, not a crystal ball. Nothing here is financial advice.")
    st.markdown("*Built with Streamlit — RIZZK by Fuaad Abdullah (GoblinOSRep@gmail.com)*")

except Exception as e:
    st.error("Something went wrong with the calculation. Check your inputs and try again.")
    st.exception(e)  # Show full traceback for debugging
