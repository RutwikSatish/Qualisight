import pandas as pd

REQUIRED_COLUMNS = {
    "complaints": ["complaint_id", "date", "product", "defect_category", "severity", "root_cause", "status"],
    "ncm": ["ncm_id", "date", "line", "defect_category", "severity", "root_cause", "capa_linked", "status"],
    "capa": ["capa_id", "opened_date", "target_close_date", "closed_date", "root_cause", "status", "effectiveness"],
    "supplier": ["supplier_id", "lot_id", "received_qty", "defect_qty", "defect_category", "scar_days", "status"],
    "batch_release": ["batch_id", "date", "reviewer", "missing_fields", "deviation_flag", "approval_time_hours", "release_status"],
}

def find_missing_columns(df: pd.DataFrame, required: list[str]) -> list[str]:
    return [c for c in required if c not in df.columns]

def normalize_dates(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    out = df.copy()
    for c in cols:
        if c in out.columns:
            out[c] = pd.to_datetime(out[c], errors="coerce")
    return out