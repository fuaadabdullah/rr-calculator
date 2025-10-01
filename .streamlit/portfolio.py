from __future__ import annotations

from datetime import datetime, timedelta
import pandas as pd

from rizzk.core.db import positions_df as db_positions_df
from rizzk.core.settings import load_settings
from core.portfolio import load_positions, enrich_with_prices, attach_sectors, load_sectors
from rizzk.providers import current_provider
from rizzk.core.data import get_ohlc_from_settings


def get_broker_positions() -> pd.DataFrame:
    """Fetches positions from the configured broker (e.g., Alpaca)."""
    cfg = load_settings()
    prov_name = (cfg.get("profiles") or {}).get(cfg.get("active_profile",""), {}).get("provider", cfg.get("provider","yf"))
    if prov_name != "alpaca":
        return pd.DataFrame(columns=["symbol", "qty", "avg_price"])

    try:
        prov = current_provider(cfg)
        poss = prov.get_positions()
        rows = [
            {
                "symbol": getattr(p, 'symbol', ''),
                "qty": float(getattr(p, 'qty', 0) or 0),
                "avg_price": float(getattr(p, 'avg_entry_price', 0) or 0),
            }
            for p in poss
        ]
        return pd.DataFrame(rows) if rows else pd.DataFrame(columns=["symbol", "qty", "avg_price"])
    except Exception:
        return pd.DataFrame(columns=["symbol", "qty", "avg_price"])


def get_last_prices(symbols: list[str]) -> dict[str, float]:
    """Fetches the last closing price for a list of symbols."""
    data: dict[str, float] = {}
    end_dt = datetime.now(); start_dt = end_dt - timedelta(days=7)
    for sym in symbols:
        try:
            df = get_ohlc_from_settings(sym, start_dt=start_dt, end_dt=end_dt, interval="1d", adjust=True)
            if df is not None and not df.empty:
                df = df.rename(columns=str.title)
                data[sym] = float(df["Close"].iloc[-1])
        except Exception:
            pass
    return data


def get_combined_positions() -> pd.DataFrame:
    """Combines positions from file, database (paper), and broker."""
    pos_file = load_positions()
    pos_db = db_positions_df()
    pos_broker = get_broker_positions()

    all_syms = set(pos_file["symbol"].tolist()) | set(pos_db["symbol"].tolist()) | set(pos_broker["symbol"].tolist())
    prices = get_last_prices(list(all_syms)) if all_syms else {}
    sectors = load_sectors()

    sources = [("File", pos_file), ("Paper", pos_db), ("Broker", pos_broker)]
    enriched_dfs = []
    for name, df in sources:
        if not df.empty:
            enriched = attach_sectors(enrich_with_prices(df, prices), sectors).assign(source=name)
            enriched_dfs.append(enriched)

    return pd.concat(enriched_dfs, ignore_index=True) if enriched_dfs else pd.DataFrame()
