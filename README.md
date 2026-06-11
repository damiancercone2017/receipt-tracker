# Receipt Tracker
**Future-Forward Concepts LLC** — AI-powered receipt scanning and expense tracking.

## What it does
Upload receipt images or PDFs → Claude AI extracts the data → expenses populate a table → export to Excel or CSV.

## Local Setup

```bash
git clone https://github.com/damiancercone2017/receipt-tracker.git
cd receipt-tracker
pip install -r requirements.txt
```

Create `.streamlit/secrets.toml` (never commit this file):
```toml
ANTHROPIC_API_KEY = "sk-ant-..."
```

Run locally:
```bash
streamlit run app.py
```

## Deploy to Streamlit Community Cloud

1. Push this repo to GitHub (secrets.toml is gitignored — safe to push)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub account → select this repo → set `app.py` as the entry point
4. Under **Advanced settings → Secrets**, add:
   ```
   ANTHROPIC_API_KEY = "sk-ant-..."
   ```
5. Click **Deploy** — your app will be live at `your-app-name.streamlit.app`

## Supported File Types
- JPG / JPEG
- PNG
- PDF (first page extracted)

## Notes
- Session only — data clears on browser refresh (by design for prototype)
- PDF support requires `poppler` installed on the host (Streamlit Cloud includes it)
- Low-confidence extractions are flagged in the table for manual review
