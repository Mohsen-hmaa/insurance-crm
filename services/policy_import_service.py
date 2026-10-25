from services.policy_assignment_service import ( 
    get_assignment_candidates_for_new_policies 
) 
import pandas as pd 
from database import SessionLocal 
from models import ( 
    Customer, 
    InsuranceTypeMapping, 
    Marketer, 
    Policy, 
    InsuranceType
) 
from services.date_service import convert_shamsi_to_date 
from services.system_config_service import get_current_agent
from services.text_service import normalize_persian_text
from services.business_rules import VAT_EXEMPT_TYPES,get_commission_config_by_date
class MarketerNotFoundError(Exception): 
    pass 
def parse_customer(value, ao_value): 
    if not value: 
        raise ValueError("اطلاعات بیمه گذار خالی است") 
    value = str(value).strip() 
    if pd.isna(ao_value) or str(ao_value).strip() == "": 
        customer_type = "حقوقی" 
    else: 
        customer_type = "حقیقی" 
    if "کد" not in value: 
        raise ValueError( 
            "فرمت بیمه گذار نامعتبر است: " 
            "کلمه «کد» پیدا نشد" 
        ) 
    customer_part, code_part = value.rsplit("کد", 1) 
    customer_part = customer_part.strip() 
    customer_code = code_part.strip() 
    if not customer_part: 
        raise ValueError("نام بیمه گذار خالی است") 
    if not customer_code: 
        raise ValueError("کد بیمه گذار خالی است") 
    if customer_type == "حقوقی": 
        return { 
            "name": customer_part, 
            "family": None, 
            "customer_code": customer_code, 
            "customer_type": customer_type 
        } 
    parts = customer_part.split(maxsplit=1) 
    if len(parts) < 2: 
        raise ValueError( 
            "برای بیمه گذار حقیقی " 
            "نام و نام خانوادگی مشخص نیست" 
        ) 
    return { 
        "name": parts[0], 
        "family": parts[1], 
        "customer_code": customer_code, 
        "customer_type": customer_type 
    } 
def get_or_create_customer(db, customer_data): 
    customer = db.query(Customer).filter( 
        Customer.customer_code == customer_data["customer_code"] 
    ).first() 
    if customer: 
        return customer 
    customer = Customer( 
        name=customer_data["name"], 
        family=customer_data["family"], 
        customer_type=customer_data["customer_type"], 
        customer_code=customer_data["customer_code"], 
        phone=None, 
        national_id=None 
    ) 
    db.add(customer) 
    db.flush() 
    return customer 
def get_insurance_type(db, excel_name): 
    if pd.isna(excel_name): 
        raise ValueError("رشته بیمه خالی است") 
    excel_name = normalize_persian_text(excel_name) 
    mappings = db.query(InsuranceTypeMapping).all() 
    for mapping in mappings: 
        mapping_name = normalize_persian_text( 
            mapping.excel_name 
        ) 
        if mapping_name == excel_name: 
            return mapping.insurance_type 
    raise ValueError( 
        f"رشته بیمه در Mapping پیدا نشد: {excel_name}" 
    ) 
def get_marketer(db, marketer_name): 
    if pd.isna(marketer_name) or str(marketer_name).strip() == "": 
        return None 
    marketer_name = normalize_persian_text(marketer_name) 
    marketers = db.query(Marketer).all() 
    for marketer in marketers: 
        marketer_db_name = normalize_persian_text( 
            marketer.name 
        ) 
        if marketer_db_name == marketer_name: 
            return marketer 
    raise MarketerNotFoundError( 
        f"بازاریاب پیدا نشد: {marketer_name}" 
    ) 
def parse_premium(premium_value, endorsement_type): 
    if pd.isna(premium_value): 
        raise ValueError("حق بیمه خالی است") 
    premium = int(premium_value) 
    if ( 
        pd.notna(endorsement_type) 
        and endorsement_type == "برگشتي" 
    ): 
        premium = -premium 
    return premium 
def parse_fund(fund_value): 
    if pd.isna(fund_value): 
        return 0 
    return int(fund_value) 
def parse_mortgage_premium(mortgage_value):
    if pd.isna(mortgage_value):
        return 0
    return int(mortgage_value)
def parse_shamsi_date(value): 
    if pd.isna(value) or str(value).strip() == "": 
        return None 
    return convert_shamsi_to_date(value) 
def add_vat_to_mortgage_premium(
    mortgage_premium,
    insurance_type,
    issue_date
):
    if not mortgage_premium:
        return 0
    if (
        insurance_type
        and insurance_type.display_name in VAT_EXEMPT_TYPES
    ):
        return mortgage_premium
    vat_config = get_commission_config_by_date(
        issue_date
    )
    if not vat_config:
        raise ValueError(
            f"تنظیمات VAT برای تاریخ "
            f"{issue_date} پیدا نشد."
        )
    vat = vat_config.vat
    vat_factor = 1 + vat
    return round(
        mortgage_premium * vat_factor
    )
def save_import_error( 
    row_number, 
    error, 
    policy_number=None 
): 
    with open( 
        "import_errors.txt", 
        "a", 
        encoding="utf-8" 
    ) as file: 
        file.write( 
            f"ردیف {row_number} | " 
            f"بیمه‌نامه {policy_number or '-'} | " 
            f"{error}\n" 
        ) 
def create_policy( 
    db, 
    row, 
    customer, 
    marketer, 
    insurance_type, 
    policy_number, 
    computer_code, 
    issue_code,
    endorsement_number, 
    endorsement_type, 
    referrer, 
    issue_date, 
    premium, 
    issuer, 
    referrer_work_unit, 
    fund, 
    is_mortgage,
    mortgage_premium, 
    start_date, 
    end_date 
): 
    referrer_type = "none" 
    if referrer: 
        referrer_type = "introducer" 
    elif marketer: 
        referrer_type = "marketer" 
    policy = Policy( 
        policy_number=policy_number, 
        endorsement_number=endorsement_number, 
        customer_id=customer.id, 
        insurance_type_id=insurance_type.id, 
        issue_date=issue_date, 
        start_date=start_date, 
        end_date=end_date, 
        premium=premium, 
        fund=fund, 
        referrer=referrer, 
        marketer_id=( 
            marketer.id 
            if marketer 
            else None 
        ), 
        referrer_type=referrer_type, 
        is_mortgage=is_mortgage,
        mortgage_premium=mortgage_premium, 
        issuer=issuer, 
        referrer_work_unit=referrer_work_unit, 
        computer_code=computer_code,
        issue_code=issue_code
    ) 
    db.add(policy) 
    return policy 
def prepare_policy_data( 
    db, 
    row, 
    customer, 
    policy_number, 
    computer_code 
): 
    endorsement_number = int( 
        row["شماره الحاقيه"] 
    ) 
    issue_code = str(
        row["کد رايانه صدور"]
    ).strip()
    if issue_code.endswith(".0"):
        issue_code = issue_code[:-2]
    endorsement_type = ( 
        None 
        if pd.isna(row["نوع الحاقيه"]) 
        else ( 
            row["نوع الحاقيه"] 
        ) 
    ) 
    if ( 
        pd.notna(row["مورد بيمه"]) 
        and str(row["مورد بيمه"]).strip() 
    ): 
        insurance_name = ( 
            str(row["مورد بيمه"]).strip() 
        ) 
        if insurance_name == "عادي": 
            insurance_name = str( 
                row["رشته"] 
            ).strip() 
    else: 
        insurance_name = ( 
            str(row["رشته"]).strip() 
        ) 
    insurance_type = get_insurance_type( 
        db, 
        insurance_name 
    ) 
    issue_date = parse_shamsi_date( 
        row["تاريخ"] 
    ) 
    referrer = ( 
        None 
        if pd.isna(row["معرف"]) 
        else str(row["معرف"]).strip() 
    ) 
    if referrer == get_current_agent() or referrer=="شعبه آپادانا کد 110002" or referrer=="مرکز کد 110001": 
        referrer = None 
    premium = parse_premium( 
        row["کل حق بيمه"], 
        endorsement_type 
    ) 
    issuer = ( 
        None 
        if pd.isna(row["صادر کننده"]) 
        else str(row["صادر کننده"]).strip() 
    ) 
    referrer_work_unit = ( 
        None 
        if pd.isna(row["واحد کاري معرف"]) 
        else str( 
            row["واحد کاري معرف"] 
        ).strip() 
    ) 
    if "صندوق" in row.index:
        fund_value = row["صندوق"]
    elif "مبلغ 4" in row.index:
        fund_value = row["مبلغ 4"]
    else:
        fund_value = None
    fund = parse_fund(fund_value)
    mortgage_premium = parse_mortgage_premium(
        row["حق بيمه مرهوناتي"]
    )
    mortgage_premium = add_vat_to_mortgage_premium(
        mortgage_premium=mortgage_premium,
        insurance_type=insurance_type,
        issue_date=issue_date
    )
    is_mortgage = mortgage_premium > 0
    start_date = parse_shamsi_date( 
        row["تاريخ شروع بيمه نامه"] 
    ) 
    end_date = parse_shamsi_date( 
        row["تاريخ پايان بيمه نامه"] 
    ) 
    return { 
        "customer": customer, 
        "policy_number": policy_number, 
        "computer_code": computer_code, 
        "issue_code": issue_code,
        "endorsement_number": endorsement_number, 
        "endorsement_type": endorsement_type, 
        "insurance_type": insurance_type, 
        "referrer": referrer, 
        "issue_date": issue_date, 
        "premium": premium, 
        "issuer": issuer, 
        "referrer_work_unit": referrer_work_unit, 
        "fund": fund, 
        "is_mortgage": is_mortgage, 
        "mortgage_premium": mortgage_premium,
        "start_date": start_date, 
        "end_date": end_date 
    } 
def process_pending_marketer_policies(
    db,
    policies,
    marketer=None
):
    created_policies = []
    for item in policies:
        policy_data = item["policy_data"]
        customer = db.query(Customer).filter(
            Customer.id == item["customer_id"]
        ).first()
        if not customer:
            raise ValueError(
                f"بیمه‌گذار با شناسه {item['customer_id']} پیدا نشد"
            )
        insurance_type = db.query(InsuranceType).filter(
            InsuranceType.id == item["insurance_type_id"]
        ).first()
        if not insurance_type:
            raise ValueError(
                f"نوع بیمه با شناسه {item['insurance_type_id']} پیدا نشد"
            )
        policy = create_policy(
            db=db,
            row=item["row"],
            customer=customer,
            marketer=marketer,
            insurance_type=insurance_type,
            policy_number=policy_data["policy_number"],
            computer_code=policy_data["computer_code"],
            issue_code=policy_data["issue_code"],
            endorsement_number=policy_data["endorsement_number"],
            endorsement_type=policy_data["endorsement_type"],
            referrer=policy_data["referrer"],
            issue_date=policy_data["issue_date"],
            premium=policy_data["premium"],
            issuer=policy_data["issuer"],
            referrer_work_unit=policy_data["referrer_work_unit"],
            fund=policy_data["fund"],
            is_mortgage=policy_data["is_mortgage"],
            mortgage_premium=policy_data["mortgage_premium"],
            start_date=policy_data["start_date"],
            end_date=policy_data["end_date"]
        )
        created_policies.append(policy)
    db.commit()
    for policy in created_policies:
        db.refresh(policy)
    return created_policies
def import_policies_from_excel(file_path): 
    df = pd.read_excel(file_path) 
    db = SessionLocal() 
    imported_count = 0 
    duplicate_count = 0 
    error_count = 0 
    new_policies = [] 
    pending_marketer_policies = [] 
    try: 
        for index, row in df.iterrows(): 
            policy_number = None 
            try: 
                policy_number = str( 
                    row["شماره بيمه نامه"] 
                ).strip() 
                computer_code = str( 
                    row["کد رايانه"] 
                ).strip() 
                if computer_code.endswith(".0"): 
                    computer_code = computer_code[:-2]
                transaction_number = row["شماره تراکنش"]
                endorsement_number = row["شماره الحاقيه"]
                if (
                    pd.notna(transaction_number)
                    and str(transaction_number).strip() not in {"", "0", "0.0"}
                    and int(endorsement_number) == 0
                ):
                    continue
                existing_policy = db.query(Policy).filter( 
                    Policy.computer_code == computer_code 
                ).first() 
                customer_value = ( 
                    None 
                    if pd.isna(row["بيمه گذار"]) 
                    else str(row["بيمه گذار"]).strip() 
                ) 
                ao_value = row["نوع استفاده بيمه نامه"] 
                customer_data = parse_customer( 
                    customer_value, 
                    ao_value 
                ) 
                customer = get_or_create_customer( 
                    db, 
                    customer_data 
                ) 
                policy_data = prepare_policy_data( 
                    db=db, 
                    row=row, 
                    customer=customer, 
                    policy_number=policy_number, 
                    computer_code=computer_code 
                ) 
                if existing_policy: 
                    duplicate_count += 1 
                    updated = False 
                    if ( 
                        existing_policy.referrer is None 
                        and policy_data["referrer"] is not None 
                    ): 
                        existing_policy.referrer = policy_data["referrer"] 
                        updated = True 
                    marketer = None 
                    marketer_name = row["بازارياب"] 
                    try: 
                        marketer = get_marketer( 
                            db, 
                            marketer_name 
                        ) 
                    except MarketerNotFoundError: 
                        marketer = None 
                    if ( 
                        existing_policy.marketer_id is None 
                        and marketer is not None 
                    ): 
                        existing_policy.marketer_id = marketer.id 
                        updated = True 
                    if updated: 
                        db.commit() 
                    continue 
                marketer = None 
                marketer_name = row["بازارياب"] 
                try: 
                    marketer = get_marketer( 
                        db, 
                        marketer_name 
                    ) 
                except MarketerNotFoundError: 
                    pending_marketer_policies.append({ 
                        "row": row, 
                        "row_number": index + 2, 
                        "policy_number": policy_number, 
                        "computer_code": computer_code, 
                        "customer_id": customer.id,
                        "insurance_type_id": policy_data["insurance_type"].id, 
                        "policy_data": policy_data, 
                        "marketer_name": normalize_persian_text( 
                            marketer_name 
                        ) 
                    }) 
                    continue 
                policy = create_policy( 
                    db=db, 
                    row=row, 
                    customer=customer, 
                    marketer=marketer, 
                    insurance_type=policy_data["insurance_type"], 
                    policy_number=policy_data["policy_number"], 
                    computer_code=policy_data["computer_code"], 
                    issue_code=policy_data["issue_code"],
                    endorsement_number=policy_data["endorsement_number"], 
                    endorsement_type=policy_data["endorsement_type"], 
                    referrer=policy_data["referrer"], 
                    issue_date=policy_data["issue_date"], 
                    premium=policy_data["premium"], 
                    issuer=policy_data["issuer"], 
                    referrer_work_unit=policy_data["referrer_work_unit"], 
                    fund=policy_data["fund"], 
                    is_mortgage=policy_data["is_mortgage"], 
                    mortgage_premium=policy_data["mortgage_premium"],
                    start_date=policy_data["start_date"], 
                    end_date=policy_data["end_date"] 
                ) 
                db.commit() 
                db.refresh(policy)
                imported_count += 1 
                new_policies.append(policy) 
            except Exception as e: 
                db.rollback() 
                error_count += 1 
                save_import_error( 
                    row_number=index + 2, 
                    error=str(e), 
                    policy_number=policy_number 
                ) 
                continue 
        assignment_candidates = get_assignment_candidates_for_new_policies( 
            new_policies 
        ) 
        return { 
            "imported": imported_count, 
            "duplicates": duplicate_count, 
            "errors": error_count, 
            "new_policies": new_policies, 
            "assignment_candidates": assignment_candidates, 
            "pending_marketer_policies": pending_marketer_policies 
        } 
    finally: 
        db.close() 
def group_pending_marketer_policies( 
    pending_marketer_policies 
): 
    grouped = {} 
    for item in pending_marketer_policies: 
        marketer_name = item["marketer_name"] 
        if pd.isna(marketer_name): 
            continue 
        marketer_name = normalize_persian_text( 
            marketer_name 
        ) 
        if marketer_name not in grouped: 
            grouped[marketer_name] = [] 
        grouped[marketer_name].append(item) 
    return grouped 
