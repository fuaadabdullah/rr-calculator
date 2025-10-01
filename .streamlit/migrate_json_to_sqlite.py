from __future__ import annotations
import json
import shutil
from datetime import datetime
from pathlib import Path

from rizzk.core.db import init_db, add_note, add_alert, save_layout, save_preset

DATA = Path("data")


def _load_json(p: Path, default):
    try:
        return json.loads(p.read_text()) if p.exists() else default
    except Exception:
        return default


def migrate():
    init_db()
    # Journal
    journal = _load_json(DATA / "journal.json", [])
    for rec in journal:
        ts = rec.get("ts")
        sym = rec.get("symbol")
        text = rec.get("text", "")
        tags = rec.get("tags", [])
        add_note(sym, text, tags)
    # Alerts
    alerts = _load_json(DATA / "alerts.json", [])
    for a in alerts:
        sym = a.get("symbol"); op = a.get("op"); price = a.get("price")
        if sym and op and price is not None:
            add_alert(sym, op, float(price))
    # Layouts
    layouts = _load_json(DATA / "layouts.json", {})
    for name, state in layouts.items():
        save_layout(name, state)
    # Presets (screener)
    presets = _load_json(DATA / "screener_presets.json", {"presets": {}}).get("presets", {})
    for name, cfg in presets.items():
        save_preset(name, cfg, kind="screener")

    # Archive old files
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    arc = DATA / "archive" / stamp
    arc.mkdir(parents=True, exist_ok=True)
    for fname in ["journal.json", "alerts.json", "layouts.json", "screener_presets.json"]:
        p = DATA / fname
        if p.exists():
            shutil.move(str(p), str(arc / fname))
    print(f"Migration complete. Archived originals under {arc}")


if __name__ == "__main__":
    migrate()
