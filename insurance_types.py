import pandas as pd
from pathlib import Path
from database import SessionLocal
from models import (
    InsuranceType,
    InsuranceTypeMapping,
    InsuranceTypeCommission,
)
from services.date_service import convert_shamsi_to_date
def import_insurance_types_from_excel(excel_path=None):
    db = SessionLocal()
    try:
        if excel_path is None:
            excel_path = (
                Path(__file__).resolve().parent
                / "data"
                / "insurance_types.xlsx"
            )
        else:
            excel_path = Path(excel_path)

        df = pd.read_excel(
            excel_path,
            sheet_name="Sheet1",
        )
        # کلید:
        # (نام والد, نام رشته)
        #
        # مثال:
        # (None, "خودرو")
        # ("خودرو", "بدنه")
        # ("خودرو", "شخص ثالث")
        insurance_map = {}
        # -----------------------------
        # Import / Update Insurance Types
        # -----------------------------
        for _, row in df.iterrows():
            name = str(row["name"]).strip()
            parent_name = None
            if pd.notna(row["parent"]):
                parent_name = str(row["parent"]).strip()
            parent = None
            if parent_name:
                # ابتدا از رکوردهایی که در همین Import پیدا شده‌اند
                # والد را پیدا می‌کنیم.
                parent_candidates = [
                    insurance_type
                    for (
                        mapped_parent_name,
                        mapped_name
                    ), insurance_type in insurance_map.items()
                    if mapped_name == parent_name
                ]
                if len(parent_candidates) == 1:
                    parent = parent_candidates[0]
                elif len(parent_candidates) > 1:
                    raise ValueError(
                        f"نام والد «{parent_name}» "
                        f"تکراری است و در Excel قابل تشخیص نیست."
                    )
                else:
                    # اگر در Import فعلی پیدا نشد،
                    # از دیتابیس پیدا می‌کنیم.
                    parent_candidates = (
                        db.query(InsuranceType)
                        .filter(
                            InsuranceType.name == parent_name
                        )
                        .all()
                    )
                    if len(parent_candidates) == 1:
                        parent = parent_candidates[0]
                    elif len(parent_candidates) == 0:
                        raise ValueError(
                            f"والد «{parent_name}» "
                            f"برای رشته «{name}» پیدا نشد."
                        )
                    else:
                        raise ValueError(
                            f"چند رشته با نام والد "
                            f"«{parent_name}» وجود دارد و "
                            f"والد رشته «{name}» قابل تشخیص نیست."
                        )
            parent_id = parent.id if parent else None
            map_key = (
                parent_name,
                name,
            )
            insurance_type = (
                db.query(InsuranceType)
                .filter(
                    InsuranceType.name == name,
                    InsuranceType.parent_id == parent_id,
                )
                .first()
            )
            # -----------------------------
            # اگر وجود نداشت، ایجاد می‌شود
            # -----------------------------
            if not insurance_type:
                has_mortgage = bool(
                    row["has_mortgage"]
                )
                insurance_type = InsuranceType(
                    name=name,
                    parent=parent,
                    has_mortgage=has_mortgage,
                    display_name=row["display_name"],
                )
                db.add(insurance_type)
                db.flush()
            # -----------------------------
            # اگر وجود داشت، Update می‌شود
            # -----------------------------
            else:
                insurance_type.display_name = (
                    row["display_name"]
                )
                insurance_type.has_mortgage = bool(
                    row["has_mortgage"]
                )
            insurance_map[map_key] = insurance_type
        # -----------------------------
        # Import / Update Commissions
        # -----------------------------
        for _, row in df.iterrows():
            name = str(row["name"]).strip()
            parent_name = None
            if pd.notna(row["parent"]):
                parent_name = str(row["parent"]).strip()
            map_key = (
                parent_name,
                name,
            )
            insurance_type = insurance_map[map_key]
            effective_date = convert_shamsi_to_date(
                row["effective_date"]
            )
            normal_commission = (
                None
                if pd.isna(row["normal_commission"])
                else float(row["normal_commission"])
            )
            mortgage_commission = (
                None
                if pd.isna(row["mortgage_commission"])
                else float(row["mortgage_commission"])
            )
            issuance_percent = (
                None
                if pd.isna(row["issuance_percent"])
                else float(row["issuance_percent"])
            )
            # -----------------------------
            # Parent ها معمولاً کارمزد ندارند
            # -----------------------------
            if (
                normal_commission is None
                and mortgage_commission is None
                and issuance_percent is None
            ):
                continue
            # -----------------------------
            # پیدا کردن کارمزد بر اساس:
            # insurance_type_id + effective_date
            # -----------------------------
            commission = (
                db.query(InsuranceTypeCommission)
                .filter(
                    InsuranceTypeCommission.insurance_type_id
                    == insurance_type.id,
                    InsuranceTypeCommission.effective_date
                    == effective_date,
                )
                .first()
            )
            # اگر همین تاریخ قبلاً وجود داشته:
            # Update
            if commission:
                commission.normal_commission = (
                    normal_commission
                )
                commission.mortgage_commission = (
                    mortgage_commission
                )
                commission.issuance_percent = (
                    issuance_percent
                )
            # اگر تاریخ جدید باشد:
            # Insert
            else:
                commission = InsuranceTypeCommission(
                    insurance_type_id=insurance_type.id,
                    effective_date=effective_date,
                    normal_commission=normal_commission,
                    mortgage_commission=mortgage_commission,
                    issuance_percent=issuance_percent,
                )
                db.add(commission)
        # -----------------------------
        # Import / Update Excel Mappings
        # -----------------------------
        for _, row in df.iterrows():
            excel_names = row["excel_names"]
            if pd.isna(excel_names):
                continue
            name = str(row["name"]).strip()
            parent_name = None
            if pd.notna(row["parent"]):
                parent_name = str(row["parent"]).strip()
            map_key = (
                parent_name,
                name,
            )
            insurance_type = insurance_map[map_key]
            names = str(excel_names).split("|")
            for excel_name in names:
                excel_name = excel_name.strip()
                if not excel_name:
                    continue
                mapping = (
                    db.query(InsuranceTypeMapping)
                    .filter(
                        InsuranceTypeMapping.excel_name
                        == excel_name
                    )
                    .first()
                )
                # اگر Mapping وجود داشت ولی به رشته دیگری
                # متصل بود، آن را اصلاح می‌کنیم.
                if mapping:
                    if (
                        mapping.insurance_type_id
                        != insurance_type.id
                    ):
                        mapping.insurance_type_id = (
                            insurance_type.id
                        )
                    continue
                mapping = InsuranceTypeMapping(
                    excel_name=excel_name,
                    insurance_type=insurance_type,
                )
                db.add(mapping)
        # -----------------------------
        # Commit
        # -----------------------------
        db.commit()
        print(
            f"{len(insurance_map)} insurance types processed"
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()