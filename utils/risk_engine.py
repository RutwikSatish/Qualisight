import numpy as np
import pandas as pd
from utils.validators import normalize_dates

THRESHOLDS = {
    "supplier_ppm_high": 1500,
    "repeat_ncm_high": 0.20,
    "capa_overdue_high": 0.15,
    "batch_delay_hours": 24,
    "missing_fields_high": 3,
}

def risk_scoring(data: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    supplier = data.get("supplier", pd.DataFrame()).copy()
    batch = data.get("batch_release", pd.DataFrame()).copy()

    supplier_risk = pd.DataFrame()
    if not supplier.empty and {"supplier_id", "received_qty", "defect_qty", "scar_days"}.issubset(supplier.columns):
        grp = supplier.groupby("supplier_id", dropna=False).agg(
            received_qty=("received_qty", "sum"),
            defect_qty=("defect_qty", "sum"),
            scar_days=("scar_days", "mean"),
            lots=("lot_id", "nunique") if "lot_id" in supplier.columns else ("supplier_id", "size"),
        ).reset_index()
        grp["ppm"] = np.where(grp["received_qty"] > 0, grp["defect_qty"] / grp["received_qty"] * 1_000_000, np.nan)
        grp["risk_score"] = (
            grp["ppm"].fillna(0) / 1000 * 0.5 +
            grp["scar_days"].fillna(0) * 0.3 +
            grp["defect_qty"].fillna(0) * 0.2
        )
        supplier_risk = grp.sort_values("risk_score", ascending=False)

    batch_risk = pd.DataFrame()
    if not batch.empty and {"batch_id", "missing_fields", "deviation_flag", "approval_time_hours", "release_status"}.issubset(batch.columns):
        batch["missing_fields"] = pd.to_numeric(batch["missing_fields"], errors="coerce").fillna(0)
        batch["approval_time_hours"] = pd.to_numeric(batch["approval_time_hours"], errors="coerce").fillna(0)
        dev = batch["deviation_flag"].astype(str).str.lower().isin(["yes", "y", "true", "1"])
        batch["risk_score"] = (
            batch["missing_fields"] * 2 +
            dev.astype(int) * 4 +
            (batch["approval_time_hours"] > THRESHOLDS["batch_delay_hours"]).astype(int) * 2
        )
        batch["risk_flag"] = np.select(
            [batch["risk_score"] >= 8, batch["risk_score"] >= 4],
            ["High", "Medium"],
            default="Low",
        )
        batch_risk = batch.sort_values(["risk_score", "approval_time_hours"], ascending=[False, False])

    return supplier_risk, batch_risk

def insight_engine(data: dict[str, pd.DataFrame], kpis: dict[str, float]) -> list[str]:
    insights = []
    supplier_risk, batch_risk = risk_scoring(data)
    ncm = data.get("ncm", pd.DataFrame())
    capa = data.get("capa", pd.DataFrame())

    if not supplier_risk.empty:
        top = supplier_risk.iloc[0]
        insights.append(
            f"Supplier {top['supplier_id']} is the highest-risk supplier based on defect volume, SCAR response time, and PPM."
        )

    if not ncm.empty and "defect_category" in ncm.columns:
        top_defect = ncm["defect_category"].astype(str).value_counts().head(1)
        if not top_defect.empty:
            insights.append(
                f"The most frequent non-conformance category is {top_defect.index[0]} ({int(top_defect.iloc[0])} records)."
            )

    if not capa.empty and {"status", "target_close_date"}.issubset(capa.columns):
        temp = normalize_dates(capa, ["target_close_date"])
        overdue = temp[
            (temp["status"].astype(str).str.lower() != "closed") &
            (temp["target_close_date"] < pd.Timestamp.today().normalize())
        ]
        if not overdue.empty:
            insights.append(f"{len(overdue)} CAPA items are overdue and need closure review.")

    if not batch_risk.empty:
        high_batches = batch_risk[batch_risk["risk_flag"] == "High"]
        if not high_batches.empty:
            insights.append(f"{len(high_batches)} batch records are flagged High risk and need immediate review.")

    repeat_ncm = kpis.get("Repeat NCM Rate")
    if pd.notna(repeat_ncm) and repeat_ncm > THRESHOLDS["repeat_ncm_high"]:
        insights.append("Repeat non-conformances are elevated, suggesting incomplete closed-loop correction.")

    if not insights:
        insights.append("No major risk patterns detected in current data.")

    return insights