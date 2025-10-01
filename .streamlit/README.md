# RizzK Trading Terminal

## Front-end

Run the Streamlit interface:

```bash
streamlit run rizzk_pro.py
```

## Backend automation service

1. Install dependencies (includes FastAPI, APScheduler, watchdog):
   ```bash
   pip install -r requirements.txt
   ```
2. Export environment variables as needed:
   ```bash
   set RIZZK_VAULT=C:\Users\you\Documents\Obsidian\Rizzk
   set RIZZK_BACKEND_URL=http://127.0.0.1:8756
   ```
3. Start the API and job runner:
   ```bash
   uvicorn backend.app:app --host 127.0.0.1 --port 8756
   ```
4. Streamlit will auto-detect the backend status in the sidebar and use `/kpi/daily` for the journal tab summary.

For Windows service instructions see [`backend/README.md`](backend/README.md).
