# Setup

## Prerequisites

- Python 3.10+
- pip

## Environment options

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `EDGY_MODE_DEFAULT` | No | `false` | Sets default UI mode at startup |

## Install

```bash
pip install -r requirements.txt
```

## Run locally

```bash
streamlit run app.py
```

## Test

```bash
pytest test_risk_reward.py -v
```

## Deploy to Streamlit Cloud

1. Connect this repository in Streamlit Community Cloud.
2. Set startup file to `app.py`.
3. Keep app visibility set to **Public** for recruiter access.
4. Redeploy after every canonical update.

## Troubleshooting

- If app redirects to Streamlit auth, verify visibility is set to Public in app settings.
- If package errors occur, re-run `pip install -r requirements.txt` in a clean environment.
