@'
# app.py — Rizzk: Risk/Reward Calculator
# Tabs, background+logo, Pylance-safe, candlesticks w/ entry/stop/targets
# Robust yfinance fallbacks (download + Ticker.history), symbol normalization,
# no hard st.stop() on data errors, clearer status banners.

from __future__ import annotations

import io
import json
import base64
from pathlib import Path
from typing import Optional, Tuple, List, Dict, TypedDict
from datetime import datetime

import numpy as np  # type: ignore
import pandas as pd  # type: ignore
import streamlit as st
import yfinance as yf  # type: ignore
import plotly.graph_objects as go  # type: ignore


# ==================== PAGE CONFIG ====================
st.set_page_config(page_title="Rizzk: Risk/Reward Calculator", page_icon="🧪", layout="wide")


# ==================== UTILITIES / SAFE CASTERS ====================
def ss_float(key: str, default: float = 0.0) -> float:
    try:
        return float(st.session_state.get(key, default))
    except Exception:
        return default

def ss_str(key: str, default: str = "") -> str:
    try:
        return str(st.session_state.get(key, default))
    except Exception:
        return default

def ss_int(key: str, default: int = 0) -> int:
    try:
        return int(st.session_state.get(key, default))
    except Exception:
        return default

def ss_bool(key: str, default: bool = False) -> bool:
    try:
        return bool(st.session_state.get(key, default))
    except Exception:
        return default

def ss_runs() -> List[Dict[str, object]]:
    if "_runs" not in st.session_state or not isinstance(st.session_state["_runs"], list):
        st.session_state["_runs"] = []
    return st.session_state["_runs"]


# ==================== BACKGROUND & LOGO ====================
def _b64_bytes(b: bytes) -> str:
    return base64.b64encode(b).decode("ascii")

def _try_read_bytes(paths: List[str]) -> Optional[bytes]:
    for p in paths:
        fp = Path(p)
        if fp.exists():
            try:
                return fp.read_bytes()
            except Exception:
                continue
    return None

def apply_background() -> None:
    bg_bytes = _try_read_bytes(["fuaad_bg_glass.png", "background.png", "bg.png"])
    if bg_bytes is not None:
        css = f"""
        <style>
        .stApp {{
            background: url("data:image/png;base64,{_b64_bytes(bg_bytes)}") no-repeat center center fixed;
            background-size: cover;
            background-color: #0b0b12;
        }}
        </style>
        """
    else:
        css = """
        <style>
        .stApp {
            background:
              radial-gradient(circle at 20% 10%, rgba(0,255,220,.08), transparent 40%),
              radial-gradient(circle at 80% 90%, rgba(180,70,255,.10), transparent 45%),
              linear-gradient(#0b0b12, #0b0b12);
        }
        </style>
        """
    st.markdown(css, unsafe_allow_html=True)

def render_header() -> None:
    logo_bytes = _try_read_bytes(["FZ_logo.png", "logo.png", "brand.png"])
    left, right = st.columns([1, 8])
    with left:
        if logo_bytes is not None:
            st.image(logo_bytes, width=64)
    with right:
        st.markdown("## **Rizzk**")
        st.caption("Risk/Reward Calculator • Built by Fuaad Abdullah")

apply_background()
render_header()


# ==================== DEFAULTS / INIT ====================
class Defaults(TypedDict):
    entry: float
    stop: float
    risk_pct: float
    account_size: float
    fees_share: float
    fees_pct: float
    slippage: float
    targets: str
    side: str
    ticker: str
    brand_name: str

DEFAULTS: Defaults = {
    "entry": 100.00,
    "stop": 98.00,
    "risk_pct": 1.00,
    "account_size": 10000.00,
    "fees_share": 0.0000,     # per-share roundtrip
    "fees_pct": 0.00,         # % of notional roundtrip (if used)
    "slippage": 0.0000,       # per-share
    "targets": "1, 1.5, 2, 3",
    "side": "Long",
    "ticker": "AAPL",
    "brand_name": "Rizzk",
}

def init_state() -> None:
    ss = st.session_state
    if ss.get("_init_done"):
        return
    ss["sb_entry_price"] = DEFAULTS["entry"]
    ss["sb_stop_price"] = DEFAULTS["stop"]
    ss["sb_risk_pct"] = DEFAULTS["risk_pct"]
    ss["sb_acct_size"] = DEFAULTS["account_size"]
    ss["sb_fee_model"] = "Per-share fixed"
    ss["sb_fees_share"] = DEFAULTS["fees_share"]
    ss["sb_fees_pct"] = DEFAULTS["fees_pct"]
    ss["sb_slippage"] = DEFAULTS["slippage"]
    ss["sb_r_targets"] = DEFAULTS["targets"]
    ss["sb_side"] = DEFAULTS["side"]
    ss["sb_ticker"] = DEFAULTS["ticker"]
    ss["sb_use_atr"] = False
    ss["sb_atr_len"] = 14
    ss["sb_atr_mult"] = 1.5
    ss["sb_symbols_text"] = "AAPL, MSFT, BTC-USD"
    ss["_runs"] = []
    ss["_init_done"] = True

init_state()


# ==================== DATA HELPERS ====================
def normalize_symbol(sym: str) -> str:
    s = sym.strip().upper()
    aliases: Dict[str, str] = {
        "SPX": "^GSPC",
        "SP500": "^GSPC",
        "SPY500": "SPY",
        "NAS100": "^NDX",
        "NDX100": "^NDX",
        "DOW": "^DJI",
        "BTC": "BTC-USD",
        "ETH": "ETH-USD",
        "EUROUSD": "EURUSD=X",
        "EURUSD": "EURUSD=X",
        "XAUUSD": "XAUUSD=X",
        "GOLD": "XAUUSD=X",
        "SILVER": "XAGUSD=X",
        "ES": "ES=F",
        "NQ": "NQ=F",
        "YM": "YM=F",
        "CL": "CL=F",
        "GC": "GC=F",
    }
    return aliases.get(s, s)

def _yf_has_ohlc(df: pd.DataFrame) -> bool:
    return isinstance(df, pd.DataFrame) and not df.empty and {"Open","High","Low","Close"}.issubset(df.columns)

@st.cache_data(ttl=60)
def fetch_snapshots(symbols: List[str]) -> pd.DataFrame:
    rows: List[Dict[str, Optional[float]]] = []
    for raw in symbols:
        sym = normalize_symbol(raw)
        if not sym:
            continue
        prev_close: Optional[float] = None
        last_price: Optional[float] = None
        try:
            d_daily = yf.download(sym, period="5d", interval="1d", progress=False)  # type: ignore
            if _yf_has_ohlc(daily := d_daily):
                if len(daily.index) >= 2:
                    prev_close = float(daily["Close"].iloc[-2])
            d_intraday = yf.download(sym, period="1d", interval="1m", progress=False)  # type: ignore
            if _yf_has_ohlc(intra := d_intraday):
                close_series = intra["Close"].dropna()
                if not close_series.empty:
                    last_price = float(close_series.iloc[-1])
        except Exception:
            try:
                t = yf.Ticker(sym)
                h5 = t.history(period="5d", interval="1d")  # type: ignore
                if _yf_has_ohlc(h5) and len(h5.index) >= 2:
                    prev_close = float(h5["Close"].iloc[-2])
                h1 = t.history(period="1d", interval="1m")  # type: ignore
                if _yf_has_ohlc(h1):
                    cs = h1["Close"].dropna()
                    if not cs.empty:
                        last_price = float(cs.iloc[-1])
            except Exception:
                pass

        change: Optional[float] = None
        pct: Optional[float] = None
        if last_price is not None and prev_close is not None:
            change = last_price - prev_close
            pct = (change / prev_close * 100.0) if prev_close != 0 else None

        rows.append({
            "Symbol": sym,
            "Price": round(last_price, 4) if last_price is not None else None,
            "Prev Close": round(prev_close, 4) if prev_close is not None else None,
            "Change $": round(change, 4) if change is not None else None,
            "Change %": round(pct, 3) if pct is not None else None,
        })
    return pd.DataFrame(rows, columns=["Symbol", "Price", "Prev Close", "Change $", "Change %"])

@st.cache_data(ttl=60)
def get_fast_price_and_atr(sym: str, length: int) -> Tuple[float, float]:
    sym_n = normalize_symbol(sym)
    hist: pd.DataFrame = pd.DataFrame()
    try:
        hist = yf.Ticker(sym_n).history(period="3mo", interval="1d")[["High", "Low", "Close"]].dropna()  # type: ignore
    except Exception:
        pass
    if hist.empty:
        try:
            hist = yf.download(sym_n, period="3mo", interval="1d", progress=False)[["High", "Low", "Close"]].dropna()  # type: ignore
        except Exception:
            pass

    if hist.empty or len(hist) < max(2, length + 1):
        raise RuntimeError("Insufficient data for ATR")

    h = hist["High"].to_numpy(dtype=float)
    l = hist["Low"].to_numpy(dtype=float)
    c = hist["Close"].to_numpy(dtype=float)

    prev_c = np.roll(c, 1)
    prev_c[0] = c[0]
    tr = np.maximum(h - l, np.maximum(np.abs(h - prev_c), np.abs(l - prev_c)))
    atr = float(np.mean(tr[-int(length):]))
    last = float(c[-1])
    return last, atr

@st.cache_data(ttl=120)
def load_candles(sym_raw: str) -> pd.DataFrame:
    sym = normalize_symbol(sym_raw)
    plans: List[Tuple[str, str]] = [
        ("1d", "1m"),
        ("5d", "5m"),
        ("1mo", "15m"),
        ("3mo", "1h"),
        ("6mo", "1d"),
        ("2y", "1d"),
        ("5y", "1d"),
        ("max", "1wk"),
    ]
    last_err: Optional[Exception] = None

    for period, interval in plans:
        try:
            df = yf.download(sym, period=period, interval=interval, progress=False)  # type: ignore
            if _yf_has_ohlc(df):
                df = df.dropna(subset=["Open","High","Low","Close"]).copy()
                try:
                    df["Time"] = df.index.tz_convert(None)
                except Exception:
                    if hasattr(df.index, "tz_localize"):
                        try:
                            df["Time"] = df.index.tz_localize(None)
                        except Exception:
                            df["Time"] = df.index
                    else:
                        df["Time"] = df.index
                return df
        except Exception as e:
            last_err = e

    try:
        t = yf.Ticker(sym)
        for period, interval in [("1mo","1d"), ("6mo","1d"), ("2y","1d"), ("max","1wk")]:
            try:
                df2 = t.history(period=period, interval=interval)  # type: ignore
                if _yf_has_ohlc(df2):
                    df2 = df2.dropna(subset=["Open","High","Low","Close"]).copy()
                    df2["Time"] = df2.index
                    return df2
            except Exception as e:
                last_err = e
    except Exception as e:
        last_err = e

    try:
        test = yf.download("AAPL", period="5d", interval="1d", progress=False)  # type: ignore
        network_ok = isinstance(test, pd.DataFrame) and not test.empty
    except Exception:
        network_ok = False

    out = pd.DataFrame(columns=["Time", "Open", "High", "Low", "Close"])
    out.attrs["__load_error__"] = {
        "symbol": sym,
        "network_ok": network_ok,
        "last_error": str(last_err) if last_err else None
    }
    return out


def parse_targets(s: str) -> List[float]:
    out: List[float] = []
    for tok in s.split(","):
        tok_clean = tok.strip().upper().replace("R", "")
        if not tok_clean:
            continue
        try:
            val = float(tok_clean)
            if val > 0:
                out.append(val)
        except Exception:
            continue
    return out


def make_candle_fig(df: pd.DataFrame,
                    sym: str,
                    entry: Optional[float],
                    stop: Optional[float],
                    target_prices: List[float],
                    side: str) -> go.Figure:
    fig = go.Figure()
    if df.empty:
        fig.update_layout(title=f"{sym} — no data", template="plotly_white", height=420)
        return fig

    fig.add_trace(go.Candlestick(
        x=df["Time"], open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
        name=sym, showlegend=False
    ))

    shapes: List[Dict[str, object]] = []
    annotations: List[Dict[str, object]] = []

    def add_line(y: float, label: str, color: str) -> None:
        shapes.append(dict(type="line", xref="x", yref="y",
                           x0=df["Time"].iloc[0], x1=df["Time"].iloc[-1], y0=y, y1=y,
                           line=dict(color=color, width=1.5, dash="dot")))
        annotations.append(dict(x=df["Time"].iloc[-1], y=y, xref="x", yref="y",
                                xanchor="left", showarrow=False, text=label,
                                font=dict(size=10, color=color)))

    if entry is not None and entry > 0:
        add_line(entry, f"Entry {entry:.4f}", "#1f77b4")
    if stop is not None and stop > 0:
        add_line(stop, f"Stop {stop:.4f}", "#d62728")

    t_color = "#2ca02c" if side == "Long" else "#9467bd"
    for i, tp in enumerate(target_prices, start=1):
        add_line(tp, f"T{i} {tp:.4f}", t_color)

    fig.update_layout(
        template="plotly_white",
        height=520,
        margin=dict(l=10, r=10, t=35, b=10),
        title=f"{normalize_symbol(sym)} — Candlesticks with Entry/Stop/Targets",
        xaxis=dict(showgrid=False, rangeslider=dict(visible=False)),
        yaxis=dict(showgrid=True, gridcolor="rgba(200,200,200,0.2)"),
        shapes=shapes,
        annotations=annotations,
    )
    return fig


# ==================== LAYOUT: TABS ====================
tab_calc, tab_market, tab_about = st.tabs(["📊 Calculator", "🌐 Market Data", "ℹ️ About"])


# -------------------- TAB: CALCULATOR --------------------
with tab_calc:
    with st.container():
        st.markdown("### Inputs")
        c1, c2, c3, c4 = st.columns([1,1,1,1])
        with c1:
            st.number_input("Account size ($)", min_value=0.0, step=100.0, format="%.2f", key="sb_acct_size")
        with c2:
            st.number_input("Risk per trade (%)", min_value=0.0, max_value=100.0, step=0.1, format="%.2f", key="sb_risk_pct")
        with c3:
            st.selectbox("Side", ["Long", "Short"], key="sb_side")
        with c4:
            st.text_input("Ticker (for ATR & chart)", key="sb_ticker")

        c5, c6, c7 = st.columns([1,1,1])
        with c5:
            st.number_input("Entry", min_value=0.0, step=0.01, format="%.4f", key="sb_entry_price")
        with c6:
            st.number_input("Stop", min_value=0.0, step=0.01, format="%.4f", key="sb_stop_price")
        with c7:
            st.number_input("Slippage/share", min_value=0.0, step=0.0001, format="%.4f", key="sb_slippage")

        c8, c9 = st.columns([1,1])
        with c8:
            st.selectbox("Fee model", ["Per-share fixed", "Percent of notional (roundtrip)"], key="sb_fee_model")
        with c9:
            if ss_str("sb_fee_model") == "Per-share fixed":
                st.number_input("Fees per share (RT)", min_value=0.0, step=0.0001, format="%.4f", key="sb_fees_share")
            else:
                st.number_input("Fees % of notional (RT)", min_value=0.0, step=0.01, format="%.4f", key="sb_fees_pct")

        st.checkbox("Use ATR-based stop (overrides Stop)", key="sb_use_atr")
        ac1, ac2 = st.columns([1,1])
        with ac1:
            st.number_input("ATR length", min_value=5, max_value=50, step=1, key="sb_atr_len")
        with ac2:
            st.number_input("ATR multiple", min_value=0.5, max_value=5.0, step=0.1, format="%.1f", key="sb_atr_mult")

        st.text_input("R targets (comma)", key="sb_r_targets")

        if st.button("Reset to defaults"):
            reset = {
                "sb_entry_price": DEFAULTS["entry"],
                "sb_stop_price": DEFAULTS["stop"],
                "sb_risk_pct": DEFAULTS["risk_pct"],
                "sb_acct_size": DEFAULTS["account_size"],
                "sb_fee_model": "Per-share fixed",
                "sb_fees_share": DEFAULTS["fees_share"],
                "sb_fees_pct": DEFAULTS["fees_pct"],
                "sb_slippage": DEFAULTS["slippage"],
                "sb_r_targets": DEFAULTS["targets"],
                "sb_side": DEFAULTS["side"],
                "sb_ticker": DEFAULTS["ticker"],
                "sb_use_atr": False,
                "sb_atr_len": 14,
                "sb_atr_mult": 1.5,
            }
            for k, v in reset.items():
                st.session_state[k] = v
            st.rerun()

    # --------------- CALC LOGIC ---------------
    entry_val = ss_float("sb_entry_price")
    stop_val = ss_float("sb_stop_price")
    riskpct_val = ss_float("sb_risk_pct")
    acct_val = ss_float("sb_acct_size")
    side_val = ss_str("sb_side")
    fees_share = ss_float("sb_fees_share")
    fees_pct = ss_float("sb_fees_pct") / 100.0
    slip_val = ss_float("sb_slippage")
    fee_model = ss_str("sb_fee_model")
    sym = ss_str("sb_ticker").strip().upper()

    if ss_bool("sb_use_atr") and sym and entry_val > 0:
        try:
            _, atr = get_fast_price_and_atr(sym, ss_int("sb_atr_len", 14))
            mult = ss_float("sb_atr_mult", 1.5)
            stop_val = entry_val - mult * atr if side_val == "Long" else entry_val + mult * atr
            st.info(f"ATR stop used: {stop_val:.4f} (ATR {atr:.4f} × {mult})")
        except Exception as e:
            st.warning(f"ATR unavailable: {e}")

    if entry_val <= 0 or stop_val <= 0:
        st.error("Entry and Stop must be greater than 0.")
    elif side_val == "Long" and stop_val >= entry_val:
        st.error("For Long, Stop must be below Entry.")
    elif side_val == "Short" and stop_val <= entry_val:
        st.error("For Short, Stop must be above Entry.")

    per_share_risk = abs(entry_val - stop_val) if entry_val > 0 and stop_val > 0 else 0.0

    fee_rt_ps = max(fees_share, 0.0) if fee_model == "Per-share fixed" else max(entry_val * fees_pct, 0.0)

    risk_amount = acct_val * (riskpct_val / 100.0)
    denom = (per_share_risk + fee_rt_ps + max(slip_val, 0.0)) if per_share_risk > 0 else 0.0
    shares = int(risk_amount // denom) if denom > 0 else 0
    shares = max(shares, 0)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Position size", f"{shares}")
    m2.metric("Per-share risk", f"${per_share_risk:.4f}")
    m3.metric("Fee/Share (RT)", f"${fee_rt_ps:.4f}")
    est_stop_loss = -shares * (per_share_risk + fee_rt_ps + max(slip_val, 0.0)) if shares > 0 else 0.0
    m4.metric("Est. stop-out PnL", f"${est_stop_loss:.2f}")

    r_list = parse_targets(ss_str("sb_r_targets"))
    rows: List[Dict[str, float]] = []
    direction = 1 if side_val == "Long" else -1
    target_prices: List[float] = []
    if per_share_risk > 0:
        for r in r_list:
            tgt_price = entry_val + direction * r * per_share_risk
            move = tgt_price - entry_val
            net_per_share = direction * move - (fee_rt_ps + max(slip_val, 0.0))
            net_pnl = shares * net_per_share
            rr = abs(move) / per_share_risk if per_share_risk else 0.0
            rows.append({
                "R": float(r),
                "Target price": round(float(tgt_price), 4),
                "Move ($)": round(float(move), 4),
                "R:R": round(float(rr), 2),
                "Est. PnL ($)": round(float(net_pnl), 2),
            })
            target_prices.append(float(tgt_price))

    st.markdown("### Targets")
    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True)
        s = io.StringIO()
        df.to_csv(s, index=False)
        st.download_button("Download targets CSV", s.getvalue(), "targets.csv", "text/csv")
    else:
        st.info("Add valid Entry/Stop and R levels like `1, 2, 3` to see target prices.")

    st.markdown("### Candlestick")
    if sym:
        candle_df = load_candles(sym)
        if candle_df.empty:
            meta = candle_df.attrs.get("__load_error__", {})
            sym_norm = normalize_symbol(sym)
            if meta.get("network_ok") is False:
                st.error("No data due to network/rate limit. Retry in ~60–120 seconds or switch networks/VPN.")
            else:
                st.warning(
                    f"No data for '{sym}' (normalized '{sym_norm}'). "
                    "Try a mainstream ticker (AAPL, MSFT, SPY, BTC-USD) or Yahoo FX/Futures format "
                    "(EURUSD=X, XAUUSD=X, ES=F, NQ=F)."
                )
        else:
            fig = make_candle_fig(
                candle_df, sym,
                entry=entry_val if entry_val > 0 else None,
                stop=stop_val if stop_val > 0 else None,
                target_prices=target_prices,
                side=side_val,
            )
            st.plotly_chart(fig, use_container_width=True, theme="streamlit")
    else:
        st.caption("Enter a ticker to render candlesticks.")

    ticket = f"""# {DEFAULTS['brand_name']} Trade Ticket
- Ticker: **{normalize_symbol(sym) or 'N/A'}** ({side_val})
- Entry: ${entry_val:.4f} | Stop: ${stop_val:.4f}
- Risk %: {riskpct_val:.2f}% | Account: ${acct_val:.2f}
- Shares: {shares} | Fee/Share (RT): ${fee_rt_ps:.4f} | Slippage: ${slip_val:.4f}
- Targets: {ss_str('sb_r_targets')}
- Est. stop-out PnL: ${est_stop_loss:.2f}
- Timestamp: {datetime.now().isoformat(timespec="seconds")}
"""
    st.download_button("Download trade ticket (.md)", ticket, "trade_ticket.md")

    if rows and shares:
        ss_runs().append({
            "ts": datetime.now().isoformat(timespec="seconds"),
            "sym": normalize_symbol(sym), "side": side_val,
            "entry": round(entry_val, 4), "stop": round(stop_val, 4),
            "risk_pct": round(riskpct_val, 2), "acct": round(acct_val, 2),
            "shares": shares, "targets": ss_str("sb_r_targets", ""),
            "fee_rt_ps": round(fee_rt_ps, 6), "slip_ps": round(slip_val, 6),
            "est_stop_pnl": round(est_stop_loss, 2),
        })

    with st.expander("Session history"):
        hist_df = pd.DataFrame(ss_runs())
        if not hist_df.empty:
            st.dataframe(hist_df, use_container_width=True)
            s2 = io.StringIO()
            hist_df.to_csv(s2, index=False)
            st.download_button("Download history CSV", s2.getvalue(), "rizzk_session.csv", "text/csv")
        else:
            st.caption("No runs yet this session.")


# -------------------- TAB: MARKET DATA --------------------
with tab_market:
    st.markdown("### Market Snapshots")
    with st.form("market_form", clear_on_submit=False):
        st.text_input("Symbols (comma)", key="sb_symbols_text")
        refresh = st.form_submit_button("↻ Refresh data")

    symbols = [s.strip() for s in ss_str("sb_symbols_text", "AAPL, MSFT, BTC-USD").split(",") if s.strip()]

    if refresh or "market_df" not in st.session_state:
        st.session_state["market_df"] = fetch_snapshots(symbols)
        st.session_state["market_last_updated"] = datetime.now()

    market_df = st.session_state.get("market_df", pd.DataFrame())
    if isinstance(market_df, pd.DataFrame) and not market_df.empty:
        ts = st.session_state.get("market_last_updated")
        if isinstance(ts, datetime):
            st.caption(f"Last updated: {ts.strftime('%Y-%m-%d %I:%M:%S %p')}")
        st.dataframe(market_df, use_container_width=True)

        pick_list = ["—"] + market_df["Symbol"].dropna().astype(str).tolist()
        pick = st.selectbox("Show candlesticks for", pick_list)
        if pick != "—":
            mdf = load_candles(pick)
            if mdf.empty:
                st.warning(f"No chartable data for '{normalize_symbol(pick)}' at tested intervals.")
            else:
                fig2 = make_candle_fig(mdf, pick, entry=None, stop=None, target_prices=[], side="Long")
                st.plotly_chart(fig2, use_container_width=True, theme="streamlit")

        s3 = io.StringIO()
        market_df.to_csv(s3, index=False)
        st.download_button("Download snapshot CSV", s3.getvalue(), "market_snapshot.csv", "text/csv")
    else:
        st.info("No market data yet. Enter symbols and refresh.")


# -------------------- TAB: ABOUT --------------------
with tab_about:
    st.markdown("### About")
    st.write(
        "This tool helps you size positions using risk multiples, fees, and optional ATR-based stops. "
        "It also renders candlestick charts with entry/stop/target overlays. Data comes from Yahoo Finance via yfinance; "
        "availability can vary by symbol, market hours, and rate limits."
    )
    st.markdown(
        "> **Disclaimer**: Educational tool only. Not investment, tax, or legal advice. "
        "Trading involves substantial risk. Verify all numbers independently."
    )
    st.caption("© 2025 Fuaad Abdullah · Rizzk")
'@ | Out-File -Encoding utf8 app.py

