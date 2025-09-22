import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Risk/Reward Trade Calculator", page_icon="📈")

st.title("📈 Risk/Reward Position Sizing Calculator")
st.write("Tiny app, big discipline. Figure out position size, R-multiples, and targets without frying your account.")

with st.sidebar:
    st.header("Account & Risk")
    account_size = st.number_input("Account size ($)", min_value=0.0, value=10000.0, step=100.0, format="%.2f", key="acct_size")
    risk_pct = st.number_input("Risk per trade (%)", min_value=0.0, max_value=100.0, value=1.0, step=0.25, format="%.2f", key="risk_pct")
    max_leverage = st.number_input("Max leverage (optional)", min_value=1.0, value=1.0, step=0.5)

    st.header("Trade Setup")
    side = st.selectbox("Side", ["Long", "Short"])
    entry = st.number_input("Entry price", min_value=0.0, value=100.0, step=0.01, format="%.4f",key="entry_price")
    stop = st.number_input("Stop price", min_value=0.0, value=98.0, step=0.01, format="%.4f")

    st.header("Frictions (Optional)")
    fee_per_share = st.number_input("Fees per share ($)", min_value=0.0, value=0.0, step=0.001, format="%.4f")
    slippage_per_share = st.number_input("Slippage per share ($)", min_value=0.0, value=0.0, step=0.001, format="%.4f",key="slippage")

    st.header("Targets")
    r_targets = st.text_input("R targets (comma-separated)", value="1, 1.5, 2, 3")

# Core calculations
risk_amount = account_size * (risk_pct / 100.0)

# Effective risk per share depends on side and friction
price_diff = None
if side == "Long":
    price_diff = max(entry - stop, 0.0)
else:
    price_diff = max(stop - entry, 0.0)

friction = fee_per_share + slippage_per_share
risk_per_share = price_diff + friction

# Guard rails
if account_size <= 0:
    st.error("Account size must be greater than 0.")
if risk_pct <= 0:
    st.warning("Risk percent is 0. Position size will be 0. Try something like 0.5% to 2%.")
if price_diff == 0:
    st.error("Entry and stop are the same or inverted. Fix that before you donate to the market.")

# Compute position size (floor to whole shares)
if risk_per_share > 0 and risk_amount > 0:
    raw_shares = risk_amount / risk_per_share
else:
    raw_shares = 0

# Leverage cap uses notional value: shares * entry <= account_size * max_leverage
if entry > 0:
    leverage_cap_shares = (account_size * max_leverage) / entry
else:
    leverage_cap_shares = 0

shares = int(np.floor(min(raw_shares, leverage_cap_shares)))

# Notional exposure and dollar risk
notional = shares * entry
risk_dollars = shares * risk_per_share

col1, col2, col3 = st.columns(3)
col1.metric("Shares", f"{shares}")
col2.metric("Risk $", f"${risk_dollars:,.2f}")
col3.metric("Notional", f"${notional:,.2f}")

# Build R table
r_vals = []
for part in r_targets.split(','):
    try:
        r = float(part.strip())
        if r <= 0:
            continue
        r_vals.append(r)
    except ValueError:
        continue
r_vals = sorted(set(r_vals))

rows = []
if shares > 0 and price_diff > 0:
    for R in r_vals:
        if side == "Long":
            target_price = entry + R * price_diff
            pnl_per_share = (target_price - entry) - friction
        else:
            target_price = entry - R * price_diff
            pnl_per_share = (entry - target_price) - friction
        pnl_total = max(0.0, pnl_per_share * shares)  # conservative, can't be negative at target
        rr = pnl_total / risk_dollars if risk_dollars > 0 else 0
        rows.append({
            "R": R,
            "Target Price": round(target_price, 4),
            "PnL per Share": round(pnl_per_share, 4),
            "Total PnL $": round(pnl_total, 2),
            "R Multiple": round(rr, 3),
        })

if rows:
    df = pd.DataFrame(rows)
    st.subheader("Targets")
    st.dataframe(df, use_container_width=True)
else:
    st.info("Enter valid numbers to see targets. I promise it works when you do.")

# Amortized ATR-style helper: suggest stop distance as a % of price
st.divider()
st.subheader("Quick Helpers")
colA, colB, colC = st.columns(3)
with colA:
    pct = st.number_input("Suggest stop as % of entry", min_value=0.1, max_value=50.0, value=1.0, step=0.1, help="Example: 1% stop distance")
with colB:
    if entry > 0:
        suggested_dist = entry * (pct / 100.0)
        st.write(f"Suggested stop distance: {suggested_dist:.4f}")
with colC:
    if side == "Long" and entry > 0:
        st.write(f"Stop at: {(entry - suggested_dist):.4f}")
    elif side == "Short" and entry > 0:
        st.write(f"Stop at: {(entry + suggested_dist):.4f}")

st.caption("This is educational, not financial advice. If you YOLO anyway, at least size correctly.")
import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Risk/Reward Trade Calculator", page_icon="📈")

st.title("📈 Risk/Reward Position Sizing Calculator")
st.write("Tiny app, big discipline. Figure out position size, R-multiples, and targets.")

with st.sidebar:
    st.header("Account & Risk")
    account_size = st.number_input("Account size ($)", min_value=0.0, value=10000.0, step=100.0, format="%.2f", key="acct_size")
    risk_pct = st.number_input("Risk per trade (%)", min_value=0.0, max_value=100.0, value=1.0, step=0.25, format="%.2f", key="risk_pct")
    max_leverage = st.number_input("Max leverage (optional)", min_value=1.0, value=1.0, step=0.5)

    st.header("Trade Setup")
    side = st.selectbox("Side", ["Long", "Short"])
    entry = st.number_input("Entry price", min_value=0.0, value=100.0, step=0.01, format="%.4f", key="entry_price")
    stop = st.number_input("Stop price", min_value=0.0, value=98.0, step=0.01, format="%.4f",key="stop_price")

    st.header("Frictions (Optional)")
    fee_per_share = st.number_input("Fees per share ($)", min_value=0.0, value=0.0, step=0.001, format="%.4f", key="fee_per_share")
    slippage_per_share = st.number_input("Slippage per share ($)", min_value=0.0, value=0.0, step=0.001, format="%.4f", key="slippage")

    st.header("Targets")
    r_targets = st.text_input("R targets (comma-separated)", value="1, 1.5, 2, 3")

risk_amount = account_size * (risk_pct / 100.0)

if side == "Long":
    price_diff = max(entry - stop, 0.0)
else:
    price_diff = max(stop - entry, 0.0)

friction = fee_per_share + slippage_per_share
risk_per_share = price_diff + friction

if account_size <= 0:
    st.error("Account size must be greater than 0.")
if risk_pct <= 0:
    st.warning("Risk percent is 0. Try something like 0.5% to 2%.")
if price_diff == 0:
    st.error("Entry and stop are the same or inverted.")

raw_shares = (risk_amount / risk_per_share) if (risk_per_share > 0 and risk_amount > 0) else 0
leverage_cap_shares = ((account_size * max_leverage) / entry) if entry > 0 else 0
shares = int(np.floor(min(raw_shares, leverage_cap_shares)))

notional = shares * entry
risk_dollars = shares * risk_per_share

col1, col2, col3 = st.columns(3)
col1.metric("Shares", f"{shares}")
col2.metric("Risk $", f"${risk_dollars:,.2f}")
col3.metric("Notional", f"${notional:,.2f}")

# Build R table
r_vals = []
for part in r_targets.split(","):
    try:
        r = float(part.strip())
        if r > 0:
            r_vals.append(r)
    except ValueError:
        pass
r_vals = sorted(set(r_vals))

rows = []
if shares > 0 and price_diff > 0 and risk_dollars > 0:
    for R in r_vals:
        if side == "Long":
            target_price = entry + R * price_diff
            pnl_per_share = (target_price - entry) - friction
        else:
            target_price = entry - R * price_diff
            pnl_per_share = (entry - target_price) - friction
        pnl_total = max(0.0, pnl_per_share * shares)
        rr = pnl_total / risk_dollars if risk_dollars > 0 else 0
        rows.append({
            "R": R,
            "Target Price": round(target_price, 4),
            "PnL per Share": round(pnl_per_share, 4),
            "Total PnL $": round(pnl_total, 2),
            "R Multiple": round(rr, 3),
        })

if rows:
    st.subheader("Targets")
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True)
else:
    st.info("Enter valid numbers to see targets.")

st.divider()
st.subheader("Quick Helpers")
colA, colB, colC = st.columns(3)
with colA:
    pct = st.number_input("Suggest stop as % of entry", min_value=0.1, max_value=50.0, value=1.0, step=0.1)
with colB:
    if entry > 0:
        suggested_dist = entry * (pct / 100.0)
        st.write(f"Suggested stop distance: {suggested_dist:.4f}")
with colC:
    if side == "Long" and entry > 0:
        st.write(f"Stop at: {(entry - suggested_dist):.4f}")
    elif side == "Short" and entry > 0:
        st.write(f"Stop at: {(entry + suggested_dist):.4f}")

st.caption("Educational, not financial advice. Size responsibly.")
st.set_page_config(page_title="Risk/Reward Trade Calculator", page_icon="🧪")

st.markdown(
    """
    <div style="padding:14px 18px;border-radius:16px;background:linear-gradient(135deg,#7c3aed33,#06b6d433);border:1px solid #2a2a3a;">
      <h1 style="margin:0;font-size:1.6rem;">🧪 Risk/Reward Position Sizing</h1>
      <p style="margin:6px 0 0;color:#b9b9c9;">Trade like you meant it, not like you guessed.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Account & Risk")
    account_size = st.number_input("Account size ($)", min_value=0.0, value=10000.0, step=100.0, format="%^.2", key="acct_size")
st.number_input







