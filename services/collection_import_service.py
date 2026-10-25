#گزارش 17030
from models import Customer,Collection,Policy
import pandas as pd
from database import SessionLocal
from services.date_service import convert_shamsi_to_date
from sqlalchemy import or_, and_
def extract_customer_code(value):
    if pd.isna(value) or str(value).strip() == "":
        raise ValueError("اطلاعات بیمه گذار خالی است")
    value = str(value).strip()
    if "کد" not in value:
        raise ValueError(
            "فرمت بیمه گذار نامعتبر است: "
            "کلمه «کد» پیدا نشد"
        )
    _, code_part = value.rsplit("کد", 1)
    customer_code = code_part.strip()
    if not customer_code:
        raise ValueError("کد بیمه گذار خالی است")
    return customer_code
def get_customer_by_code(db, customer_code):
    customer = db.query(Customer).filter(
        Customer.customer_code == customer_code
    ).first()
    if not customer:
        raise ValueError(
            f"بیمه گذار با کد {customer_code} پیدا نشد"
        )
    return customer
def parse_phone(value):
    if pd.isna(value):
        return None
    phone = str(value).strip()
    if phone in ("", "_"):
        return None
    phone = phone.rstrip("_")
    if phone.endswith(".0"):
        phone = phone[:-2]
    return phone
def check_phone_change(customer, new_phone):
    if new_phone is None:
        return "empty"
    if customer.phone is None:
        return "new"
    if customer.phone == new_phone:
        return "same"
    return "changed"
def update_customer_phone(customer, new_phone):
    if customer.phone is None and new_phone is not None:
        customer.phone = new_phone
        return True
    return False
def create_phone_change_item(customer, new_phone):
    return {
        "customer_name": customer.name or "",
        "customer_family": customer.family or "",
        "customer_code": customer.customer_code or "",
        "customer_id": customer.id,
        "old_phone": customer.phone,
        "new_phone": new_phone,
    }
def get_existing_collection(
    db,
    operation_code,
    due_computer_code,
    receipt_document_number,
    policy_computer_code,
    settlement_amount
):
    return db.query(Collection).filter(
        Collection.settlement_operation_code == operation_code,
        or_(
            Collection.due_computer_code == due_computer_code,
            and_(
                Collection.due_computer_code.is_(None),
                due_computer_code is None
            )
        ),
        or_(
            Collection.receipt_document_number == receipt_document_number,
            and_(
                Collection.receipt_document_number.is_(None),
                receipt_document_number is None
            )
        ),
        Collection.policy_computer_code == policy_computer_code,
        Collection.settlement_amount == settlement_amount
    ).first()
def parse_shamsi_date(value):
    if pd.isna(value) or str(value).strip() == "":
        return None
    return convert_shamsi_to_date(value)
def import_collections_from_excel(file_path):
    df = pd.read_excel(file_path)
    db = SessionLocal()
    imported_count = 0
    duplicate_count = 0
    error_count = 0
    duplicate_reports = []
    phone_changes = {}
    try:
        for index, row in df.iterrows():
            try:
                operation_type = (
                    None
                    if pd.isna(row["نوع عملیات تسویه"])
                    else str(row["نوع عملیات تسویه"]).strip()
                )
                if operation_type == "حذف بدهي":
                    continue
                settlement_date = parse_shamsi_date(
                    row["تاریخ تسویه"]
                )
                if settlement_date is None:
                    continue
                operation_code = str(
                    row["کد رایانه عملیات تسویه"]
                ).strip()
                if (
                    pd.isna(row["کد رایانه عملیات تسویه"])
                    or operation_code == ""
                ):
                    raise ValueError(
                        "کد رایانه عملیات تسویه خالی است"
                    )
                due_computer_code = None
                if (
                    pd.notna(row["کد رایانه سررسید"])
                    and str(row["کد رایانه سررسید"]).strip() != ""
                ):
                    due_computer_code = str(
                        row["کد رایانه سررسید"]
                    ).strip()
                    if due_computer_code.endswith(".0"):
                        due_computer_code = due_computer_code[:-2]
                policy_computer_code = str(
                    row["کدرایانه بیمه نامه "]
                ).strip()
                if policy_computer_code.endswith(".0"):
                    policy_computer_code = policy_computer_code[:-2]
                if (
                    pd.isna(row["کدرایانه بیمه نامه "])
                    or policy_computer_code == ""
                ):
                    raise ValueError(
                        "کد رایانه بیمه نامه خالی است"
                    )
                existing_collection = None
                receipt_document_number = None
                if (
                    pd.notna(row["شماره سند دریافتی"])
                    and str(row["شماره سند دریافتی"]).strip() != ""
                ):
                    receipt_document_number = str(
                        row["شماره سند دریافتی"]
                    ).strip()
                    if receipt_document_number.endswith(".0"):
                        receipt_document_number = receipt_document_number[:-2]
                settlement_amount = (
                    None
                    if pd.isna(row["مبلغ تسویه شده "])
                    else int(row["مبلغ تسویه شده "])
                )
                existing_collection = get_existing_collection(
                    db,
                    operation_code,
                    due_computer_code,
                    receipt_document_number,
                    policy_computer_code,
                    settlement_amount
                )
                if existing_collection:
                    duplicate_count += 1
                    duplicate_reports.append({
                        "ردیف Excel": index + 2,
                        "کد عملیات تسویه": operation_code,
                        "کد رایانه سررسید": due_computer_code,
                        "کد رایانه بیمه نامه": policy_computer_code,
                        "کد عملیات موجود در DB": (
                            existing_collection.settlement_operation_code
                        ),
                        "کد سررسید موجود در DB": (
                            existing_collection.due_computer_code
                        ),
                        "شماره سند دریافتی": receipt_document_number,
                        "شماره سند دریافتی موجود در DB": (
                            existing_collection.receipt_document_number
                        ),
                        "شناسه رکورد DB": existing_collection.id,
                    })
                    continue
                policy = db.query(Policy).filter(
                    Policy.computer_code == policy_computer_code
                ).first()
                if not policy:
                    raise ValueError(
                        f"بیمه‌نامه با کد رایانه‌ای "
                        f"{policy_computer_code} پیدا نشد"
                    )
                customer = None
                try:
                    customer_code = extract_customer_code(
                        row["بیمه گذار الحاقیه آخر"]
                    )
                    customer = get_customer_by_code(
                        db,
                        customer_code
                    )
                except Exception as e:
                    print(
                        f"بیمه‌گذار پیدا نشد در ردیف {index + 2}: {e}"
                    )
                new_phone = parse_phone(
                    row["شماره موبايل بيمه گذار"]
                )
                if customer:
                    phone_status = check_phone_change(
                        customer,
                        new_phone
                    )
                    if phone_status == "new":
                        update_customer_phone(
                            customer,
                            new_phone
                        )
                    if phone_status == "changed":
                        phone_changes[customer.id] = (
                            create_phone_change_item(
                                customer,
                                new_phone
                            )
                        )
                collection = Collection(
                    policy_id=policy.id if policy else None,
                    settlement_operation_code=operation_code,
                    due_computer_code=due_computer_code,
                    receipt_document_number=receipt_document_number,
                    policy_computer_code=policy_computer_code,
                    settlement_amount=settlement_amount,
                    due_date=parse_shamsi_date(
                        row["تاریخ سررسید"]
                    ),
                    collection_date=parse_shamsi_date(
                        row["تاریخ تسویه"]
                    ),
                    receipt_type=(
                        None
                        if pd.isna(row["نوع دریافتی"])
                        else str(row["نوع دریافتی"]).strip()
                    ),
                    debt_type=(
                        None
                        if pd.isna(row["نوع بدهی"])
                        else str(row["نوع بدهی"]).strip()
                    ),
                )
                db.add(collection)
                db.commit()
                imported_count += 1
            except Exception as e:
                db.rollback()
                error_count += 1
                continue
        if duplicate_reports:
            duplicate_report_df = pd.DataFrame(
                duplicate_reports
            )
            duplicate_report_df.to_excel(
                "duplicate_collections_report.xlsx",
                index=False
            )
        phone_changes = list(phone_changes.values())
        return {
            "imported": imported_count,
            "duplicates": duplicate_count,
            "errors": error_count,
            "phone_changes": phone_changes
        }
    finally:
        db.close()