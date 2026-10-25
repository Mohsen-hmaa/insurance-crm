import pandas as pd
from database import SessionLocal
from models import Policy
from services.business_rules import (
    VAT_EXEMPT_TYPES,
    get_commission_config_by_date,
)
def parse_mortgage_premium(value):
    if pd.isna(value):
        return 0
    return int(value)
def add_vat_to_mortgage_premium(
    mortgage_premium,
    policy,
):
    if not mortgage_premium:
        return 0
    insurance_type = policy.insurance_type
    if (
        insurance_type
        and insurance_type.display_name in VAT_EXEMPT_TYPES
    ):
        return mortgage_premium
    vat_config = get_commission_config_by_date(
        policy.issue_date
    )
    if not vat_config:
        raise ValueError(
            f"تنظیمات VAT برای تاریخ "
            f"{policy.issue_date} پیدا نشد."
        )
    vat = vat_config.vat
    vat_factor = 1 + vat
    return round(
        mortgage_premium * vat_factor
    )
def import_mortgage_premiums_from_excel(file_path):
    df = pd.read_excel(file_path)
    db = SessionLocal()
    updated_count = 0
    zero_count = 0
    not_found_count = 0
    error_count = 0
    try:
        for index, row in df.iterrows():
            computer_code = None
            try:
                computer_code = str(
                    row["کد رايانه"]
                ).strip()
                if computer_code.endswith(".0"):
                    computer_code = computer_code[:-2]
                policy = (
                    db.query(Policy)
                    .filter(
                        Policy.computer_code
                        == computer_code
                    )
                    .first()
                )
                if not policy:
                    not_found_count += 1
                    print(
                        f"بیمه‌نامه پیدا نشد: "
                        f"{computer_code}"
                    )
                    continue
                mortgage_premium = (
                    parse_mortgage_premium(
                        row["حق بيمه مرهوناتي"]
                    )
                )
                mortgage_premium = (
                    add_vat_to_mortgage_premium(
                        mortgage_premium,
                        policy,
                    )
                )
                policy.mortgage_premium = (
                    mortgage_premium
                )
                updated_count += 1
                if mortgage_premium == 0:
                    zero_count += 1
                db.commit()
            except Exception as e:
                db.rollback()
                error_count += 1
                print(
                    f"خطا در ردیف "
                    f"{index + 2}: {e}"
                )
        print()
        print("نتیجه انتقال حق بیمه مرهوناتی")
        print("------------------------------")
        print(
            f"به‌روزرسانی شده: {updated_count}"
        )
        print(
            f"مقدار صفر: {zero_count}"
        )
        print(
            f"بیمه‌نامه پیدا نشد: {not_found_count}"
        )
        print(
            f"خطا: {error_count}"
        )
    finally:
        db.close()
if __name__ == "__main__":
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="انتخاب فایل اکسل بیمه‌نامه‌ها",
        filetypes=[
            ("Excel files", "*.xlsx *.xls"),
            ("All files", "*.*"),
        ],
    )
    root.destroy()
    if not file_path:
        print("هیچ فایلی انتخاب نشد.")
    else:
        import_mortgage_premiums_from_excel(
            file_path
        )