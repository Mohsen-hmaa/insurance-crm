import time
from datetime import date
from decimal import Decimal
from database import SessionLocal
from models import (
    Policy,
    Collection,
    InsuranceType,
)
from services.system_config_service import (
    get_current_agent,
)
from services.commission_service import (
    get_commission_config_by_date,
)
from services.business_rules import (
    VAT_EXEMPT_TYPES,
)
from sqlalchemy.orm import joinedload
def _get_vat_from_config(issue_date):
    config = get_commission_config_by_date(issue_date)
    if config is None:
        raise ValueError(
            f"تنظیمات کارمزد برای تاریخ {issue_date} پیدا نشد."
        )
    vat = Decimal(str(config.vat))
    # اگر VAT به صورت درصد ذخیره شده باشد، مثلاً 10
    if vat > Decimal("1"):
        vat /= Decimal("100")
    return vat
def _is_vat_exempt(policy):
    insurance_type = policy.insurance_type
    if not insurance_type:
        return False
    return insurance_type.display_name in VAT_EXEMPT_TYPES
def _is_third_party_vehicle(policy):
    insurance_type = policy.insurance_type
    if not insurance_type:
        return False
    return insurance_type.display_name == "شخص ثالث خودرو"
def get_net_premium(
    policy,
    vat_cache=None,
):
    """
    محاسبه حق بیمه خالص یک بیمه نامه یا الحاقیه.
    برای شخص ثالث خودرو ابتدا صندوق از حق بیمه کم می‌شود.
    سپس، در صورت مشمول بودن، VAT بر اساس CommissionConfig
    مربوط به تاریخ صدور همان رکورد از مبلغ کسر می‌شود.
    vat_cache در صورت ارسال شدن، باعث می‌شود VAT مربوط به
    یک تاریخ فقط یک بار از تنظیمات خوانده شود.
    """
    premium = policy.premium or 0
    if _is_third_party_vehicle(policy):
        fund = policy.fund or 0
        premium -= fund
    if _is_vat_exempt(policy):
        return premium
    issue_date = policy.issue_date
    if (
        vat_cache is not None
        and issue_date in vat_cache
    ):
        vat = vat_cache[issue_date]
    else:
        vat = _get_vat_from_config(
            issue_date
        )
        if vat_cache is not None:
            vat_cache[issue_date] = vat
    return premium / (1 + vat)
def get_gross_premium(policy):
    """
    محاسبه حق بیمه ناخالص برای گزارش عملکرد.
    VAT از مبلغ کسر نمی‌شود.
    در شخص ثالث خودرو، مبلغ صندوق از حق بیمه کسر می‌شود.
    """
    premium = policy.premium or 0
    if _is_third_party_vehicle(policy):
        fund = policy.fund or 0
        premium -= fund
    return premium
def get_gross_sales(policies):
    return sum(
        get_gross_premium(policy)
        for policy in policies
    )
def get_period_policies(
    db,
    start_date,
    end_date,
    current_agent=None,
    marketer_id=None,
):
    query = (
        db.query(Policy)
        .options(
            joinedload(
                Policy.insurance_type
            ).joinedload(
                InsuranceType.parent
            )
        )
        .filter(
            Policy.issue_date >= start_date,
            Policy.issue_date <= end_date,
        )
    )
    # گزارش اختصاصی یک بازاریاب
    if marketer_id is not None:
        query = query.filter(
            Policy.marketer_id == marketer_id
        )
    else:
        # رفتار عادی گزارش نمایندگی
        if current_agent is None:
            current_agent = get_current_agent()
        if not current_agent:
            return []
        query = query.filter(
            Policy.referrer_work_unit == current_agent
        )
    return query.all()
def get_policy_count(policies):
    return sum(
        1
        for policy in policies
        if policy.endorsement_number == 0
    )
def get_policy_premium(
    policies,
    vat_cache=None,
):
    return sum(
        get_net_premium(
            policy,
            vat_cache,
        )
        for policy in policies
        if policy.endorsement_number == 0
    )
def get_additional_endorsement_premium(
    policies,
    vat_cache=None,
):
    return sum(
        get_net_premium(
            policy,
            vat_cache,
        )
        for policy in policies
        if (
            policy.endorsement_number > 0
            and (policy.premium or 0) > 0
        )
    )
def get_return_endorsement_premium(
    policies,
    vat_cache=None,
):
    return abs(
        sum(
            get_net_premium(
                policy,
                vat_cache,
            )
            for policy in policies
            if (
                policy.endorsement_number > 0
                and (policy.premium or 0) < 0
            )
        )
    )
def get_net_sales(
    policies,
    vat_cache=None,
):
    return sum(
        get_net_premium(
            policy,
            vat_cache,
        )
        for policy in policies
    )
def get_collected_amount(
    db,
    policies,
):
    """
    وصولی تمام بیمه نامه ها و الحاقیه های
    صادرشده در بازه را جمع می‌کند.
    تاریخ وصول در این گزارش ملاک نیست.
    """
    policy_ids = [
        policy.id
        for policy in policies
        if policy.id is not None
    ]
    if not policy_ids:
        return 0
    rows = (
        db.query(Collection.settlement_amount)
        .filter(
            Collection.policy_id.in_(policy_ids)
        )
        .all()
    )
    return sum(
        amount or 0
        for (amount,) in rows
    )
def get_report_insurance_type(policy):
    insurance_type = policy.insurance_type
    if not insurance_type:
        return "نامشخص"
    name = insurance_type.display_name or ""
    # استثنا: مسئولیت حمل و نقل
    if name in {
        "مسئوليت متصدیان حمل و نقل",
        "مسئوليت شرکت های حمل و نقل بین المللی CMR",
    }:
        return "مسئولیت حمل و نقل"
    # استثنا: سازندگان ابنیه
    if name == (
        "مسئوليت سازندگان ابنیه در قبال اشخاص ثالث"
    ):
        return (
            "مسئولیت سازندگان ابنیه در قبال اشخاص ثالث"
        )
    # استثنا: مسئولیت کارفرما
    if name in {
        "مسئوليت کارفرما صنعتی، تولیدی و خدماتی",
        "مسئوليت کارفرما عمرانی",
        "مسئوليت کارفرما ساختمانی",
    }:
        return "مسئولیت کارفرما"
    # استثنا: شخص ثالث اتومبیل
    if name == "شخص ثالث خودرو":
        return "شخص ثالث اتومبیل"
    # قانون اصلی parent
    parent = insurance_type.parent
    if parent:
        return parent.display_name
    return insurance_type.display_name
def get_sales_by_insurance_type(
    policies,
    vat_cache=None,
):
    result = {}
    for policy in policies:
        name = get_report_insurance_type(
            policy
        )
        result[name] = (
            result.get(name, 0)
            + get_net_premium(
                policy,
                vat_cache,
            )
        )
    return result
def calculate_growth(
    current_value,
    previous_value,
):
    if previous_value == 0:
        return (
            0
            if current_value == 0
            else None
        )
    return (
        (
            current_value
            - previous_value
        )
        / abs(previous_value)
    ) * 100
def get_previous_year_period(
    start_date,
    end_date,
):
    try:
        previous_start = start_date.replace(
            year=start_date.year - 1
        )
    except ValueError:
        previous_start = date(
            start_date.year - 1,
            2,
            28,
        )
    try:
        previous_end = end_date.replace(
            year=end_date.year - 1
        )
    except ValueError:
        previous_end = date(
            end_date.year - 1,
            2,
            28,
        )
    return (
        previous_start,
        previous_end,
    )
def get_issue_code_policies(issue_code):
    db = SessionLocal()
    try:
        return (
            db.query(Policy)
            .filter(
                Policy.issue_code == issue_code
            )
            .order_by(
                Policy.endorsement_number.asc()
            )
            .all()
        )
    finally:
        db.close()
def get_agency_performance_report(
    start_date,
    end_date,
    current_agent=None,
    marketer_id=None,
):
    if marketer_id is None and current_agent is None:
        current_agent = get_current_agent()
    """
    گزارش عملکرد نمایندگی در بازه مشخص.
    تمام اطلاعات فقط مربوط به بیمه‌نامه‌ها
    و الحاقیه‌هایی است که referrer_work_unit
    آنها برابر نمایندگی جاری باشد.
    منطق محاسبات مالی تغییر نکرده است.
    فقط VAT در طول اجرای همین گزارش cache می‌شود.
    """
    total_start = time.perf_counter()
    db = SessionLocal()
    try:
        # ==================================================
        # Cache مربوط به VAT
        # ==================================================
        vat_cache = {}
        # ==================================================
        # دوره جاری
        # ==================================================
        start = time.perf_counter()
        current_policies = get_period_policies(
            db,
            start_date,
            end_date,
            current_agent=current_agent,
            marketer_id=marketer_id,
        )
        # ==================================================
        # دوره مشابه سال قبل
        # ==================================================
        start = time.perf_counter()
        previous_start, previous_end = (
            get_previous_year_period(
                start_date,
                end_date,
            )
        )
        previous_policies = get_period_policies(
            db,
            previous_start,
            previous_end,
            current_agent=current_agent,
            marketer_id=marketer_id,
        )
        # ==================================================
        # تعداد بیمه‌نامه‌ها
        # ==================================================
        start = time.perf_counter()
        policy_count = get_policy_count(
            current_policies
        )
        previous_policy_count = get_policy_count(
            previous_policies
        )
        # ==================================================
        # حق بیمه بیمه‌نامه‌های اصلی
        # ==================================================
        start = time.perf_counter()
        policy_premium = get_policy_premium(
            current_policies,
            vat_cache,
        )
        # ==================================================
        # الحاقیه‌های اضافی
        # ==================================================
        start = time.perf_counter()
        additional_endorsement_premium = (
            get_additional_endorsement_premium(
                current_policies,
                vat_cache,
            )
        )
        # ==================================================
        # الحاقیه‌های برگشتی
        # ==================================================
        start = time.perf_counter()
        return_endorsement_premium = (
            get_return_endorsement_premium(
                current_policies,
                vat_cache,
            )
        )
        # ==================================================
        # فروش خالص
        # ==================================================
        start = time.perf_counter()
        net_sales = get_net_sales(
            current_policies,
            vat_cache,
        )
        # ==================================================
        # فروش خالص سال قبل
        # ==================================================
        start = time.perf_counter()
        previous_net_sales = get_net_sales(
            previous_policies,
            vat_cache,
        )
        # ==================================================
        # فروش ناخالص
        # ==================================================
        start = time.perf_counter()
        gross_sales = get_gross_sales(
            current_policies
        )
        # ==================================================
        # وصول
        # ==================================================
        start = time.perf_counter()
        collected_amount = get_collected_amount(
            db,
            current_policies,
        )
        # ==================================================
        # رشد تعدادی
        # ==================================================
        start = time.perf_counter()
        count_growth = calculate_growth(
            policy_count,
            previous_policy_count,
        )
        # ==================================================
        # رشد ریالی
        # ==================================================
        start = time.perf_counter()
        premium_growth = calculate_growth(
            net_sales,
            previous_net_sales,
        )
        # ==================================================
        # فروش به تفکیک رشته
        # ==================================================
        start = time.perf_counter()
        sales_by_insurance_type = (
            get_sales_by_insurance_type(
                current_policies,
                vat_cache,
            )
        )
        # ==================================================
        # اطلاعات Cache برای تشخیص
        # ==================================================
        # ==================================================
        # نتیجه نهایی
        # ==================================================
        return {
            "start_date": start_date,
            "end_date": end_date,
            "policy_count": policy_count,
            "policy_premium": policy_premium,
            "additional_endorsement_premium": (
                additional_endorsement_premium
            ),
            "return_endorsement_premium": (
                return_endorsement_premium
            ),
            "net_sales": net_sales,
            "collected_amount": collected_amount,
            "gross_sales": gross_sales,
            "previous_policy_count": (
                previous_policy_count
            ),
            "previous_net_sales": (
                previous_net_sales
            ),
            # رشد ریالی
            "premium_growth": premium_growth,
            # رشد تعدادی
            "policy_count_growth": count_growth,
            "sales_by_insurance_type": (
                sales_by_insurance_type
            ),
        }
    finally:
        db.close()