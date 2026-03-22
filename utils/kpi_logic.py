import numpy as np
import pandas as pd
from utils.validators import normalize_dates

def calculate_kpis(data: dict[str, pd.DataFrame]) -> dict[str, float]:
    complaints = data.get("complaints", pd.DataFrame())
    ncm = data.get("ncm", pd.DataFrame())
    capa = data.get("capa", pd.DataFrame())
    supplier = data.get("supplier", pd.DataFrame())
    batch = data.get("batch_release", pd.DataFrame())

    complaint_count = float(len(complaints))

    capa_closed_rate = np.nan
    if not capa.empty and "status" in capa.columns:
        capa_closed_rate = capa["status"].astype(str).str.lower().eq("closed").mean()

    repeat_ncm_rate = np.nan
    if not ncm.empty and "root_cause" in ncm.columns:
        root_counts = ncm["root_cause"].astype(str).value_counts()
        repeated = root_counts[root_counts > 1].sum()
        repeat_ncm_rate = repeated / len(ncm) if len(ncm) else np.nan

    supplier_ppm = np.nan
    if not supplier.empty and {"received_qty", "defect_qty"}.issubset(supplier.columns):
        total_received = pd.to_numeric(supplier["received_qty"], errors="coerce").fillna(0).sum()
        total_defects = pd.to_numeric(supplier["defect_qty"], errors="coerce").fillna(0).sum()
        supplier_ppm = (total_defects / total_received) * 1_000_000 if total_received else np.nan

    batch_tat = np.nan
    if not batch.empty and "approval_time_hours" in batch.columns:
        batch_tat = pd.to_numeric(batch["approval_time_hours"], errors="coerce").mean()

    dhr_completeness = np.nan
    if not batch.empty and "missing_fields" in batch.columns:
        missing = pd.to_numeric(batch["missing_fields"], errors="coerce").fillna(0)
        dhr_completeness = (missing == 0).mean()

    overdue_capa = np.nan
    if not capa.empty and {"target_close_date", "closed_date", "status"}.issubset(capa.columns):
        temp = normalize_dates(capa, ["target_close_date", "closed_date"])
        today = pd.Timestamp.today().normalize()
        overdue = (
            (temp["status"].astype(str).str.lower() != "closed") &
            (temp["target_close_date"].notna()) &
            (temp["target_close_date"] < today)
        )
        overdue_capa = overdue.mean()

    return {
        "Complaint Count": complaint_count,
        "CAPA Closure Rate": capa_closed_rate,
        "Repeat NCM Rate": repeat_ncm_rate,
        "Supplier PPM": supplier_ppm,
        "Batch Release TAT (hrs)": batch_tat,
        "DHR Complete Rate": dhr_completeness,
        "Overdue CAPA Rate": overdue_capa,
    }

def month_series(df: pd.DataFrame, date_col: str, value_name: str) -> pd.DataFrame:
    if date_col not in df.columns or df.empty:
        return pd.DataFrame(columns=["month", value_name])
    temp = df.copy()
    temp[date_col] = pd.to_datetime(temp[date_col], errors="coerce")
    temp = temp.dropna(subset=[date_col])
    if temp.empty:
        return pd.DataFrame(columns=["month", value_name])
    temp["month"] = temp[date_col].dt.to_period("M").astype(str)
    return temp.groupby("month").size().reset_index(name=value_name)