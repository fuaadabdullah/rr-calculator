# Architecture

## Overview

RIZZK is a focused Streamlit application built around deterministic risk-calculation functions.

## Main components

- `app.py`: UI and interaction flow
- `rizzk_core.py`: core calculation logic
- `test_risk_reward.py`: automated tests for edge cases and correctness

## Design principles

- Keep math logic isolated from UI rendering
- Validate all inputs before calculations
- Keep output explicit and journal-ready
