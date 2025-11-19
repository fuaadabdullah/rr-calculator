import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="RIZZK Calculator", page_icon="⚡️", layout="wide")

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #FFD700;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #888;
        text-align: center;
        margin-bottom: 1rem;
        letter-spacing: 0.05em;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
        margin: 0.5rem;
    }
    .success-msg {
        background-color: #d4edda;
        color: #155724;
        padding: 0.75rem;
        border-radius: 0.25rem;
        margin: 1rem 0;
    }
    .stButton>button[data-testid="stBaseButton-primary"] {
        background-color: #FFD700 !important;
        color: #000 !important;
        border: none !important;
    }
    .stButton>button[data-testid="stBaseButton-primary"]:hover {
        background-color: #FFC107 !important;
        color: #000 !important;
    }
</style>
""", unsafe_allow_html=True)

if 'history' not in st.session_state:
    st.session_state.history = []

try:
    with st.sidebar:
        st.markdown("## About")
        st.markdown("**Fuaad Abdullah** — Builder & Trader")
        st.markdown("[✉️ GoblinOSRep@gmail.com](mailto:GoblinOSRep@gmail.com)")
        st.markdown("Built by a day trader to turn risk management into a first-class habit.")
        st.markdown("---")
        st.markdown("_Edgy, refined, numbers-first. RIZZK is for traders who keep it sharp._")

    st.markdown('<h1 class="main-header">⚡ RIZZK Calculator</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Refined risk. Raw edge. Position sizing for traders who know their RIZZ.</p>', unsafe_allow_html=True)

    st.caption("Example numbers. Tune to your own playbook.")

    col_left, col_right = st.columns([1, 1.5])

    with col_left:
        with st.form("rizzk_form"):
            # Add position type selector
            position_type = st.selectbox("Position Type", ["Long", "Short"], index=0)

            # Risk mode toggle
            risk_mode = st.radio("Risk Mode", ["% of Account", "Fixed $ Amount"], index=0, horizontal=True)

            col1, col2 = st.columns(2)

            with col1:
                account_size = st.number_input("Account Size ($)", min_value=0.0, value=10000.0, step=100.0, help="Total trading account balance")
                if risk_mode == "% of Account":
                    risk_percentage = st.number_input("Risk Percentage (%)", min_value=0.0, max_value=100.0, value=1.0, step=0.1, help="Percentage of account to risk per trade")
                else:
                    risk_amount_input = st.number_input("Risk Amount ($)", min_value=0.0, value=100.0, step=10.0, help="Fixed dollar amount to risk per trade")

            with col2:
                entry_price = st.number_input("Entry Price ($)", min_value=0.0, value=100.0, step=0.1, help="Price at which you plan to enter the trade")
                stop_loss = st.number_input("Stop Loss Price ($)", min_value=0.0, value=95.0, step=0.1, help="Price at which you will exit if the trade goes against you")

            submitted = st.form_submit_button("Calculate", type="primary")

    with col_right:
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

            # Risk validation
            if risk_mode == "% of Account":
                if risk_percentage <= 0 or risk_percentage > 100:
                    st.error("Risk percentage must be between 0 and 100.")
                    st.stop()
                risk_amount = account_size * (risk_percentage / 100)
            else:
                if risk_amount_input <= 0:
                    st.error("Risk amount must be greater than 0.")
                    st.stop()
                if risk_amount_input > account_size:
                    st.error("Risk amount cannot exceed account size.")
                    st.stop()
                risk_amount = risk_amount_input

            if position_type == "Long":
                if entry_price <= stop_loss:
                    st.error("Entry price must be higher than stop loss for long positions.")
                    st.stop()
                position_size = risk_amount / (entry_price - stop_loss)
                stop_loss_amount = position_size * (entry_price - stop_loss)
                profit_1_1 = entry_price + (entry_price - stop_loss)
                profit_2_1 = entry_price + 2 * (entry_price - stop_loss)
                pct_drop_to_stop = ((entry_price - stop_loss) / entry_price) * 100
                pct_move_to_1_1 = ((profit_1_1 - entry_price) / entry_price) * 100
            else:  # Short
                if entry_price >= stop_loss:
                    st.error("Entry price must be lower than stop loss for short positions.")
                    st.stop()
                position_size = risk_amount / (stop_loss - entry_price)
                stop_loss_amount = position_size * (stop_loss - entry_price)
                profit_1_1 = entry_price - (stop_loss - entry_price)
                profit_2_1 = entry_price - 2 * (stop_loss - entry_price)
                pct_drop_to_stop = ((stop_loss - entry_price) / entry_price) * 100
                pct_move_to_1_1 = ((entry_price - profit_1_1) / entry_price) * 100

            st.markdown('<div class="success-msg">Calculation Complete!</div>', unsafe_allow_html=True)

            # KPI Dashboard
            st.markdown("### Key Metrics")
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("Position Size", f"{position_size:.2f} shares")
            with col2:
                st.metric("Dollar Risk", f"${risk_amount:.2f}")
            with col3:
                st.metric("1:1 Target", f"${profit_1_1:.2f}")
            with col4:
                st.metric("2:1 Target", f"${profit_2_1:.2f}")
            with col5:
                rr_ratio = 1.0 if '1:1' in str(profit_1_1) else 2.0  # simplistic, but since both are calculated, perhaps show 1:1 ratio
                # Actually, calculate properly
                if position_type == "Long":
                    rr_1_1 = (profit_1_1 - entry_price) / (entry_price - stop_loss)
                    rr_2_1 = (profit_2_1 - entry_price) / (entry_price - stop_loss)
                else:
                    rr_1_1 = (entry_price - profit_1_1) / (stop_loss - entry_price)
                    rr_2_1 = (entry_price - profit_2_1) / (stop_loss - entry_price)
                st.metric("R:R Multiple", f"{rr_1_1:.1f}:1")  # Show for 1:1

            st.caption("Rounded to whole shares on your broker.")

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
            fig = px.bar(chart_data, x='Scenario', y='Amount', color_discrete_sequence=['#FFD700', '#FFD700', '#FFD700'])
            st.plotly_chart(fig, width='stretch')

            # Export results
            results_df = pd.DataFrame({
                'Metric': ['Position Size', 'Risk Amount', 'Stop Loss Impact', 'Profit 1:1', 'Profit 2:1'],
                'Value': [f"{position_size:.2f} shares", f"${risk_amount:.2f}", f"${stop_loss_amount:.2f}", f"${profit_1_1:.2f}", f"${profit_2_1:.2f}"]
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
                'risk_amount': risk_amount,
                'profit_1_1': profit_1_1,
                'profit_2_1': profit_2_1
            }
            st.session_state.history.append(calc)
        else:
            st.markdown("### Results Preview (⌐■_■)")
            st.markdown("Fill the form and hit Calculate — results show here: position size, dollar risk, targets, and R:R.")
            st.markdown("---")
            st.markdown("**Key Metrics** will show: Position Size, Dollar Risk, Profit Targets, R:R Ratio")
            st.markdown("**Percentage Moves** will display: % Drop to Stop, % Move to 1:1 Target")
            st.markdown("**Risk/Reward Chart** will visualize the scenarios")

    st.markdown("---")
    st.header("📊 Calculation History")
    if st.session_state.history:
        recent = st.session_state.history[-5:]
        for i, h in enumerate(reversed(recent), start=1):
            with st.expander(f"Calc {i}: {h['position_type']}"):
                # Calculate additional metrics
                if h['position_type'] == "Long":
                    pct_drop_to_stop = ((h['entry_price'] - h['stop_loss']) / h['entry_price']) * 100
                    pct_move_to_1_1 = ((h['profit_1_1'] - h['entry_price']) / h['entry_price']) * 100
                    rr_ratio = (h['profit_1_1'] - h['entry_price']) / (h['entry_price'] - h['stop_loss'])
                else:
                    pct_drop_to_stop = ((h['stop_loss'] - h['entry_price']) / h['entry_price']) * 100
                    pct_move_to_1_1 = ((h['entry_price'] - h['profit_1_1']) / h['entry_price']) * 100
                    rr_ratio = (h['entry_price'] - h['profit_1_1']) / (h['stop_loss'] - h['entry_price'])

                hist_col1, hist_col2, hist_col3, hist_col4 = st.columns(4)
                with hist_col1:
                    st.metric("Account", f"${h['account_size']}")
                    st.metric("Entry", f"${h['entry_price']}")
                with hist_col2:
                    risk_label = "%" if h.get('risk_mode', '% of Account') == '% of Account' else "$"
                    st.metric("Risk", f"{h['risk_input']}{risk_label}")
                    st.metric("Stop", f"${h['stop_loss']}")
                with hist_col3:
                    st.metric("Position", f"{h['position_size']:.2f} shares")
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
    if st.button("🧹 Clear All History"):
        st.session_state.history = []
        st.rerun()
    st.caption("This only clears local session history, not your broker. Sadly.")

    st.markdown("---")
    st.markdown("*Built with Streamlit — RIZZK by Fuaad Abdullah*")

except Exception as e:
    st.error(f"An error occurred: {e}")
