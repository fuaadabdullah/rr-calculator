---
description: "README"
---

# RIZZK Calculator

RIZZK Calculator (pronounced "Rizz-k") — sharp, refined position-sizing for traders who think in probabilities and move with style.

Author: Fuaad Abdullah

Default UI: Polished emoji mode is the default. Use the sidebar "🦇 mode (ASCII emoticons)" toggle to switch to the ASCII-emoticon experience.

## Live Demo

🚀 [Try the live demo here](https://rr-calculator-2tywogeksqdgr4hf4jzssm.streamlit.app/)

![RIZZK Calculator Screenshot](assets/rizzk-demo.svg)

## What this is

- 🦇, polished Streamlit app to compute position size, stop-loss impact, and profit targets. Built for traders who want clean numbers without the fluff.

## Who this is for

Day traders, students, and new traders who want disciplined risk sizing.

## This is not

Not a signal service. Not financial advice. Just math with taste.

## Key Features

- Position sizing from account size and risk % or fixed-dollar mode with inline validation
- Long and short support with adaptive stop guidance
- Always-visible live summary (position size, $ risk, % risk, R multiple)
- Shareable URLs: inputs are encoded in query params for quick permalinks
- 1:1 and 2:1 profit targets plus copy-to-clipboard helpers
- Downloadable CSV and session-scoped calculation history
- Clean UI with charts, responsive design, and branding trust cues (build version shown in footer)

## Local Development

If you want to run locally:

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Usage

Fill the inputs: account size, risk %, entry, stop. Hit Calculate. Export CSV if you want to log the trade.

## Alternative UI

For a different visual experience, run the demo version:

```bash
streamlit run demo_app.py
```

This provides an alternative interface with different styling and layout.

## Deployment

Two easy paths:

- Azure App Service (no container):
  - Set runtime to Python 3.11
  - Deploy this folder with `requirements.txt` present
  - Startup command: `python -m streamlit run app.py --server.port 8000 --server.address 0.0.0.0`

- Container (Azure Web App for Containers, ACI, ECS):
  - Build using the Dockerfile in this directory as build context:

    ```bash
    docker build -t rizzk:latest .
    docker run -p 8501:8501 rizzk:latest
    ```

  - Push to a registry (e.g., ACR) and point your service at the image

Note: The app expects no secrets; `EDGY_MODE_DEFAULT` env can optionally be set to `true`/`false` to toggle the default UI mode.

## Testing

Unit tests live under `apps/python/rizzk-calculator/risk_reward_calculator/tests/test_rizzk_core.py` and exercise the pure calculation helpers (no Streamlit dependency).

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt  # optional if you already have deps
python -m unittest apps/python/rizzk-calculator/risk_reward_calculator/tests/test_rizzk_core.py
```

The suite asserts correct sizing math for both risk modes, validates percentage move helpers, and checks error handling for invalid trades.

## Tech

- Python 3.11
- Streamlit
- Pandas
- Python’s unittest (core calculation tests)

## Engineering Approach

Built with production-grade practices: comprehensive type hints, thorough unit testing with edge case coverage, modular architecture, and safety-first error handling. The core calculation logic is battle-tested against extreme scenarios to ensure reliability in high-stakes trading environments.

## Tone

RIZZK is designed to be direct and pragmatic — modern, confident, and professional with an edge.

## License

MIT
