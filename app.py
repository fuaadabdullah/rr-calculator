import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timezone

# ---------------- Branding & page setup ----------------
APP_OWNER = "Fuaad Abdullah"
BRAND_TAG = f"Built by {APP_OWNER} • © 2025"
st.set_page_config(page_title="Risk/Reward Trade Calculator", page_icon="🧪")

st.markdown(
    f"""
    <div style="padding:14px 18px;border-radius:16px;background:linear-gradient(135deg,#7c3aed33,#06b6d433);border:1px solid #2a2a3a;">
      <h1 style="margin:0;font-size:1.6rem;">🧪 Risk/Reward Position Sizing</h1>
      <p style="margin:6px 0 0;color:#b9b9c9;">Trade like you meant it, not like you guessed.</p>
      <p style="margin:6px 0 0;color:#8a8a9a;font-size:.9rem;">{BRAND_TAG}</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------- Defaults ----------------
DEFAULTS = {
    "account_size": 10000.0,
    "risk_pct": 1.0,
    "entry": 100.0,
    "stop": 98.0,
    "fees": 0.0,
    "slip": 0.0,
    "targets": "1, 1.5, 2, 3",
    "symbols": "AAPL, MSFT, BTC-USD",
    "max_leverage": 1.0,
    "side": "Long 🟢",
}

# initialize once
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.sb_acct_size = DEFAULTS["account_size"]
    st.session_state.sb_risk_pct = DEFAULTS["risk_pct"]
    st.session_state.sb_max_lev = DEFAULTS["max_leverage"]
    st.session_state.sb_side_pick = DEFAULTS["side"]
    st.session_state.sb_entry_price = DEFAULTS["entry"]
    st.session_state.sb_stop_price = DEFAULTS["stop"]
    st.session_state.sb_fee_ps = DEFAULTS["fees"]
    st.session_state.sb_slip_ps = DEFAULTS["slip"]
    st.session_state.sb_r_targets = DEFAULTS["targets"]
    st.session_state.sb_symbols_text = DEFAULTS["symbols"]
    st.session_state.market_df = pd.DataFrame()
    st.session_state.market_last_updated = None

# One-click reset
if st.button("⚡ Fuaad Mode (reset defaults)", key="btn_reset_defaults"):
    for k, v in DEFAULTS.items():
        if k == "max_leverage":
            st.session_state["sb_max_lev"] = v
        elif k == "side":
            st.session_state["sb_side_pick"] = v
        elif k == "account_size":
            st.session_state["sb_acct_size"] = v
        elif k == "risk_pct":
            st.session_state["sb_risk_pct"] = v
        elif k == "entry":
            st.session_state["sb_entry_price"] = v
        elif k == "stop":
            st.session_state["sb_stop_price"] = v
        elif k == "fees":
            st.session_state["sb_fee_ps"] = v
        elif k == "slip":
            st.session_state["sb_slip_ps"] = v
        elif k == "targets":
            st.session_state["sb_r_targets"] = v
        elif k == "symbols":
            st.session_state["sb_symbols_text"] = v
    st.rerun()

# ---------------- CACHED data fetchers ----------------
@st.cache_data(ttl=60)  # 60s cache so rapid reruns don't spam downloads
def fetch_snapshots(symbols: list[str]) -> pd.DataFrame:
    out = []
    for sym in symbols:
        s = sym.strip().upper()
        if not s:
            continue
        try:
            d_daily = yf.download(s, period="5d", interval="1d", progress=False)
            prev_close = float(d_daily["Close"].iloc[-2]) if len(daily := d_daily) >= 2 else float("nan")

            d_intraday = yf.download(s, period="1d", interval="1m", progress=False)
            last_price = float(d_intraday["Close"].dropna().iloc[-1]) if len(d_intraday) else float("nan")

            change = (last_price - prev_close) if (np.isfinite(last_price) and np.isfinite(prev_close)) else float("nan")
            pct = (change / prev_close * 100) if (np.isfinite(prev_close) and prev_close != 0) else float("nan")

            out.append({
                "Symbol": s,
                "Price": round(last_price, 4) if np.isfinite(last_price) else None,
                "Prev Close": round(prev_close, 4) if np.isfinite(prev_close) else None,
                "Change $": round(change, 4) if np.isfinite(change) else None,
                "Change %": round(pct, 3) if np.isfinite(pct) else None,
            })
        except Exception:
            out.append({"Symbol": s, "Price": None, "Prev Close": None, "Change $": None, "Change %": None})
    cols = ["Symbol","Price","Prev Close","Change $","Change %"]
    return pd.DataFrame(out, columns=cols) if out else pd.DataFrame(columns=cols)

# ---------------- Sidebar: one FORM to rule them all ----------------
with st.sidebar:
    with st.form("inputs_form", clear_on_submit=False):
        st.header("Account & Risk")
        account_size = st.number_input(
            "Account size ($)", min_value=0.0, value=st.session_state.sb_acct_size,
            step=100.0, format="%.2f", key="sb_acct_size"
        )
        risk_pct = st.number_input(
            "Risk per trade (%)", min_value=0.0, max_value=100.0, value=st.session_state.sb_risk_pct,
            step=0.25, key="sb_risk_pct"
        )
        max_leverage = st.number_input(
            "Max leverage (x)", min_value=1.0, value=st.session_state.sb_max_lev, step=0.5, key="sb_max_lev"
        )

        st.header("Trade Setup")
        side = st.selectbox("Side", ["Long 🟢", "Short 🔴"], index=0 if "Long" in st.session_state.sb_side_pick else 1, key="sb_side_pick")
        entry = st.number_input(
            "Entry", min_value=0.0, value=st.session_state.sb_entry_price, step=0.01, format="%.4f", key="sb_entry_price"
        )
        stop = st.number_input(
            "Stop", min_value=0.0, value=st.session_state.sb_stop_price, step=0.01, format="%.4f", key="sb_stop_price"
        )

        st.header("Friction")
        fee_per_share = st.number_input(
            "Fees/share", min_value=0.0, value=st.session_state.sb_fee_ps, step=0.001, format="%.4f", key="sb_fee_ps"
        )
        slippage_per_share = st.number_input(
            "Slippage/share", min_value=0.0, value=st.session_state.sb_slip_ps, step=0.001, format="%.4f", key="sb_slip_ps"
        )

        st.header("Targets")
        r_targets = st.text_input("R targets (comma)", value=st.session_state.sb_r_targets, key="sb_r_targets")

        st.header("Market Data")
        symbols_text = st.text_input("Symbols (comma)", value=st.session_state.sb_symbols_text, key="sb_symbols_text")

        submitted = st.form_submit_button("Calculate")

    # separate refresh to avoid re-submitting the whole form
    refresh = st.button("↻ Refresh market data", key="sb_refresh_btn")

# Refresh market data on explicit click
symbols = [s.strip() for s in st.session_state.get("sb_symbols_text", DEFAULTS["symbols"]).split(",")]
if refresh:
    st.session_state.market_df = fetch_snapshots(symbols)
    st.session_state.market_last_updated = datetime.now(timezone.utc)

# If we have no snapshot yet, fetch once
if st.session_state.market_df.empty:
    st.session_state.market_df = fetch_snapshots(symbols)
    st.session_state.market_last_updated = datetime.now(timezone.utc)

# ---------------- Calculations: only when user submits, or on first load ----------------
run_calcs = submitted or ("_first_run_done" not in st.session_state)
if run_calcs:
    st.session_state._first_run_done = True

normalized_side = "Short" if "Short" in st.session_state.sb_side_pick else "Long"
risk_amount = st.session_state.sb_acct_size * (st.session_state.sb_risk_pct / 100.0)

# price distance and friction
if normalized_side == "Long":
    price_diff = max(st.session_state.sb_entry_price - st.session_state.sb_stop_price, 0.0)
else:
    price_diff = max(st.session_state.sb_stop_price - st.session_state.sb_entry_price, 0.0)

friction = st.session_state.sb_fee_ps + st.session_state.sb_slip_ps
risk_per_share = price_diff + friction

# guard rails
if st.session_state.sb_acct_size <= 0:
    st.error("Account size must be greater than 0.")
if st.session_state.sb_risk_pct <= 0:
    st.warning("Risk percent is 0. Try 0.5% to 2%.")
if price_diff == 0:
    st.error("Entry and stop are the same or inverted.")

# shares from risk and leverage caps
raw_shares = (risk_amount / risk_per_share) if (risk_per_share > 0 and risk_amount > 0) else 0
lev_cap_shares = ((st.session_state.sb_acct_size * st.session_state.sb_max_lev) / st.session_state.sb_entry_price) if st.session_state.sb_entry_price > 0 else 0
shares = int(np.floor(min(raw_shares, lev_cap_shares))) if run_calcs else 0

notional = shares * st.session_state.sb_entry_price
risk_dollars = shares * risk_per_share

c1, c2, c3 = st.columns(3)
c1.metric("Size (shares)", f"{shares}")
c2.metric("Risk $", f"${risk_dollars:,.2f}")
c3.metric("Notional", f"${notional:,.2f}")
if shares == int(np.floor(lev_cap_shares)) and shares > 0:
    st.info("Leverage cap hit. Increase max leverage or lower entry price to size up.")

# parse R targets
r_vals = []
for part in st.session_state.sb_r_targets.split(","):
    try:
        r = float(part.strip())
        if r > 0:
            r_vals.append(r)
    except ValueError:
        pass
r_vals = sorted(set(r_vals))

# targets table
rows = []
if shares > 0 and price_diff > 0 and risk_dollars > 0:
    for R in r_vals:
        if normalized_side == "Long":
            target_price = st.session_state.sb_entry_price + R * price_diff
            pnl_per_share = (target_price - st.session_state.sb_entry_price) - friction
        else:
            target_price = st.session_state.sb_entry_price - R * price_diff
            pnl_per_share = (st.session_state.sb_entry_price - target_price) - friction
        pnl_total = max(0.0, pnl_per_share * shares)
        rr = pnl_total / risk_dollars if risk_dollars > 0 else 0
        rows.append({
            "R": R,
            "Target Price": round(target_price, 4),
            "PnL per Share": round(pnl_per_share, 4),
            "Total PnL $": round(pnl_total, 2),
            "R Multiple": round(rr, 3),
        })

st.subheader("Targets")
if rows:
    df = pd.DataFrame(rows)

    def color_pnl(val):
        try:
            return "background-color: rgba(34,197,94,.18)" if float(val) > 0 else ""
        except Exception:
            return ""

    st.dataframe(df.style.applymap(color_pnl, subset=["Total PnL $"]), use_container_width=True)

    # CSV export
    csv_targets = df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download targets (CSV)", data=csv_targets, file_name="targets.csv", mime="text/csv")
else:
    st.info("Enter valid numbers to see targets.")

# ---------------- Market data view ----------------
st.subheader("Live Snapshots")
market_df = st.session_state.market_df
if not market_df.empty:
    if st.session_state.market_last_updated:
        st.caption(f"Last updated: {st.session_state.market_last_updated.astimezone().strftime('%Y-%m-%d %I:%M:%S %p %Z')}")
    st.dataframe(market_df, use_container_width=True)

    pick = st.selectbox("Use price for Entry", ["—"] + market_df["Symbol"].tolist(), key="pick_use_price")
    if pick != "—":
        row = market_df[market_df["Symbol"] == pick]
        if not row.empty and row["Price"].notna().iloc[0]:
            new_entry = float(row["Price"].iloc[0])
            st.session_state["sb_entry_price"] = new_entry
            st.success(f"Entry set to {pick}: {new_entry}")
            st.rerun()

    # CSV export for market data
    csv_market = market_df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download market snapshot (CSV)", data=csv_market, file_name="market_snapshot.csv", mime="text/csv")

# ---------------- Footer ----------------
st.markdown(
    f"<div style='margin-top:16px;opacity:.6;font-size:.85rem'>{BRAND_TAG}</div>",
    unsafe_allow_html=True
)
