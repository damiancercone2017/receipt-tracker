import streamlit as st
import pandas as pd
from extractor import extract_from_file
from exporter import to_excel, to_csv

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Receipt Tracker | Future-Forward Concepts",
    page_icon="🧾",
    layout="wide",
)

# ── Branding CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* Header banner */
.ffc-header {
    background: linear-gradient(90deg, #2D1B69 0%, #3d2590 100%);
    padding: 18px 32px;
    border-radius: 10px;
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.ffc-header .brand { color: #fff; font-size: 22px; font-weight: 700; letter-spacing: -0.3px; }
.ffc-header .brand span { color: #E8824A; }
.ffc-header .tagline { color: #c4b8f0; font-size: 13px; font-weight: 400; }

/* Section labels */
.section-label {
    font-size: 11px; font-weight: 700; letter-spacing: 1.5px;
    color: #2D1B69; text-transform: uppercase; margin-bottom: 8px;
}

/* Metric cards */
.metric-row { display: flex; gap: 16px; margin-bottom: 24px; }
.metric-card {
    flex: 1; background: #fff; border: 1px solid #e0d9f5;
    border-radius: 10px; padding: 16px 20px;
    border-left: 4px solid #E8824A;
}
.metric-card .label { font-size: 11px; color: #7B68C8; font-weight: 600;
    text-transform: uppercase; letter-spacing: 1px; }
.metric-card .value { font-size: 26px; font-weight: 700; color: #2D1B69; margin-top: 4px; }

/* Warning / low-confidence badge */
.badge-warn {
    background: #FFF3CD; color: #856404; font-size: 11px;
    padding: 2px 8px; border-radius: 20px; font-weight: 600;
}
.badge-ok {
    background: #D4EDDA; color: #155724; font-size: 11px;
    padding: 2px 8px; border-radius: 20px; font-weight: 600;
}

/* Button overrides */
div.stButton > button {
    border-radius: 8px; font-weight: 600; border: none;
}
div.stButton > button:first-child {
    background: #E8824A; color: white;
}
div.stButton > button:first-child:hover { background: #d4703a; }

/* Divider */
.ffc-divider { border: none; border-top: 1px solid #e0d9f5; margin: 24px 0; }
</style>
""", unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="ffc-header">
  <div>
    <div class="brand">Future-Forward Concepts <span>LLC</span></div>
    <div class="tagline">Receipt Tracker — Prototype v0.1</div>
  </div>
  <div style="color:#c4b8f0; font-size:13px;">🧾 AI-powered expense capture</div>
</div>
""", unsafe_allow_html=True)

# ── Session state init ────────────────────────────────────────────────────────
if "expenses" not in st.session_state:
    st.session_state.expenses = []
if "confirm_clear" not in st.session_state:
    st.session_state.confirm_clear = False

# ── API key ───────────────────────────────────────────────────────────────────
try:
    api_key = st.secrets["ANTHROPIC_API_KEY"]
except Exception:
    api_key = None

if not api_key:
    st.error("⚠️  **API key not found.** Add `ANTHROPIC_API_KEY` to your Streamlit secrets.", icon="🔑")
    st.stop()

# ── SECTION 1: Upload & Scan ──────────────────────────────────────────────────
st.markdown('<div class="section-label">Step 1 — Upload Receipts</div>', unsafe_allow_html=True)

uploaded_files = st.file_uploader(
    "Drag and drop receipts here, or click to browse",
    type=["jpg", "jpeg", "png", "pdf"],
    accept_multiple_files=True,
    label_visibility="collapsed",
)

scan_col, _ = st.columns([1, 4])
with scan_col:
    scan_clicked = st.button("🔍  Scan Receipts", use_container_width=True)

if scan_clicked and uploaded_files:
    progress = st.progress(0, text="Starting scan...")
    results_log = []

    for i, f in enumerate(uploaded_files):
        progress.progress((i) / len(uploaded_files), text=f"Scanning {f.name}…")
        try:
            result = extract_from_file(f.read(), f.name, api_key)

            # Flag likely duplicates using vendor + date + amount.
            duplicate = any(
                (existing.get("vendor") or "").strip().lower() == (result.get("vendor") or "").strip().lower()
                and (existing.get("date") or "") == (result.get("date") or "")
                and float(existing.get("amount") or 0) == float(result.get("amount") or 0)
                for existing in st.session_state.expenses
            )

            if duplicate:
                results_log.append(f"⚠️ {f.name}: possible duplicate — not added")
            else:
                st.session_state.expenses.append(result)
                results_log.append(f"✅ {f.name}")
        except Exception as e:
            results_log.append(f"❌ {f.name}: {e}")

    progress.progress(1.0, text="Done!")
    for msg in results_log:
        st.caption(msg)

elif scan_clicked and not uploaded_files:
    st.warning("Please upload at least one receipt first.")

st.markdown('<hr class="ffc-divider">', unsafe_allow_html=True)

# ── SECTION 2: Expense Table ──────────────────────────────────────────────────
st.markdown('<div class="section-label">Step 2 — Review Expenses</div>', unsafe_allow_html=True)

expenses = st.session_state.expenses

if expenses:
    # Metrics
    total = sum(e.get("amount") or 0 for e in expenses)
    categories = {}
    for e in expenses:
        cat = e.get("category") or "Other"
        categories[cat] = categories.get(cat, 0) + (e.get("amount") or 0)
    top_cat = max(categories, key=categories.get) if categories else "—"

    st.markdown(f"""
    <div class="metric-row">
      <div class="metric-card">
        <div class="label">Total Expenses</div>
        <div class="value">${total:,.2f}</div>
      </div>
      <div class="metric-card">
        <div class="label">Receipts Scanned</div>
        <div class="value">{len(expenses)}</div>
      </div>
      <div class="metric-card">
        <div class="label">Top Category</div>
        <div class="value" style="font-size:20px">{top_cat}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Category filter
    all_cats = sorted(set(e.get("category") or "Other" for e in expenses))
    filter_col, _ = st.columns([2, 5])
    with filter_col:
        selected_cat = st.selectbox("Filter by category", ["All"] + all_cats)

    filtered = expenses if selected_cat == "All" else [
        e for e in expenses if (e.get("category") or "Other") == selected_cat
    ]

    # Build an editable dataframe. Keep the source index so edits map back
    # to the correct session-state record even when a category filter is used.
    filtered_pairs = [
        (idx, e) for idx, e in enumerate(expenses)
        if selected_cat == "All" or (e.get("category") or "Other") == selected_cat
    ]

    rows = []
    for source_index, e in filtered_pairs:
        rows.append({
            "_source_index": source_index,
            "Delete": False,
            "Date": e.get("date") or "",
            "Vendor": e.get("vendor") or "",
            "Category": e.get("category") or "Other",
            "Amount": float(e.get("amount") or 0),
            "Payment Method": e.get("payment_method") or "",
            "Notes": e.get("notes") or "",
            "Confidence": "Low" if e.get("confidence") == "low" else "High",
            "File": e.get("source_file") or "",
        })

    df = pd.DataFrame(rows)
    edited_df = st.data_editor(
        df,
        use_container_width=True,
        hide_index=True,
        disabled=["_source_index", "Confidence", "File"],
        column_config={
            "_source_index": None,
            "Delete": st.column_config.CheckboxColumn(
                "Delete",
                help="Select rows to remove, then click Save Changes.",
                default=False,
                width="small",
            ),
            "Date": st.column_config.TextColumn(width="small"),
            "Vendor": st.column_config.TextColumn(width="medium"),
            "Category": st.column_config.SelectboxColumn(
                options=["Meals", "Office Supplies", "Travel", "Software", "Utilities", "Other"],
                required=True,
                width="medium",
            ),
            "Amount": st.column_config.NumberColumn(
                format="$%.2f",
                min_value=0.0,
                step=0.01,
                width="small",
            ),
            "Payment Method": st.column_config.TextColumn(width="medium"),
            "Notes": st.column_config.TextColumn(width="large"),
            "Confidence": st.column_config.TextColumn(width="small"),
            "File": st.column_config.TextColumn(width="medium"),
        },
        key="expense_editor",
    )

    save_col, _ = st.columns([1, 4])
    with save_col:
        if st.button("💾 Save Changes", use_container_width=True):
            delete_indices = set()

            for _, row in edited_df.iterrows():
                source_index = int(row["_source_index"])

                if bool(row["Delete"]):
                    delete_indices.add(source_index)
                    continue

                expense = st.session_state.expenses[source_index]
                expense["date"] = str(row["Date"]).strip() or None
                expense["vendor"] = str(row["Vendor"]).strip() or None
                expense["category"] = str(row["Category"]).strip() or "Other"
                expense["amount"] = float(row["Amount"]) if pd.notna(row["Amount"]) else None
                expense["payment_method"] = str(row["Payment Method"]).strip() or None
                expense["notes"] = str(row["Notes"]).strip() or None

            if delete_indices:
                st.session_state.expenses = [
                    expense for idx, expense in enumerate(st.session_state.expenses)
                    if idx not in delete_indices
                ]

            st.success("Expense log updated.")
            st.rerun()

    if any(e.get("confidence") == "low" for e in filtered):
        st.caption("⚠️ Rows marked **Low** had ambiguous fields — review and edit as needed.")

else:
    st.info("No expenses yet. Upload receipts and click **Scan Receipts** to get started.", icon="📂")

st.markdown('<hr class="ffc-divider">', unsafe_allow_html=True)

# ── SECTION 3: Export ─────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Step 3 — Export</div>', unsafe_allow_html=True)

exp_col1, exp_col2, exp_col3, _ = st.columns([1, 1, 1, 4])

with exp_col1:
    if expenses:
        xlsx_bytes = to_excel(expenses)
        st.download_button(
            "⬇ Download Excel",
            data=xlsx_bytes,
            file_name="expenses_ffc.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    else:
        st.button("⬇ Download Excel", disabled=True, use_container_width=True)

with exp_col2:
    if expenses:
        csv_bytes = to_csv(expenses)
        st.download_button(
            "⬇ Download CSV",
            data=csv_bytes,
            file_name="expenses_ffc.csv",
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.button("⬇ Download CSV", disabled=True, use_container_width=True)

with exp_col3:
    if expenses and not st.session_state.confirm_clear:
        if st.button("🗑 Clear Session", use_container_width=True):
            st.session_state.confirm_clear = True
            st.rerun()
    elif expenses:
        st.warning("Clear all receipts?")
        confirm_col, cancel_col = st.columns(2)
        with confirm_col:
            if st.button("Yes, clear", use_container_width=True):
                st.session_state.expenses = []
                st.session_state.confirm_clear = False
                st.rerun()
        with cancel_col:
            if st.button("Cancel", use_container_width=True):
                st.session_state.confirm_clear = False
                st.rerun()
    else:
        st.button("🗑 Clear Session", disabled=True, use_container_width=True)
