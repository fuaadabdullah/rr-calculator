# Architecture

## Overview

RIZZK is a focused Streamlit application built around deterministic risk-calculation functions.

## Main components

- `app.py`: Streamlit UI, form handling, metric rendering, chart output, and history state.
- `rizzk_core.py`: centralized calculation logic for position sizing and risk/reward math.
- `test_risk_reward.py`: validation of core calculation correctness and edge behavior.
- `assets/`: static media used in docs/README.

## Calculation flow

1. User enters account size, entry, stop loss, and risk mode.
2. UI validates inputs and forwards values to `rizzk_core.py`.
3. Core function returns sizing outputs, risk amount, and profit targets.
4. UI renders metrics, percentage moves, and chart visualizations.
5. Session history stores prior runs for quick comparison.

## Deployment topology

- Primary host target: Streamlit Community Cloud.
- Local run path: `streamlit run app.py`.
- Runtime dependencies are intentionally minimal for quick startup.
