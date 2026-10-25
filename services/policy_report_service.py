from openpyxl import Workbook
from openpyxl.styles import (
    Font,
    Alignment,
    PatternFill,
    Border,
    Side
)
from services.date_service import convert_date_to_shamsi
from datetime import date
from database import SessionLocal
from models import Policy
from sqlalchemy.orm import joinedload
def get_expiry_policies(
    policies,
    end_date_from,
    end_date_to
):
    """
    بیمه‌نامه‌های اصلی که تاریخ پایان آنها
    در بازه مشخص شده قرار دارد.
    """
    filtered_policies = [
        policy
        for policy in policies
        if (
            policy.end_date is not None
            and policy.endorsement_number == 0
            and end_date_from <= policy.end_date <= end_date_to
        )
    ]
    filtered_policies.sort(
        key=lambda policy: policy.end_date
    )
    return filtered_policies
def load_expiry_policies(
    end_date_from,
    end_date_to
):
    """
    دریافت مستقیم بیمه‌نامه‌های اصلی
    در حال انقضا از دیتابیس.
    این تابع برای مواقعی است که فقط
    بیمه‌نامه‌های یک بازه مشخص مورد نیاز هستند
    و نباید کل بیمه‌نامه‌ها از دیتابیس خوانده شوند.
    """
    db = SessionLocal()
    try:
        return (
            db.query(Policy)
            .options(
                joinedload(Policy.customer),
                joinedload(Policy.insurance_type),
            )
            .filter(
                Policy.end_date.isnot(None),
                Policy.endorsement_number == 0,
                Policy.end_date >= end_date_from,
                Policy.end_date <= end_date_to,
            )
            .order_by(
                Policy.end_date.asc()
            )
            .all()
        )
    finally:
        db.close()
def generate_expiry_report(
    policies,
    end_date_from,
    end_date_to,
    file_path
):
    """
    گزارش بیمه‌نامه‌هایی که تاریخ پایان آنها
    در بازه مشخص شده قرار دارد.
    """
    # ---------------------------------------------------------
    # Filter
    # ---------------------------------------------------------
    filtered_policies = get_expiry_policies(
        policies,
        end_date_from,
        end_date_to
    )
    # ---------------------------------------------------------
    # Workbook
    # ---------------------------------------------------------
    wb = Workbook()
    ws = wb.active
    ws.title = "بیمه‌نامه‌های در حال انقضا"
    # راست به چپ
    ws.sheet_view.rightToLeft = True
    # ---------------------------------------------------------
    # Colors / Styles
    # ---------------------------------------------------------
    # رنگ اصلی هدر گزارش‌ها
    header_fill = PatternFill(
        fill_type="solid",
        fgColor="D9EAD3"
    )
    title_fill = PatternFill(
        fill_type="solid",
        fgColor="E2F0D9"
    )
    thin_side = Side(
        style="thin",
        color="B7B7B7"
    )
    thin_border = Border(
        left=thin_side,
        right=thin_side,
        top=thin_side,
        bottom=thin_side
    )
    title_font = Font(
        name="Tahoma",
        bold=True,
        size=14
    )
    header_font = Font(
        name="Tahoma",
        bold=True,
        size=11
    )
    normal_font = Font(
        name="Tahoma",
        size=9
    )
    center_alignment = Alignment(
        horizontal="center",
        vertical="center"
    )
    # ---------------------------------------------------------
    # Title
    # ---------------------------------------------------------
    ws.merge_cells("A1:G1")
    title_cell = ws["A1"]
    title_cell.value = "گزارش بیمه‌نامه‌های در حال انقضا"
    title_cell.font = title_font
    title_cell.fill = title_fill
    title_cell.alignment = center_alignment
    for row in ws["A1:G1"]:
        for cell in row:
            cell.border = thin_border
    ws.row_dimensions[1].height = 28
    # ---------------------------------------------------------
    # Date range
    # ---------------------------------------------------------
    ws.merge_cells("A2:G2")
    date_range_cell = ws["A2"]
    date_range_cell.value = (
        f"بازه تاریخ پایان: "
        f"{convert_date_to_shamsi(end_date_from)} "
        f"تا "
        f"{convert_date_to_shamsi(end_date_to)}"
    )
    date_range_cell.font = Font(
        name="Tahoma",
        size=10
    )
    date_range_cell.alignment = center_alignment
    for row in ws["A2:G2"]:
        for cell in row:
            cell.border = thin_border
    ws.row_dimensions[2].height = 22
    # ---------------------------------------------------------
    # Headers
    # ---------------------------------------------------------
    headers = [
        "ردیف",
        "بیمه‌گذار",
        "ش بیمه‌",
        "رشته بیمه",
        "تاریخ پایان",
        "معرف",
        "موبایل",
    ]
    header_row = 4
    for column, header in enumerate(
        headers,
        start=1
    ):
        cell = ws.cell(
            row=header_row,
            column=column,
            value=header
        )
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_alignment
        cell.border = thin_border
    ws.row_dimensions[header_row].height = 24
    # ---------------------------------------------------------
    # Data
    # ---------------------------------------------------------
    for index, policy in enumerate(
        filtered_policies,
        start=1
    ):
        customer_name = ""
        if policy.customer:
            customer_name = (
                f"{policy.customer.name or ''} "
                f"{policy.customer.family or ''}"
                f"{policy.customer.customer_code or ''}"
            ).strip()
        insurance_type = ""
        if policy.insurance_type:
            insurance_type = (
                policy.insurance_type.display_name
                or ""
            ).strip()
        referrer = (
            policy.referrer
            if policy.referrer
            else ""
        )
        mobile = "-"
        if policy.customer:
            mobile = (
                policy.customer.phone
                or "-"
            )
        row = [
            index,
            customer_name,
            policy.policy_number or "",
            insurance_type,
            convert_date_to_shamsi(
                policy.end_date
            ),
            referrer,
            mobile,
        ]
        excel_row = header_row + index
        for column, value in enumerate(
            row,
            start=1
        ):
            cell = ws.cell(
                row=excel_row,
                column=column,
                value=value
            )
            cell.font = normal_font
            cell.border = thin_border
            if column in (2, 4):
                cell.alignment = Alignment(
                    horizontal="right",
                    vertical="center"
                )
            else:
                cell.alignment = center_alignment
        ws.row_dimensions[excel_row].height = 15
    # ---------------------------------------------------------
    # If no result
    # ---------------------------------------------------------
    if not filtered_policies:
        excel_row = header_row + 1
        ws.merge_cells(
            start_row=excel_row,
            start_column=1,
            end_row=excel_row,
            end_column=7
        )
        cell = ws.cell(
            row=excel_row,
            column=1,
            value="در این بازه بیمه‌نامه‌ای یافت نشد."
        )
        cell.font = normal_font
        cell.alignment = center_alignment
        cell.border = thin_border
    # ---------------------------------------------------------
    # Column widths
    # ---------------------------------------------------------
    widths = {
        "A": 5,
        "B": 35,
        "C": 10,
        "D": 25,
        "E": 10,
        "F": 30,
        "G": 12,
    }
    for column, width in widths.items():
        ws.column_dimensions[column].width = width
    # ---------------------------------------------------------
    # Freeze / Filter
    # ---------------------------------------------------------
    ws.freeze_panes = "A5"
    # ---------------------------------------------------------
    # Save
    # ---------------------------------------------------------
    wb.save(file_path)