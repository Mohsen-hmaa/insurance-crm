from database import SessionLocal
from models import (
    Policy,
    CommissionConfig,
    InsuranceTypeCommission,
    Collection
)
from sqlalchemy.orm import joinedload
from services.marketer_service import find_best_commission_rule
from services.system_config_service import get_current_agent
from decimal import Decimal
from services.business_rules import get_commission_config_by_date,VAT_EXEMPT_TYPES 
def get_insurance_type_commission_by_date(
    insurance_type_id,
    issue_date
):
    db = SessionLocal()
    try:
        return (
            db.query(InsuranceTypeCommission)
            .filter(
                InsuranceTypeCommission.insurance_type_id == insurance_type_id,
                InsuranceTypeCommission.effective_date <= issue_date
            )
            .order_by(
                InsuranceTypeCommission.effective_date.desc()
            )
            .first()
        )
    finally:
        db.close()
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
def get_original_policy(policy):
    policies = get_issue_code_policies(
        policy.issue_code
    )
    if not policies:
        return None
    return policies[0]
def calculate_base_commission(
    net_premium,
    commission_percent,
    first_step_commission
):
    net_premium = Decimal(str(net_premium or 0))
    commission_percent = Decimal(str(commission_percent or 0))
    first_step_commission = Decimal(
        str(first_step_commission or 0)
    )
    sec_step_commission = (
        first_step_commission * Decimal("2")
    )
    th_step_commission = (
        first_step_commission * Decimal("4")
    )
    if net_premium <= first_step_commission:
        commission = (
            net_premium
            * commission_percent
            / Decimal("100")
        )
    elif net_premium <= sec_step_commission:
        commission = (
            first_step_commission
            * commission_percent
            / Decimal("100")
            + (
                net_premium - first_step_commission
            )
            * Decimal("0.5")
            * commission_percent
            / Decimal("100")
        )
    elif net_premium <= th_step_commission:
        commission = (
            first_step_commission
            * commission_percent
            / Decimal("100")
            + (
                sec_step_commission - first_step_commission
            )
            * Decimal("0.5")
            * commission_percent
            / Decimal("100")
            + (
                net_premium - sec_step_commission
            )
            * Decimal("0.25")
            * commission_percent
            / Decimal("100")
        )
    else:
        commission = (
            first_step_commission
            * commission_percent
            / Decimal("100")
            + (
                sec_step_commission - first_step_commission
            )
            * Decimal("0.5")
            * commission_percent
            / Decimal("100")
            + (
                th_step_commission - sec_step_commission
            )
            * Decimal("0.25")
            * commission_percent
            / Decimal("100")
            + (
                net_premium - th_step_commission
            )
            * Decimal("0.1")
            * commission_percent
            / Decimal("100")
        )
    return commission
def calculate_base_issuance(
    net_premium,
    issuance_percent,
    first_step_commission
):
    net_premium = Decimal(str(net_premium or 0))
    issuance_percent = Decimal(str(issuance_percent or 0))
    first_step_commission = Decimal(
        str(first_step_commission or 0)
    )
    first_step_issuance = (
        first_step_commission / Decimal("5")
    )
    sec_step_issuance = (
        first_step_issuance * Decimal("5")
    )
    th_step_issuance = (
        sec_step_issuance * Decimal("2")
    )
    if net_premium <= first_step_issuance:
        issuance = (
            net_premium
            * issuance_percent
            / Decimal("100")
        )
    elif net_premium <= sec_step_issuance:
        issuance = (
            first_step_issuance
            * issuance_percent
            / Decimal("100")
            + (
                net_premium - first_step_issuance
            )
            * Decimal("0.25")
            * issuance_percent
            / Decimal("100")
        )
    elif net_premium <= th_step_issuance:
        issuance = (
            first_step_issuance
            * issuance_percent
            / Decimal("100")
            + (
                sec_step_issuance - first_step_issuance
            )
            * Decimal("0.25")
            * issuance_percent
            / Decimal("100")
            + (
                net_premium - sec_step_issuance
            )
            * Decimal("0.1")
            * issuance_percent
            / Decimal("100")
        )
    else:
        issuance = (
            first_step_issuance
            * issuance_percent
            / Decimal("100")
            + (
                sec_step_issuance - first_step_issuance
            )
            * Decimal("0.25")
            * issuance_percent
            / Decimal("100")
            + (
                th_step_issuance - sec_step_issuance
            )
            * Decimal("0.1")
            * issuance_percent
            / Decimal("100")
            + (
                net_premium - th_step_issuance
            )
            * Decimal("0.05")
            * issuance_percent
            / Decimal("100")
        )
    return issuance
def calculate_cumulative_commission(
    issue_code,
    endorsement_number
):
    policies = get_issue_code_policies(
        issue_code
    )
    if not policies:
        return 0, 0
    original_policy = policies[0]
    # نسبت صندوق بیمه اصلی برای شخص ثالث
    fund_ratio = 0
    if (
        original_policy.insurance_type
        and original_policy.insurance_type.display_name
        =="شخص ثالث خودرو"
    ):
        original_premium = (
            original_policy.premium or 0
        )
        original_fund = (
            original_policy.fund or 0
        )
        if (
            original_premium > 0
            and original_fund > 0
        ):
            fund_ratio = (
                original_fund
                / original_premium
            )
    original_config = (
        get_commission_config_by_date(
            original_policy.issue_date
        )
    )
    if not original_config:
        return 0, 0
    first_step_commission = (
        original_config.first_step_commission
    )
    # نرخ کارمزد رشته فقط از بیمه‌نامه اصلی
    original_type_commission = (
        get_insurance_type_commission_by_date(
            original_policy.insurance_type_id,
            original_policy.issue_date
        )
    )
    if not original_type_commission:
        return 0, 0
    normal_commission_percent = (
        original_type_commission.normal_commission
        or 0
    )
    mortgage_commission_percent = (
        original_type_commission.mortgage_commission
        or 0
    )
    cumulative_premium = 0
    cumulative_normal_premium = 0
    cumulative_mortgage_premium = 0
    commission_difference = 0
    gross_commission_difference = 0
    for policy in policies:
        if (
            policy.endorsement_number
            > endorsement_number
        ):
            break
        premium = policy.premium or 0
        mortgage_premium = (
            policy.mortgage_premium or 0
        )
        # -------------------------------------------------
        # VAT مربوط به تاریخ همان بیمه‌نامه/الحاقیه
        # -------------------------------------------------
        vat_config = get_commission_config_by_date(
            policy.issue_date
        )
        if not vat_config:
            return 0, 0
        vat = vat_config.vat
        vat_factor = 1 + vat
        # -------------------------------------------------
        # تفکیک بخش عادی و مرهوناتی
        # -------------------------------------------------
        normal_premium = (
            premium - mortgage_premium
        )
        # -------------------------------------------------
        # کسر سهم صندوق
        # -------------------------------------------------
        normal_commissionable_premium = (
            normal_premium
            * (1 - fund_ratio)
        )
        mortgage_commissionable_premium = (
            mortgage_premium
        )
        # -------------------------------------------------
        # تبدیل به مبلغ خالص
        # همان منطق قبلی VAT
        # -------------------------------------------------
        if (
            policy.insurance_type.display_name
            not in VAT_EXEMPT_TYPES
        ):
            net_premium = (
                premium
                * (1 - fund_ratio)
                / vat_factor
            )
            net_normal_premium = (
                normal_commissionable_premium
                / vat_factor
            )
            net_mortgage_premium = (
                mortgage_commissionable_premium
                / vat_factor
            )
            gross_factor = vat_factor
        else:
            net_premium = (
                premium
                * (1 - fund_ratio)
            )
            net_normal_premium = (
                normal_commissionable_premium
            )
            net_mortgage_premium = (
                mortgage_commissionable_premium
            )
            gross_factor = 1
        # -------------------------------------------------
        # مهم:
        # پله فقط بر اساس premium است
        # -------------------------------------------------
        previous_cumulative_premium = (
            cumulative_premium
        )
        cumulative_premium += net_premium
        # این دو فقط برای محاسبه کارمزد هستند
        cumulative_normal_premium += (
            net_normal_premium
        )
        cumulative_mortgage_premium += (
            net_mortgage_premium
        )
        # -------------------------------------------------
        # کارمزد تجمعی بر اساس همان منطق پلکانی قبلی
        #
        # خود calculate_base_commission تعیین می‌کند
        # cumulative_premium در چه پله‌ای قرار دارد.
        # -------------------------------------------------
        def calculate_split_commission(
            total_premium,
            normal_premium,
            mortgage_premium
        ):
            if total_premium == 0:
                return (
                    normal_premium
                    * normal_commission_percent
                    / 100
                    +
                    mortgage_premium
                    * mortgage_commission_percent
                    / 100
                )
            base_commission = (
                calculate_base_commission(
                    total_premium,
                    100,
                    first_step_commission
                )
            )
            commission_factor = (
                base_commission
                / total_premium
            )
            return (
                (
                    normal_premium
                    * normal_commission_percent
                    / 100
                )
                +
                (
                    mortgage_premium
                    * mortgage_commission_percent
                    / 100
                )
            ) * commission_factor
        previous_commission = (
            calculate_split_commission(
                previous_cumulative_premium,
                cumulative_normal_premium
                - net_normal_premium,
                cumulative_mortgage_premium
                - net_mortgage_premium
            )
        )
        current_commission = (
            calculate_split_commission(
                cumulative_premium,
                cumulative_normal_premium,
                cumulative_mortgage_premium
            )
        )
        commission_difference = (
            current_commission
            - previous_commission
        )
        gross_commission_difference = (
            commission_difference
            * gross_factor
        )
    return (
        round(commission_difference),
        round(gross_commission_difference)
    )
def calculate_cumulative_issuance(
    issue_code,
    endorsement_number
):
    policies = get_issue_code_policies(
        issue_code
    )
    if not policies:
        return 0, 0
    original_policy = policies[0]
    # ==================================================
    # نسبت صندوق بیمه اصلی برای شخص ثالث
    # ==================================================
    fund_ratio = 0
    if (
        original_policy.insurance_type
        and original_policy.insurance_type.display_name == "شخص ثالث خودرو"
    ):
        original_premium = original_policy.premium or 0
        original_fund = original_policy.fund or 0
        if original_premium > 0 and original_fund > 0:
            fund_ratio = original_fund / original_premium
    original_config = get_commission_config_by_date(
        original_policy.issue_date
    )
    if not original_config:
        return 0, 0
    first_step_commission = (
        original_config.first_step_commission
    )
    # درصد صدور فقط از بیمه‌نامه اصلی
    original_type_commission = (
        get_insurance_type_commission_by_date(
            original_policy.insurance_type_id,
            original_policy.issue_date
        )
    )
    if not original_type_commission:
        return 0, 0
    issuance_percent = (
        original_type_commission.issuance_percent
        or 0
    )
    cumulative_premium = 0
    issuance_difference = 0
    gross_issuance_difference = 0
    for policy in policies:
        if policy.endorsement_number > endorsement_number:
            break
        premium = policy.premium or 0
        if premium == 0:
            continue
        # VAT مربوط به تاریخ صدور همان بیمه‌نامه/الحاقیه است
        vat_config = get_commission_config_by_date(
            policy.issue_date
        )
        if not vat_config:
            return 0, 0
        vat = vat_config.vat
        vat_factor = 1 + vat
        # --------------------------------------
        # کسر سهم صندوق از حق بیمه شخص ثالث
        # --------------------------------------
        commissionable_premium = (
            premium * (1 - fund_ratio)
        )
        if (
            policy.insurance_type.display_name
            not in VAT_EXEMPT_TYPES
        ):
            net_premium = (
                commissionable_premium / vat_factor
            )
            gross_factor = vat_factor
        else:
            net_premium = commissionable_premium
            gross_factor = 1
        previous_premium = cumulative_premium
        cumulative_premium += net_premium
        previous_issuance = calculate_base_issuance(
            previous_premium,
            issuance_percent,
            first_step_commission
        )
        current_issuance = calculate_base_issuance(
            cumulative_premium,
            issuance_percent,
            first_step_commission
        )
        issuance_difference = (
            current_issuance
            - previous_issuance
        )
        gross_issuance_difference = (
            issuance_difference
            * gross_factor
        )
    return (
        round(issuance_difference),
        round(gross_issuance_difference)
    )
def calculate_commission(policy):
    current_agent = get_current_agent()
    if not current_agent:
        return 0, 0
    if policy.referrer_work_unit != current_agent:
        return 0, 0
    premium = Decimal(
        str(policy.premium or 0)
    )
    mortgage_premium = Decimal(
        str(policy.mortgage_premium or 0)
    )
    normal_premium = (
        premium - mortgage_premium
    )
    commission_config = get_commission_config_by_date(
        policy.issue_date
    )
    if not commission_config:
        return 0, 0
    first_step_commission = Decimal(
        str(
            commission_config.first_step_commission
            or 0
        )
    )
    vat = Decimal(
        str(commission_config.vat or 0)
    )
    vat_factor = (
        Decimal("1") + vat
    )
    # --------------------------------------
    # کسر سهم صندوق برای شخص ثالث
    # --------------------------------------
    fund_ratio = Decimal("0")
    if (
        policy.insurance_type
        and policy.insurance_type.display_name
        == "شخص ثالث خودرو"
    ):
        original_policy = get_original_policy(
            policy
        )
        original_premium = Decimal(
            str(
                original_policy.premium
                or 0
            )
        )
        original_fund = Decimal(
            str(
                original_policy.fund
                or 0
            )
        )
        if (
            original_premium > 0
            and original_fund > 0
        ):
            fund_ratio = (
                original_fund
                / original_premium
            )
    # --------------------------------------
    # تقسیم بخش عادی و مرهوناتی
    # --------------------------------------
    normal_commissionable = (
        normal_premium
        * (Decimal("1") - fund_ratio)
    )
    mortgage_commissionable = (
        mortgage_premium
    )
    # --------------------------------------
    # VAT
    # --------------------------------------
    if (
        policy.insurance_type.display_name
        not in VAT_EXEMPT_TYPES
    ):
        net_normal_premium = (
            normal_commissionable
            / vat_factor
        )
        net_mortgage_premium = (
            mortgage_commissionable
            / vat_factor
        )
        gross_factor = vat_factor
    else:
        net_normal_premium = (
            normal_commissionable
        )
        net_mortgage_premium = (
            mortgage_commissionable
        )
        gross_factor = Decimal("1")
    # --------------------------------------
    # نرخ‌های کارمزد
    # --------------------------------------
    insurance_type_commission = (
        get_insurance_type_commission_by_date(
            policy.insurance_type_id,
            policy.issue_date
        )
    )
    if not insurance_type_commission:
        return 0, 0
    normal_commission_percent = Decimal(
        str(
            insurance_type_commission.normal_commission
            or 0
        )
    )
    mortgage_commission_percent = Decimal(
        str(
            insurance_type_commission.mortgage_commission
            or 0
        )
    )
    # --------------------------------------
    # محاسبه کارمزد
    #
    # پله فقط بر اساس کل premium تعیین می‌شود.
    # بخش عادی و مرهوناتی فقط نرخ متفاوت دارند.
    # --------------------------------------
    total_net_premium = (
        net_normal_premium
        + net_mortgage_premium
    )
    if total_net_premium == 0:
        # این حالت می‌تواند مثلاً زمانی رخ دهد که:
        #
        # premium = 0
        # mortgage_premium > 0
        #
        # در این حالت normal_premium منفی و
        # mortgage_premium مثبت است و مجموع آنها صفر می‌شود.
        #
        # چون مبلغ کل برای تعیین پله صفر است،
        # ضریب کاهش پلکان اعمال نمی‌شود.
        commission = (
            net_normal_premium
            * normal_commission_percent
            / Decimal("100")
            +
            net_mortgage_premium
            * mortgage_commission_percent
            / Decimal("100")
        )
    else:
        base_commission = (
            calculate_base_commission(
                total_net_premium,
                Decimal("100"),
                first_step_commission
            )
        )
        commission_factor = (
            base_commission
            / total_net_premium
        )
        commission = (
            net_normal_premium
            * normal_commission_percent
            / Decimal("100")
            * commission_factor
            +
            net_mortgage_premium
            * mortgage_commission_percent
            / Decimal("100")
            * commission_factor
        )
    # --------------------------------------
    # کارمزد ناخالص
    # --------------------------------------
    gross_commission = (
        commission
        * gross_factor
    )
    return (
        round(commission),
        round(gross_commission)
    )
def calculate_issuance_cost(policy):
    current_agent = get_current_agent()
    if not current_agent:
        return 0, 0
    if policy.issuer != current_agent:
        return 0, 0
    premium = policy.premium or 0
    if premium == 0:
        return 0, 0
    if policy.endorsement_number == 0:
        commission_config = get_commission_config_by_date(
            policy.issue_date
        )
        if not commission_config:
            return 0, 0
        first_step_commission = (
            commission_config.first_step_commission
        )
        vat = commission_config.vat
        vat_factor = 1 + vat
        # --------------------------------------
        # کسر سهم صندوق برای شخص ثالث
        # --------------------------------------
        fund_ratio = 0
        if (
            policy.insurance_type
            and policy.insurance_type.display_name == "شخص ثالث خودرو"
        ):
            original_premium = policy.premium or 0
            original_fund = policy.fund or 0
            if original_premium > 0 and original_fund > 0:
                fund_ratio = (
                    original_fund
                    / original_premium
                )
        commissionable_premium = (
            premium * (1 - fund_ratio)
        )
        if (
            policy.insurance_type.display_name
            not in VAT_EXEMPT_TYPES
        ):
            net_premium = (
                commissionable_premium
                / vat_factor
            )
            gross_factor = vat_factor
        else:
            net_premium = commissionable_premium
            gross_factor = 1
        insurance_type_commission = (
            get_insurance_type_commission_by_date(
                policy.insurance_type_id,
                policy.issue_date
            )
        )
        if not insurance_type_commission:
            return 0, 0
        issuance_percent = (
            insurance_type_commission.issuance_percent
            or 0
        )
        issuance = calculate_base_issuance(
            net_premium,
            issuance_percent,
            first_step_commission
        )
        gross_issuance = (
            issuance
            * gross_factor
        )
    else:
        issuance, gross_issuance = (
            calculate_cumulative_issuance(
                policy.issue_code,
                policy.endorsement_number
            )
        )
    return (
        round(issuance),
        round(gross_issuance)
    )
def calculate_marketer_share(policy):
    commission, _ = calculate_commission(policy)
    return calculate_marketer_share_from_commission(
        policy,
        commission
    )
def calculate_collection_commission_amount(
    collection_amount,
    commission_percent,
    first_step_commission
):
    collection_amount = Decimal(
        str(collection_amount or 0)
    )
    commission_percent = Decimal(
        str(commission_percent or 0)
    )
    first_step_commission = Decimal(
        str(first_step_commission or 0)
    )
    sec_step_commission = (
        first_step_commission * Decimal("2")
    )
    th_step_commission = (
        first_step_commission * Decimal("4")
    )
    if collection_amount <= first_step_commission:
        commission = (
            collection_amount
            * commission_percent
            / Decimal("100")
        )
    elif collection_amount <= sec_step_commission:
        commission = (
            first_step_commission
            * commission_percent
            / Decimal("100")
            + (
                collection_amount
                - first_step_commission
            )
            * Decimal("0.5")
            * commission_percent
            / Decimal("100")
        )
    elif collection_amount <= th_step_commission:
        commission = (
            first_step_commission
            * commission_percent
            / Decimal("100")
            + (
                sec_step_commission
                - first_step_commission
            )
            * Decimal("0.5")
            * commission_percent
            / Decimal("100")
            + (
                collection_amount
                - sec_step_commission
            )
            * Decimal("0.25")
            * commission_percent
            / Decimal("100")
        )
    else:
        commission = (
            first_step_commission
            * commission_percent
            / Decimal("100")
            + (
                sec_step_commission
                - first_step_commission
            )
            * Decimal("0.5")
            * commission_percent
            / Decimal("100")
            + (
                th_step_commission
                - sec_step_commission
            )
            * Decimal("0.25")
            * commission_percent
            / Decimal("100")
            + (
                collection_amount
                - th_step_commission
            )
            * Decimal("0.1")
            * commission_percent
            / Decimal("100")
        )
    return commission
def calculate_split_collection_commission(
    total_amount,
    mortgage_amount,
    normal_commission_percent,
    mortgage_commission_percent,
    first_step_commission
):
    total_amount = Decimal(
        str(total_amount or 0)
    )
    mortgage_amount = Decimal(
        str(mortgage_amount or 0)
    )
    normal_amount = (
        total_amount - mortgage_amount
    )
    normal_commission_percent = Decimal(
        str(normal_commission_percent or 0)
    )
    mortgage_commission_percent = Decimal(
        str(mortgage_commission_percent or 0)
    )
    first_step_commission = Decimal(
        str(first_step_commission or 0)
    )
    if total_amount == 0:
        return (
            normal_amount
            * normal_commission_percent
            / Decimal("100")
            +
            mortgage_amount
            * mortgage_commission_percent
            / Decimal("100")
        )
    base_commission = (
        calculate_collection_commission_amount(
            total_amount,
            Decimal("100"),
            first_step_commission
        )
    )
    commission_factor = (
        base_commission
        / total_amount
    )
    commission = (
        normal_amount
        * normal_commission_percent
        / Decimal("100")
        * commission_factor
        +
        mortgage_amount
        * mortgage_commission_percent
        / Decimal("100")
        * commission_factor
    )
    return commission
def calculate_cumulative_collection_commission(
    issue_code,
    policy_id=None,
    collection_id=None
):
    db = SessionLocal()
    try:
        policies = (
            db.query(Policy)
            .filter(
                Policy.issue_code == issue_code
            )
            .order_by(
                Policy.endorsement_number.asc()
            )
            .all()
        )
        if not policies:
            return 0, 0
        target_collection = None
        target_policy = None
        if collection_id is not None:
            target_collection = next(
                (
                    collection
                    for policy in policies
                    for collection in policy.collections
                    if collection.id == collection_id
                ),
                None
            )
            if not target_collection:
                return 0, 0
            target_policy = target_collection.policy
        elif policy_id is not None:
            target_policy = next(
                (
                    policy
                    for policy in policies
                    if policy.id == policy_id
                ),
                None
            )
            if not target_policy:
                return 0, 0
        else:
            return 0, 0
        config = get_commission_config_by_date(
            target_policy.issue_date
        )
        if not config:
            return 0, 0
        insurance_type_commission = (
            get_insurance_type_commission_by_date(
                target_policy.insurance_type_id,
                target_policy.issue_date
            )
        )
        if not insurance_type_commission:
            return 0, 0
        normal_commission_percent = Decimal(
            str(
                insurance_type_commission.normal_commission
                or 0
            )
        )
        mortgage_commission_percent = Decimal(
            str(
                insurance_type_commission.mortgage_commission
                or 0
            )
        )
        first_step_commission = Decimal(
            str(
                config.first_step_commission
                or 0
            )
        )
        vat = Decimal(
            str(
                config.vat
                if config.vat is not None
                else 0
            )
        )
        vat_factor = Decimal("1") + vat
        events = []
        for policy in policies:
            events.append(
                (
                    policy.issue_date,
                    0,
                    policy.id,
                    "premium",
                    policy
                )
            )
            for collection in policy.collections:
                events.append(
                    (
                        collection.collection_date,
                        1,
                        collection.id,
                        "collection",
                        collection
                    )
                )
            if (
                policy.endorsement_number > 0
                and policy.premium < 0
            ):
                events.append(
                    (
                        policy.issue_date,
                        2,
                        policy.id,
                        "negative",
                        policy
                    )
                )
        events.sort(
            key=lambda event: (
                event[0],
                event[1],
                event[2]
            )
        )
        outstanding_gross = Decimal("0")
        cumulative_collection = Decimal("0")
        cumulative_mortgage_collection = Decimal("0")
        target_collection_ids = set()
        if target_collection is not None:
            target_collection_ids.add(
                target_collection.id
            )
        # =========================================================
        # TARGET NEGATIVE ENDORSEMENT
        # =========================================================
        if (
            target_policy is not None
            and target_policy.premium < 0
        ):
            for event_date, event_order, event_id, event_type, obj in events:
                # -------------------------------------------------
                # Premium
                # -------------------------------------------------
                if event_type == "premium":
                    policy = obj
                    if policy.premium > 0:
                        outstanding_gross += Decimal(
                            str(
                                policy.premium
                                or 0
                            )
                        )
                    continue
                # -------------------------------------------------
                # Collection
                # -------------------------------------------------
                if event_type == "collection":
                    collection = obj
                    policy = collection.policy
                    collection_amount = Decimal(
                        str(
                            collection.settlement_amount
                            or 0
                        )
                    )
                    policy_premium = Decimal(
                        str(
                            policy.premium
                            or 0
                        )
                    )
                    if policy_premium == 0:
                        mortgage_collection = (
                            Decimal("0")
                        )
                    else:
                        mortgage_ratio = (
                            Decimal(
                                str(
                                    policy.mortgage_premium
                                    or 0
                                )
                            )
                            / policy_premium
                        )
                        mortgage_collection = (
                            collection_amount
                            * mortgage_ratio
                        )
                    if (
                        policy.insurance_type
                        and
                        policy.insurance_type.display_name
                        in VAT_EXEMPT_TYPES
                    ):
                        net_collection = (
                            collection_amount
                        )
                        net_mortgage_collection = (
                            mortgage_collection
                        )
                    else:
                        net_collection = (
                            collection_amount
                            / vat_factor
                        )
                        net_mortgage_collection = (
                            mortgage_collection
                            / vat_factor
                        )
                    cumulative_collection += (
                        net_collection
                    )
                    cumulative_mortgage_collection += (
                        net_mortgage_collection
                    )
                    outstanding_gross -= (
                        collection_amount
                    )
                    continue
                # -------------------------------------------------
                # Negative endorsement
                # -------------------------------------------------
                if event_type == "negative":
                    policy = obj
                    returned_amount_gross = abs(
                        Decimal(
                            str(
                                policy.premium
                                or 0
                            )
                        )
                    )
                    unpaid_gross = max(
                        outstanding_gross,
                        Decimal("0")
                    )
                    effective_return_gross = max(
                        returned_amount_gross
                        - unpaid_gross,
                        Decimal("0")
                    )
                    outstanding_gross -= min(
                        returned_amount_gross,
                        max(
                            outstanding_gross,
                            Decimal("0")
                        )
                    )
                    # =================================================
                    # TARGET NEGATIVE ENDORSEMENT
                    # =================================================
                    if policy.id == target_policy.id:
                        policy_premium = Decimal(
                            str(
                                policy.premium
                                or 0
                            )
                        )
                        policy_mortgage_premium = Decimal(
                            str(
                                policy.mortgage_premium
                                or 0
                            )
                        )
                        # mortgage_premium در برگشتی مثبت ذخیره شده،
                        # بنابراین برای محاسبه کارمزد باید علامت
                        # مبلغ مرهوناتی را با premium هماهنگ کنیم.
                        if (
                            policy_premium < 0
                            and
                            policy_mortgage_premium > 0
                        ):
                            mortgage_amount = (
                                -policy_mortgage_premium
                            )
                        else:
                            mortgage_amount = (
                                policy_mortgage_premium
                            )
                        normal_amount = (
                            policy_premium
                            - mortgage_amount
                        )
                        if (
                            policy.insurance_type
                            and
                            policy.insurance_type.display_name
                            in VAT_EXEMPT_TYPES
                        ):
                            net_normal_amount = (
                                normal_amount
                            )
                            net_mortgage_amount = (
                                mortgage_amount
                            )
                            gross_factor = Decimal("1")
                        else:
                            net_normal_amount = (
                                normal_amount
                                / vat_factor
                            )
                            net_mortgage_amount = (
                                mortgage_amount
                                / vat_factor
                            )
                            gross_factor = (
                                vat_factor
                            )
                        event_commission = (
                            net_normal_amount
                            * normal_commission_percent
                            / Decimal("100")
                            +
                            net_mortgage_amount
                            * mortgage_commission_percent
                            / Decimal("100")
                        )
                        event_commission_gross = (
                            event_commission
                            * gross_factor
                        )
                        return (
                            round(event_commission),
                            round(
                                event_commission_gross
                            )
                        )
                    # =================================================
                    # NON-TARGET NEGATIVE ENDORSEMENT
                    # =================================================
                    if effective_return_gross > 0:
                        policy_premium = Decimal(
                            str(
                                policy.premium
                                or 0
                            )
                        )
                        if policy_premium != 0:
                            mortgage_ratio = (
                                Decimal(
                                    str(
                                        policy.mortgage_premium
                                        or 0
                                    )
                                )
                                / policy_premium
                            )
                            mortgage_return_gross = (
                                effective_return_gross
                                * mortgage_ratio
                            )
                            if (
                                policy.insurance_type
                                and
                                policy.insurance_type.display_name
                                in VAT_EXEMPT_TYPES
                            ):
                                net_return = (
                                    effective_return_gross
                                )
                                net_mortgage_return = (
                                    mortgage_return_gross
                                )
                            else:
                                net_return = (
                                    effective_return_gross
                                    / vat_factor
                                )
                                net_mortgage_return = (
                                    mortgage_return_gross
                                    / vat_factor
                                )
                            cumulative_collection -= (
                                net_return
                            )
                            cumulative_mortgage_collection -= (
                                net_mortgage_return
                            )
                    continue
        # =========================================================
        # TARGET COLLECTION
        # =========================================================
        if target_collection is not None:
            for event_date, event_order, event_id, event_type, obj in events:
                # -------------------------------------------------
                # Premium
                # -------------------------------------------------
                if event_type == "premium":
                    policy = obj
                    if policy.premium > 0:
                        outstanding_gross += Decimal(
                            str(
                                policy.premium
                                or 0
                            )
                        )
                    elif (
                        policy.premium == 0
                        and
                        policy.id == target_policy.id
                    ):
                        mortgage_amount = Decimal(
                            str(
                                policy.mortgage_premium
                                or 0
                            )
                        )
                        normal_amount = (
                            -mortgage_amount
                        )
                        if (
                            policy.insurance_type
                            and
                            policy.insurance_type.display_name
                            in VAT_EXEMPT_TYPES
                        ):
                            net_normal_amount = (
                                normal_amount
                            )
                            net_mortgage_amount = (
                                mortgage_amount
                            )
                            gross_factor = Decimal("1")
                        else:
                            net_normal_amount = (
                                normal_amount
                                / vat_factor
                            )
                            net_mortgage_amount = (
                                mortgage_amount
                                / vat_factor
                            )
                            gross_factor = vat_factor
                        commission = (
                            net_normal_amount
                            * normal_commission_percent
                            / Decimal("100")
                            +
                            net_mortgage_amount
                            * mortgage_commission_percent
                            / Decimal("100")
                        )
                        return (
                            round(commission),
                            round(
                                commission
                                * gross_factor
                            )
                        )
                    continue
                # -------------------------------------------------
                # Collection
                # -------------------------------------------------
                if event_type == "collection":
                    collection = obj
                    policy = collection.policy
                    collection_amount = Decimal(
                        str(
                            collection.settlement_amount
                            or 0
                        )
                    )
                    policy_premium = Decimal(
                        str(
                            policy.premium
                            or 0
                        )
                    )
                    if policy_premium == 0:
                        mortgage_collection = (
                            Decimal("0")
                        )
                    else:
                        mortgage_ratio = (
                            Decimal(
                                str(
                                    policy.mortgage_premium
                                    or 0
                                )
                            )
                            / policy_premium
                        )
                        mortgage_collection = (
                            collection_amount
                            * mortgage_ratio
                        )
                    if (
                        policy.insurance_type
                        and
                        policy.insurance_type.display_name
                        in VAT_EXEMPT_TYPES
                    ):
                        net_collection = (
                            collection_amount
                        )
                        net_mortgage_collection = (
                            mortgage_collection
                        )
                    else:
                        net_collection = (
                            collection_amount
                            / vat_factor
                        )
                        net_mortgage_collection = (
                            mortgage_collection
                            / vat_factor
                        )
                    cumulative_before = (
                        cumulative_collection
                    )
                    mortgage_cumulative_before = (
                        cumulative_mortgage_collection
                    )
                    cumulative_collection += (
                        net_collection
                    )
                    cumulative_mortgage_collection += (
                        net_mortgage_collection
                    )
                    previous_split_commission = (
                        calculate_split_collection_commission(
                            cumulative_before,
                            mortgage_cumulative_before,
                            normal_commission_percent,
                            mortgage_commission_percent,
                            first_step_commission
                        )
                    )
                    current_split_commission = (
                        calculate_split_collection_commission(
                            cumulative_collection,
                            cumulative_mortgage_collection,
                            normal_commission_percent,
                            mortgage_commission_percent,
                            first_step_commission
                        )
                    )
                    event_commission = (
                        current_split_commission
                        - previous_split_commission
                    )
                    outstanding_gross -= (
                        collection_amount
                    )
                    if collection.id in target_collection_ids:
                        gross_factor = (
                            vat_factor
                            if not (
                                policy.insurance_type
                                and
                                policy.insurance_type.display_name
                                in VAT_EXEMPT_TYPES
                            )
                            else Decimal("1")
                        )
                        return (
                            round(event_commission),
                            round(
                                event_commission
                                * gross_factor
                            )
                        )
                    continue
                # -------------------------------------------------
                # Negative endorsement before target collection
                # -------------------------------------------------
                if event_type == "negative":
                    policy = obj
                    returned_amount_gross = abs(
                        Decimal(
                            str(
                                policy.premium
                                or 0
                            )
                        )
                    )
                    unpaid_gross = max(
                        outstanding_gross,
                        Decimal("0")
                    )
                    effective_return_gross = max(
                        returned_amount_gross
                        - unpaid_gross,
                        Decimal("0")
                    )
                    outstanding_gross -= min(
                        returned_amount_gross,
                        max(
                            outstanding_gross,
                            Decimal("0")
                        )
                    )
                    if effective_return_gross > 0:
                        policy_premium = Decimal(
                            str(
                                policy.premium
                                or 0
                            )
                        )
                        if policy_premium != 0:
                            mortgage_ratio = (
                                Decimal(
                                    str(
                                        policy.mortgage_premium
                                        or 0
                                    )
                                )
                                / policy_premium
                            )
                            mortgage_return_gross = (
                                effective_return_gross
                                * mortgage_ratio
                            )
                            if (
                                policy.insurance_type
                                and
                                policy.insurance_type.display_name
                                in VAT_EXEMPT_TYPES
                            ):
                                net_return = (
                                    effective_return_gross
                                )
                                net_mortgage_return = (
                                    mortgage_return_gross
                                )
                            else:
                                net_return = (
                                    effective_return_gross
                                    / vat_factor
                                )
                                net_mortgage_return = (
                                    mortgage_return_gross
                                    / vat_factor
                                )
                            cumulative_collection -= (
                                net_return
                            )
                            cumulative_mortgage_collection -= (
                                net_mortgage_return
                            )
                    continue
            return 0, 0
        return 0, 0
    finally:
        db.close()
def calculate_collection_issuance_amount(
    collection_amount,
    issuance_percent,
    first_step_commission
):
    first_step_issuance = (
        first_step_commission / 5
    )
    sec_step_issuance = (
        first_step_issuance * 5
    )
    th_step_issuance = (
        sec_step_issuance * 2
    )
    if collection_amount <= first_step_issuance:
        issuance = (
            collection_amount
            * issuance_percent
            / 100
        )
    elif collection_amount <= sec_step_issuance:
        issuance = (
            first_step_issuance
            * issuance_percent
            / 100
            + (
                collection_amount
                - first_step_issuance
            )
            * Decimal("0.25")
            * issuance_percent
            / 100
        )
    elif collection_amount <= th_step_issuance:
        issuance = (
            first_step_issuance
            * issuance_percent
            / 100
            + (
                sec_step_issuance
                - first_step_issuance
            )
            * Decimal("0.25")
            * issuance_percent
            / 100
            + (
                collection_amount
                - sec_step_issuance
            )
            * Decimal("0.1")
            * issuance_percent
            / 100
        )
    else:
        issuance = (
            first_step_issuance
            * issuance_percent
            / 100
            + (
                sec_step_issuance
                - first_step_issuance
            )
            * Decimal("0.25")
            * issuance_percent
            / 100
            + (
                th_step_issuance
                - sec_step_issuance
            )
            * Decimal("0.1")
            * issuance_percent
            / 100
            + (
                collection_amount
                - th_step_issuance
            )
            * Decimal("0.05")
            * issuance_percent
            / 100
        )
    return issuance
def calculate_cumulative_collection_issuance(
    issue_code,
    policy_id
):
    db = SessionLocal()
    try:
        policies = (
            db.query(Policy)
            .filter(
                Policy.issue_code == issue_code
            )
            .order_by(
                Policy.endorsement_number.asc()
            )
            .all()
        )
        if not policies:
            return 0, 0
        target_policy = next(
            (
                policy
                for policy in policies
                if policy.id == policy_id
            ),
            None
        )
        if not target_policy:
            return 0, 0
        # -------------------------------------------------
        # بیمه‌نامه اصلی
        # -------------------------------------------------
        original_policy = next(
            (
                policy
                for policy in policies
                if policy.endorsement_number == 0
            ),
            policies[0]
        )
        # ==================================================
        # نسبت صندوق بیمه اصلی برای شخص ثالث
        # ==================================================
        fund_ratio = 0
        if (
            original_policy.insurance_type
            and original_policy.insurance_type.display_name == "شخص ثالث خودرو"
        ):
            original_premium = original_policy.premium or 0
            original_fund = original_policy.fund or 0
            if original_premium > 0 and original_fund > 0:
                fund_ratio = original_fund / original_premium
        original_config = get_commission_config_by_date(
            original_policy.issue_date
        )
        if not original_config:
            return 0, 0
        first_step_commission = (
            original_config.first_step_commission
        )
        # درصد هزینه صدور از بیمه‌نامه اصلی
        original_type_commission = (
            get_insurance_type_commission_by_date(
                original_policy.insurance_type_id,
                original_policy.issue_date
            )
        )
        if not original_type_commission:
            return 0, 0
        issuance_percent = (
            original_type_commission.issuance_percent
            or 0
        )
        # -------------------------------------------------
        # تمام وصول‌ها
        # -------------------------------------------------
        all_collections = (
            db.query(Collection)
            .filter(
                Collection.policy_id.in_(
                    [policy.id for policy in policies]
                )
            )
            .all()
        )
        # -------------------------------------------------
        # ساخت رویدادها
        #
        # premium:
        #   افزایش بدهی ناخالص
        #
        # collection:
        #   کاهش بدهی ناخالص
        #   افزایش وصول خالص
        #
        # negative_endorsement:
        #   مقایسه برگشت ناخالص با بدهی ناخالص
        #   و در صورت وجود مازاد، کاهش وصول خالص
        # -------------------------------------------------
        events = []
        # بیمه‌نامه اصلی + الحاقیه‌های مثبت
        for policy in policies:
            premium = policy.premium or 0
            if premium <= 0:
                continue
            events.append(
                (
                    policy.issue_date,
                    0,
                    policy.id,
                    "premium",
                    policy,
                    None,
                    premium
                )
            )
        # وصول‌ها
        for collection in all_collections:
            amount = (
                collection.settlement_amount or 0
            )
            if amount <= 0:
                continue
            policy = collection.policy
            if not policy:
                continue
            events.append(
                (
                    collection.collection_date,
                    1,
                    collection.id,
                    "collection",
                    policy,
                    collection.id,
                    amount
                )
            )
        # برگشت‌ها
        for policy in policies:
            premium = policy.premium or 0
            if premium >= 0:
                continue
            returned_amount_gross = abs(premium)
            events.append(
                (
                    policy.issue_date,
                    2,
                    policy.id,
                    "negative_endorsement",
                    policy,
                    None,
                    returned_amount_gross
                )
            )
        # ترتیب زمانی
        events.sort(
            key=lambda event: (
                event[0],
                event[1],
                event[2]
            )
        )
        # -------------------------------------------------
        # وضعیت تجمعی
        # -------------------------------------------------
        outstanding_gross = 0
        cumulative_collection = 0
        # -------------------------------------------------
        # اگر خود بیمه‌نامه هدف، برگشتی است
        # -------------------------------------------------
        if (
            target_policy.premium is not None
            and target_policy.premium < 0
        ):
            for (
                event_date,
                event_type_order,
                event_id,
                event_type,
                policy,
                collection_id,
                amount
            ) in events:
                # -----------------------------
                # حق‌بیمه / الحاقیه مثبت
                # -----------------------------
                if event_type == "premium":
                    outstanding_gross += amount
                    continue
                # -----------------------------
                # وصول
                # -----------------------------
                if event_type == "collection":
                    outstanding_gross = max(
                        outstanding_gross - amount,
                        0
                    )
                    config = get_commission_config_by_date(
                        policy.issue_date
                    )
                    if not config:
                        return 0, 0
                    insurance_type = policy.insurance_type
                    is_vat_exempt = (
                        insurance_type
                        and insurance_type.display_name
                        in VAT_EXEMPT_TYPES
                    )
                    # --------------------------------------
                    # کسر سهم صندوق از وصولی شخص ثالث
                    # --------------------------------------
                    commissionable_amount = (
                        amount * (1 - fund_ratio)
                    )
                    if is_vat_exempt:
                        collection_net = commissionable_amount
                    else:
                        collection_net = (
                            commissionable_amount
                            / (1 + config.vat)
                        )
                    continue
                # -----------------------------
                # برگشت
                # -----------------------------
                if event_type == "negative_endorsement":
                    returned_amount_gross = amount
                    unpaid_gross = max(
                        outstanding_gross,
                        0
                    )
                    # فقط مازاد برگشت بر بدهی مؤثر است
                    effective_return_gross = max(
                        returned_amount_gross
                        - unpaid_gross,
                        0
                    )
                    # کاهش بدهی ناخالص
                    outstanding_gross = max(
                        outstanding_gross
                        - returned_amount_gross,
                        0
                    )
                    # اگر این همان برگشت هدف است
                    if policy.id == target_policy.id:
                        # برگشت تا سقف بدهی،
                        # هیچ اثری روی هزینه صدور ندارد
                        if effective_return_gross == 0:
                            return 0, 0
                        config = get_commission_config_by_date(
                            policy.issue_date
                        )
                        if not config:
                            return 0, 0
                        insurance_type = policy.insurance_type
                        is_vat_exempt = (
                            insurance_type
                            and insurance_type.display_name
                            in VAT_EXEMPT_TYPES
                        )
                        # --------------------------------------
                        # کسر سهم صندوق از برگشت مؤثر شخص ثالث
                        # --------------------------------------
                        commissionable_return = (
                            effective_return_gross
                            * (1 - fund_ratio)
                        )
                        if is_vat_exempt:
                            effective_return_net = (
                                commissionable_return
                            )
                        else:
                            effective_return_net = (
                                commissionable_return
                                / (1 + config.vat)
                            )
                        # هزینه صدور قبل از برگشت
                        previous_issuance = (
                            calculate_collection_issuance_amount(
                                cumulative_collection,
                                issuance_percent,
                                first_step_commission
                            )
                        )
                        # برگشت مؤثر از وصول تجمعی کم می‌شود
                        cumulative_collection = max(
                            cumulative_collection
                            - effective_return_net,
                            0
                        )
                        # هزینه صدور بعد از برگشت
                        current_issuance = (
                            calculate_collection_issuance_amount(
                                cumulative_collection,
                                issuance_percent,
                                first_step_commission
                            )
                        )
                        issuance_difference = (
                            current_issuance
                            - previous_issuance
                        )
                        if is_vat_exempt:
                            gross_issuance = (
                                issuance_difference
                            )
                        else:
                            gross_issuance = (
                                issuance_difference
                                * (1 + config.vat)
                            )
                        return (
                            round(issuance_difference),
                            round(gross_issuance)
                        )
                    # برگشت مربوط به قبل از برگشت هدف
                    # باید روی cumulative اثر بگذارد
                    if effective_return_gross > 0:
                        config = get_commission_config_by_date(
                            policy.issue_date
                        )
                        if not config:
                            return 0, 0
                        insurance_type = policy.insurance_type
                        is_vat_exempt = (
                            insurance_type
                            and insurance_type.display_name
                            in VAT_EXEMPT_TYPES
                        )
                        # --------------------------------------
                        # کسر سهم صندوق از برگشت مؤثر شخص ثالث
                        # --------------------------------------
                        commissionable_return = (
                            effective_return_gross
                            * (1 - fund_ratio)
                        )
                        if is_vat_exempt:
                            effective_return_net = (
                                commissionable_return
                            )
                        else:
                            effective_return_net = (
                                commissionable_return
                                / (1 + config.vat)
                            )
                        cumulative_collection = max(
                            cumulative_collection
                            - effective_return_net,
                            0
                        )
            return 0, 0
        # -------------------------------------------------
        # هدف یک وصول است
        # -------------------------------------------------
        cumulative_collection = 0
        outstanding_gross = 0
        total_issuance = 0
        total_gross_issuance = 0
        target_collection_ids = {
            collection.id
            for collection in all_collections
            if (
                collection.policy_id == target_policy.id
                and (collection.settlement_amount or 0) > 0
            )
        }
        last_target_collection_id = None
        # -------------------------------------------------
        # پردازش رویدادها
        # -------------------------------------------------
        for (
            event_date,
            event_type_order,
            event_id,
            event_type,
            policy,
            collection_id,
            amount
        ) in events:
            # ---------------------------------------------
            # حق‌بیمه / الحاقیه مثبت
            # ---------------------------------------------
            if event_type == "premium":
                outstanding_gross += amount
                continue
            # ---------------------------------------------
            # وضعیت قبل از رویداد
            # ---------------------------------------------
            previous_issuance = (
                calculate_collection_issuance_amount(
                    cumulative_collection,
                    issuance_percent,
                    first_step_commission
                )
            )
            # ---------------------------------------------
            # وصول
            # ---------------------------------------------
            if event_type == "collection":
                outstanding_gross = max(
                    outstanding_gross - amount,
                    0
                )
                config = get_commission_config_by_date(
                    policy.issue_date
                )
                if not config:
                    return 0, 0
                insurance_type = policy.insurance_type
                is_vat_exempt = (
                    insurance_type
                    and insurance_type.display_name
                    in VAT_EXEMPT_TYPES
                )
                # --------------------------------------
                # کسر سهم صندوق از وصولی شخص ثالث
                # --------------------------------------
                commissionable_amount = (
                    amount * (1 - fund_ratio)
                )
                if is_vat_exempt:
                    collection_net = commissionable_amount
                else:
                    collection_net = (
                        commissionable_amount
                        / (1 + config.vat)
                    )
            # ---------------------------------------------
            # برگشت
            # ---------------------------------------------
            elif event_type == "negative_endorsement":
                returned_amount_gross = amount
                unpaid_gross = max(
                    outstanding_gross,
                    0
                )
                effective_return_gross = max(
                    returned_amount_gross
                    - unpaid_gross,
                    0
                )
                outstanding_gross = max(
                    outstanding_gross
                    - returned_amount_gross,
                    0
                )
                # اگر برگشت هیچ مازادی نداشته باشد،
                # هیچ اثری روی هزینه صدور ندارد.
                if effective_return_gross == 0:
                    continue
                config = get_commission_config_by_date(
                    policy.issue_date
                )
                if not config:
                    return 0, 0
                insurance_type = policy.insurance_type
                is_vat_exempt = (
                    insurance_type
                    and insurance_type.display_name
                    in VAT_EXEMPT_TYPES
                )
                # --------------------------------------
                # کسر سهم صندوق از برگشت مؤثر شخص ثالث
                # --------------------------------------
                commissionable_return = (
                    effective_return_gross
                    * (1 - fund_ratio)
                )
                if is_vat_exempt:
                    effective_return_net = (
                        commissionable_return
                    )
                else:
                    effective_return_net = (
                        commissionable_return
                        / (1 + config.vat)
                    )
                cumulative_collection = max(
                    cumulative_collection
                    - effective_return_net,
                    0
                )
            # ---------------------------------------------
            # هزینه صدور بعد از رویداد
            # ---------------------------------------------
            current_issuance = (
                calculate_collection_issuance_amount(
                    cumulative_collection,
                    issuance_percent,
                    first_step_commission
                )
            )
            event_issuance = (
                current_issuance
                - previous_issuance
            )
            config = get_commission_config_by_date(
                policy.issue_date
            )
            if not config:
                return 0, 0
            insurance_type = policy.insurance_type
            is_vat_exempt = (
                insurance_type
                and insurance_type.display_name
                in VAT_EXEMPT_TYPES
            )
            if is_vat_exempt:
                gross_event_issuance = (
                    event_issuance
                )
            else:
                gross_event_issuance = (
                    event_issuance
                    * (1 + config.vat)
                )
            # ---------------------------------------------
            # فقط وصول هدف را در خروجی جمع کن
            # ---------------------------------------------
            if (
                event_type == "collection"
                and collection_id in target_collection_ids
            ):
                total_issuance += event_issuance
                total_gross_issuance += (
                    gross_event_issuance
                )
                last_target_collection_id = (
                    collection_id
                )
            if (
                last_target_collection_id is not None
                and event_type == "collection"
                and collection_id == last_target_collection_id
            ):
                break
        return (
            round(total_issuance),
            round(total_gross_issuance)
        )
    finally:
        db.close()
'''def calculate_commission_report(
    issue_code,
    basis,
    start_date,
    end_date
):
    """
    گزارش کارمزد یک بیمه‌نامه و الحاقیه‌های آن
    در یک بازه زمانی مشخص.
    basis:
        "premium"     -> بر اساس تاریخ صدور/الحاقیه
        "collection"  -> بر اساس تاریخ وصول
    """
    if basis not in {"premium", "collection"}:
        raise ValueError(
            "basis must be 'premium' or 'collection'"
        )
    db = SessionLocal()
    try:
        policies = (
            db.query(Policy)
            .filter(
                Policy.issue_code == issue_code
            )
            .order_by(
                Policy.endorsement_number.asc()
            )
            .all()
        )
        if not policies:
            return {
                "basis": basis,
                "start_date": start_date,
                "end_date": end_date,
                "details": [],
                "total_commission": 0,
                "total_gross_commission": 0,
            }
        original_policy = policies[0]
        # =====================================================
        # تنظیمات بیمه‌نامه اصلی
        # =====================================================
        original_config = (
            db.query(CommissionConfig)
            .filter(
                CommissionConfig.effective_date
                <= original_policy.issue_date
            )
            .order_by(
                CommissionConfig.effective_date.desc()
            )
            .first()
        )
        if not original_config:
            return {
                "basis": basis,
                "start_date": start_date,
                "end_date": end_date,
                "details": [],
                "total_commission": 0,
                "total_gross_commission": 0,
            }
        first_step_commission = (
            original_config.first_step_commission
        )
        # نرخ کارمزد رشته فقط از بیمه‌نامه اصلی
        original_type_commission = (
            db.query(InsuranceTypeCommission)
            .filter(
                InsuranceTypeCommission.insurance_type_id
                == original_policy.insurance_type_id,
                InsuranceTypeCommission.effective_date
                <= original_policy.issue_date
            )
            .order_by(
                InsuranceTypeCommission.effective_date.desc()
            )
            .first()
        )
        if not original_type_commission:
            return {
                "basis": basis,
                "start_date": start_date,
                "end_date": end_date,
                "details": [],
                "total_commission": 0,
                "total_gross_commission": 0,
            }
        if original_policy.is_mortgage:
            commission_percent = (
                original_type_commission.mortgage_commission
                or 0
            )
        else:
            commission_percent = (
                original_type_commission.normal_commission
                or 0
            )
        details = []
        total_commission = 0
        total_gross_commission = 0
        # =====================================================
        # نسبت صندوق بیمه اصلی برای شخص ثالث
        # =====================================================
        fund_ratio = Decimal("0")
        if (
            original_policy.insurance_type
            and original_policy.insurance_type.display_name == "شخص ثالث خودرو"
        ):
            original_premium = original_policy.premium or 0
            original_fund = original_policy.fund or 0
            if original_premium > 0 and original_fund > 0:
                fund_ratio = (
                    Decimal(str(original_fund))
                    / Decimal(str(original_premium))
                )
        # =====================================================
        # گزارش بر اساس حق‌بیمه
        # =====================================================
        if basis == "premium":
            cumulative_premium = 0
            for policy in policies:
                premium = policy.premium or 0
                if premium == 0:
                    continue
                # VAT بر اساس تاریخ صدور همان بیمه‌نامه/الحاقیه
                vat_config = (
                    db.query(CommissionConfig)
                    .filter(
                        CommissionConfig.effective_date
                        <= policy.issue_date
                    )
                    .order_by(
                        CommissionConfig.effective_date.desc()
                    )
                    .first()
                )
                if not vat_config:
                    continue
                vat_factor = 1 + vat_config.vat
                # ---------------------------------------------
                # کسر سهم صندوق از حق‌بیمه شخص ثالث
                # ---------------------------------------------
                commissionable_premium = (
                    premium * (1 - fund_ratio)
                )
                if (
                    policy.insurance_type.display_name
                    not in VAT_EXEMPT_TYPES
                ):
                    net_premium = (
                        commissionable_premium
                        / vat_factor
                    )
                    gross_factor = vat_factor
                else:
                    net_premium = (
                        commissionable_premium
                    )
                    gross_factor = 1
                previous_premium = cumulative_premium
                cumulative_premium += net_premium
                previous_commission = (
                    calculate_base_commission(
                        previous_premium,
                        commission_percent,
                        first_step_commission
                    )
                )
                current_commission = (
                    calculate_base_commission(
                        cumulative_premium,
                        commission_percent,
                        first_step_commission
                    )
                )
                commission_difference = (
                    current_commission
                    - previous_commission
                )
                gross_commission_difference = (
                    commission_difference
                    * gross_factor
                )
                # فقط رکوردهای داخل بازه گزارش
                if (
                    start_date
                    <= policy.issue_date
                    <= end_date
                ):
                    commission_difference = round(
                        commission_difference
                    )
                    gross_commission_difference = round(
                        gross_commission_difference
                    )
                    details.append({
                        "policy_id": policy.id,
                        "endorsement_number":
                            policy.endorsement_number,
                        "date":
                            policy.issue_date,
                        "premium":
                            premium,
                        "net_premium":
                            round(net_premium),
                        "commission_percent":
                            commission_percent,
                        "commission":
                            commission_difference,
                        "gross_commission":
                            gross_commission_difference,
                    })
                    total_commission += (
                        commission_difference
                    )
                    total_gross_commission += (
                        gross_commission_difference
                    )
        # =====================================================
        # گزارش بر اساس وصولی
        # =====================================================
        else:
            events = []
            # -------------------------------------------------
            # ساخت رویدادهای بیمه‌نامه، وصول و الحاقیه منفی
            # -------------------------------------------------
            for policy in policies:
                # VAT مربوط به تاریخ صدور بیمه‌نامه
                vat_config = (
                    db.query(CommissionConfig)
                    .filter(
                        CommissionConfig.effective_date
                        <= policy.issue_date
                    )
                    .order_by(
                        CommissionConfig.effective_date.desc()
                    )
                    .first()
                )
                if not vat_config:
                    continue
                vat_factor = 1 + vat_config.vat
                if (
                    policy.insurance_type.display_name
                    not in VAT_EXEMPT_TYPES
                ):
                    gross_factor = vat_factor
                else:
                    gross_factor = 1
                premium = policy.premium or 0
                # -------------------------------------------------
                # بیمه‌نامه / الحاقیه مثبت
                # برای محاسبه بدهی ناخالص
                # -------------------------------------------------
                if premium > 0:
                    events.append({
                        "event_type": "premium",
                        "date": policy.issue_date,
                        "id": policy.id,
                        "policy": policy,
                        "amount": premium,
                        "vat_factor": vat_factor,
                        "gross_factor": gross_factor,
                    })
                # -------------------------------------------------
                # الحاقیه منفی
                # -------------------------------------------------
                elif premium < 0:
                    events.append({
                        "event_type": "negative_endorsement",
                        "date": policy.issue_date,
                        "id": policy.id,
                        "policy": policy,
                        "amount": abs(premium),
                        "vat_factor": vat_factor,
                        "gross_factor": gross_factor,
                    })
                # -------------------------------------------------
                # وصولی‌ها
                # -------------------------------------------------
                collections = (
                    db.query(Collection)
                    .filter(
                        Collection.policy_id == policy.id
                    )
                    .order_by(
                        Collection.collection_date.asc(),
                        Collection.id.asc()
                    )
                    .all()
                )
                for collection in collections:
                    amount = (
                        collection.settlement_amount
                        or 0
                    )
                    if amount <= 0:
                        continue
                    events.append({
                        "event_type": "collection",
                        "date": collection.collection_date,
                        "id": collection.id,
                        "policy": policy,
                        "collection": collection,
                        "amount": amount,
                        "vat_factor": vat_factor,
                        "gross_factor": gross_factor,
                    })
            # -------------------------------------------------
            # ترتیب رویدادها
            #
            # در یک تاریخ:
            # 1. بیمه‌نامه
            # 2. وصول
            # 3. الحاقیه منفی
            # -------------------------------------------------
            event_order = {
                "premium": 0,
                "collection": 1,
                "negative_endorsement": 2,
            }
            events.sort(
                key=lambda event: (
                    event["date"],
                    event_order[event["event_type"]],
                    event["id"],
                )
            )
            # -------------------------------------------------
            # وضعیت تجمعی
            # -------------------------------------------------
            cumulative_collection = 0
            outstanding_gross = 0
            # -------------------------------------------------
            # پردازش رویدادها
            # -------------------------------------------------
            for event in events:
                event_type = event["event_type"]
                policy = event["policy"]
                amount = event["amount"]
                vat_factor = event["vat_factor"]
                gross_factor = event["gross_factor"]
                # =================================================
                # بیمه‌نامه / الحاقیه مثبت
                # =================================================
                if event_type == "premium":
                    outstanding_gross += amount
                    continue
                # =================================================
                # وصول
                # =================================================
                if event_type == "collection":
                    # ---------------------------------------------
                    # کاهش بدهی ناخالص
                    # ---------------------------------------------
                    outstanding_gross = max(
                        outstanding_gross - amount,
                        0
                    )
                    # ---------------------------------------------
                    # کسر سهم صندوق از وصولی شخص ثالث
                    # ---------------------------------------------
                    commissionable_amount = (
                        amount * (1 - fund_ratio)
                    )
                    # ---------------------------------------------
                    # تبدیل مبلغ مشمول کارمزد به خالص
                    # ---------------------------------------------
                    if (
                        policy.insurance_type.display_name
                        not in VAT_EXEMPT_TYPES
                    ):
                        net_amount = (
                            commissionable_amount
                            / vat_factor
                        )
                    else:
                        net_amount = (
                            commissionable_amount
                        )
                    # ---------------------------------------------
                    # کارمزد تجمعی قبل
                    # ---------------------------------------------
                    previous_collection = (
                        cumulative_collection
                    )
                    previous_commission = (
                        calculate_collection_commission_amount(
                            previous_collection,
                            commission_percent,
                            first_step_commission
                        )
                    )
                    # ---------------------------------------------
                    # اضافه شدن وصول
                    # ---------------------------------------------
                    cumulative_collection += net_amount
                    # ---------------------------------------------
                    # کارمزد تجمعی بعد
                    # ---------------------------------------------
                    current_commission = (
                        calculate_collection_commission_amount(
                            cumulative_collection,
                            commission_percent,
                            first_step_commission
                        )
                    )
                    commission_difference = (
                        current_commission
                        - previous_commission
                    )
                    # ---------------------------------------------
                    # کارمزد ناخالص
                    # ---------------------------------------------
                    gross_commission_difference = (
                        commission_difference
                        * gross_factor
                    )
                    # ---------------------------------------------
                    # فقط وصول‌های داخل بازه گزارش
                    # ---------------------------------------------
                    if (
                        start_date
                        <= event["date"]
                        <= end_date
                    ):
                        details.append({
                            "policy_id":
                                policy.id,
                            "endorsement_number":
                                policy.endorsement_number,
                            "date":
                                event["date"],
                            "collection_amount":
                                amount,
                            "net_collection_amount":
                                round(net_amount),
                            "cumulative_net_collection":
                                round(
                                    cumulative_collection
                                ),
                            "commission_percent":
                                commission_percent,
                            "commission":
                                round(
                                    commission_difference
                                ),
                            "gross_commission":
                                round(
                                    gross_commission_difference
                                ),
                        })
                        total_commission += (
                            round(
                                commission_difference
                            )
                        )
                        total_gross_commission += (
                            round(
                                gross_commission_difference
                            )
                        )
                    continue
                # =================================================
                # الحاقیه منفی
                # =================================================
                if event_type == "negative_endorsement":
                    returned_amount_gross = amount
                    # ---------------------------------------------
                    # بدهی پرداخت‌نشده فعلی
                    # ---------------------------------------------
                    unpaid_gross = max(
                        outstanding_gross,
                        0
                    )
                    # ---------------------------------------------
                    # ابتدا برگشتی با بدهی ناخالص مقایسه می‌شود
                    # ---------------------------------------------
                    effective_return_gross = max(
                        returned_amount_gross
                        - unpaid_gross,
                        0
                    )
                    # ---------------------------------------------
                    # کل مبلغ برگشتی، بدهی را کاهش می‌دهد
                    # ---------------------------------------------
                    outstanding_gross = max(
                        outstanding_gross
                        - returned_amount_gross,
                        0
                    )
                    # اگر کل برگشتی صرف تسویه بدهی شده،
                    # اثری روی کارمزد ندارد
                    if effective_return_gross <= 0:
                        continue
                    # ---------------------------------------------
                    # کسر سهم صندوق از برگشتی مؤثر
                    # ---------------------------------------------
                    commissionable_return = (
                        effective_return_gross
                        * (1 - fund_ratio)
                    )
                    # ---------------------------------------------
                    # تبدیل برگشتی مؤثر به خالص
                    # ---------------------------------------------
                    if (
                        policy.insurance_type.display_name
                        not in VAT_EXEMPT_TYPES
                    ):
                        effective_return_net = (
                            commissionable_return
                            / vat_factor
                        )
                    else:
                        effective_return_net = (
                            commissionable_return
                        )
                    # ---------------------------------------------
                    # کارمزد تجمعی قبل از برگشتی
                    # ---------------------------------------------
                    previous_collection = (
                        cumulative_collection
                    )
                    previous_commission = (
                        calculate_collection_commission_amount(
                            previous_collection,
                            commission_percent,
                            first_step_commission
                        )
                    )
                    # ---------------------------------------------
                    # برگشتی مؤثر از وصول تجمعی کم می‌شود
                    # ---------------------------------------------
                    cumulative_collection = max(
                        cumulative_collection
                        - effective_return_net,
                        0
                    )
                    # ---------------------------------------------
                    # کارمزد تجمعی بعد از برگشتی
                    # ---------------------------------------------
                    current_commission = (
                        calculate_collection_commission_amount(
                            cumulative_collection,
                            commission_percent,
                            first_step_commission
                        )
                    )
                    # ---------------------------------------------
                    # اختلاف کارمزد = منفی
                    # ---------------------------------------------
                    commission_difference = (
                        current_commission
                        - previous_commission
                    )
                    # ---------------------------------------------
                    # کارمزد ناخالص منفی
                    # ---------------------------------------------
                    gross_commission_difference = (
                        commission_difference
                        * gross_factor
                    )
                    # ---------------------------------------------
                    # فقط الحاقیه‌های منفی داخل بازه گزارش
                    # ---------------------------------------------
                    if (
                        start_date
                        <= event["date"]
                        <= end_date
                    ):
                        details.append({
                            "policy_id":
                                policy.id,
                            "endorsement_number":
                                policy.endorsement_number,
                            "date":
                                event["date"],
                            "collection_amount":
                                -effective_return_gross,
                            "net_collection_amount":
                                -round(
                                    effective_return_net
                                ),
                            "cumulative_net_collection":
                                round(
                                    cumulative_collection
                                ),
                            "commission_percent":
                                commission_percent,
                            "commission":
                                round(
                                    commission_difference
                                ),
                            "gross_commission":
                                round(
                                    gross_commission_difference
                                ),
                        })
                        total_commission += (
                            round(
                                commission_difference
                            )
                        )
                        total_gross_commission += (
                            round(
                                gross_commission_difference
                            )
                        )
            # -------------------------------------------------
            # مرتب‌سازی نهایی گزارش
            # -------------------------------------------------
            details.sort(
                key=lambda item: (
                    item["date"],
                    item["policy_id"]
                )
            )
        return {
            "basis":
                basis,
            "start_date":
                start_date,
            "end_date":
                end_date,
            "details":
                details,
            "total_commission":
                round(total_commission),
            "total_gross_commission":
                round(total_gross_commission),
        }
    finally:
        db.close()
def calculate_issuance_report(
    issue_code,
    basis,
    start_date,
    end_date
):
    """
    گزارش هزینه صدور یک بیمه‌نامه و الحاقیه‌های آن
    در یک بازه زمانی مشخص.
    basis:
        "premium"    -> بر اساس تاریخ صدور/الحاقیه
        "collection" -> بر اساس تاریخ وصول
    نکته:
    محاسبه تجمعی هزینه صدور بر اساس کل issue_code انجام می‌شود،
    اما هزینه صدور فقط برای بیمه‌نامه‌هایی منظور می‌شود که
    صادرکننده آنها current_agent باشد.
    """
    if basis not in {"premium", "collection"}:
        raise ValueError(
            "basis must be 'premium' or 'collection'"
        )
    current_agent = get_current_agent()
    db = SessionLocal()
    try:
        policies = (
            db.query(Policy)
            .options(
                joinedload(Policy.insurance_type)
            )
            .filter(
                Policy.issue_code == issue_code
            )
            .order_by(
                Policy.endorsement_number.asc(),
                Policy.id.asc()
            )
            .all()
        )
        if not policies:
            return {
                "details": [],
                "total_issuance": 0,
                "total_gross_issuance": 0,
            }
        original_policy = policies[0]
        config = get_commission_config_by_date(
            original_policy.issue_date
        )
        if not config:
            return {
                "details": [],
                "total_issuance": 0,
                "total_gross_issuance": 0,
            }
        insurance_type_commission = (
            get_insurance_type_commission_by_date(
                original_policy.insurance_type_id,
                original_policy.issue_date
            )
        )
        if not insurance_type_commission:
            return {
                "details": [],
                "total_issuance": 0,
                "total_gross_issuance": 0,
            }
        # هزینه صدور هیچ وابستگی به مرهوناتی ندارد.
        issuance_percent = (
            insurance_type_commission.issuance_percent or 0
        )
        first_step_commission = (
            config.first_step_commission or 0
        )
        # =========================================================
        # نسبت صندوق بیمه اصلی برای شخص ثالث
        # =========================================================
        fund_ratio = 0
        if (
            original_policy.insurance_type
            and original_policy.insurance_type.display_name == "شخص ثالث خودرو"
        ):
            original_premium = original_policy.premium or 0
            original_fund = original_policy.fund or 0
            if original_premium > 0 and original_fund > 0:
                fund_ratio = (
                    original_fund
                    / original_premium
                )
        details = []
        # =========================================================
        # PREMIUM BASIS
        # =========================================================
        if basis == "premium":
            cumulative_net_premium = 0
            previous_issuance = 0
            for policy in policies:
                premium = policy.premium or 0
                vat = 0
                if (
                    policy.insurance_type
                    and policy.insurance_type.display_name
                    not in VAT_EXEMPT_TYPES
                ):
                    vat = config.vat or 0
                gross_factor = 1 + vat
                # -------------------------------------------------
                # کسر سهم صندوق از حق‌بیمه شخص ثالث
                # -------------------------------------------------
                commissionable_premium = (
                    premium
                    * (1 - fund_ratio)
                )
                # -------------------------------------------------
                # حق بیمه خالص
                # -------------------------------------------------
                if (
                    policy.insurance_type
                    and policy.insurance_type.display_name
                    in VAT_EXEMPT_TYPES
                ):
                    net_premium = (
                        commissionable_premium
                    )
                else:
                    net_premium = (
                        commissionable_premium
                        / gross_factor
                    )
                # -------------------------------------------------
                # تجمع حق بیمه خالص
                # -------------------------------------------------
                cumulative_net_premium += net_premium
                # -------------------------------------------------
                # هزینه صدور تجمعی
                # -------------------------------------------------
                current_cumulative_issuance = (
                    calculate_base_issuance(
                        cumulative_net_premium,
                        issuance_percent,
                        first_step_commission
                    )
                )
                issuance_difference = (
                    current_cumulative_issuance
                    - previous_issuance
                )
                previous_issuance = (
                    current_cumulative_issuance
                )
                gross_issuance_difference = (
                    issuance_difference
                    * gross_factor
                )
                # -------------------------------------------------
                # فقط صادرکننده current_agent
                # -------------------------------------------------
                if policy.issuer != current_agent:
                    continue
                # -------------------------------------------------
                # فقط رکوردهای داخل بازه گزارش
                # -------------------------------------------------
                if not (
                    start_date
                    <= policy.issue_date
                    <= end_date
                ):
                    continue
                details.append({
                    "policy_id": policy.id,
                    "endorsement_number": (
                        policy.endorsement_number
                    ),
                    "date": policy.issue_date,
                    "premium": premium,
                    "net_premium": net_premium,
                    "issuance": issuance_difference,
                    "gross_issuance": gross_issuance_difference,
                })
        # =========================================================
        # COLLECTION BASIS
        # =========================================================
        else:
            events = []
            # -----------------------------------------------------
            # رویدادهای حق بیمه / الحاقیه
            # -----------------------------------------------------
            for policy in policies:
                premium = policy.premium or 0
                # حق بیمه مثبت
                if premium > 0:
                    events.append({
                        "date": policy.issue_date,
                        "event_order": 0,
                        "id": policy.id,
                        "type": "premium",
                        "policy": policy,
                        "amount": premium,
                    })
                # الحاقیه منفی
                elif premium < 0:
                    events.append({
                        "date": policy.issue_date,
                        "event_order": 2,
                        "id": policy.id,
                        "type": "negative",
                        "policy": policy,
                        "amount": premium,
                    })
            # -----------------------------------------------------
            # وصولی‌ها
            # -----------------------------------------------------
            policy_ids = [policy.id for policy in policies]
            collections = (
                db.query(Collection)
                .filter(
                    Collection.policy_id.in_(policy_ids)
                )
                .all()
            )
            policy_map = {
                policy.id: policy
                for policy in policies
            }
            for collection in collections:
                policy = policy_map.get(
                    collection.policy_id
                )
                if not policy:
                    continue
                collection_amount = (
                    collection.settlement_amount or 0
                )
                if collection_amount <= 0:
                    continue
                events.append({
                    "date": collection.collection_date,
                    "event_order": 1,
                    "id": collection.id,
                    "type": "collection",
                    "policy": policy,
                    "amount": collection_amount,
                })
            # -----------------------------------------------------
            # ترتیب رویدادها
            # -----------------------------------------------------
            events.sort(
                key=lambda event: (
                    event["date"],
                    event["event_order"],
                    event["id"]
                )
            )
            cumulative_net_collection = 0
            previous_issuance = 0
            # مبلغ ناخالص حق بیمه‌ای که هنوز وصول نشده
            outstanding_gross = 0
            for event in events:
                policy = event["policy"]
                event_type = event["type"]
                amount = event["amount"]
                # VAT مربوط به همان بیمه‌نامه
                vat = 0
                if (
                    policy.insurance_type
                    and policy.insurance_type.display_name
                    not in VAT_EXEMPT_TYPES
                ):
                    vat = config.vat or 0
                gross_factor = 1 + vat
                # =================================================
                # حق بیمه مثبت
                # =================================================
                if event_type == "premium":
                    outstanding_gross += amount
                    continue
                # =================================================
                # وصولی
                # =================================================
                if event_type == "collection":
                    # فقط بخشی از وصولی که مربوط به بدهی موجود است
                    effective_gross = min(
                        amount,
                        outstanding_gross
                    )
                    if effective_gross <= 0:
                        continue
                    outstanding_gross -= effective_gross
                    # -------------------------------------------------
                    # کسر سهم صندوق از وصولی شخص ثالث
                    # -------------------------------------------------
                    commissionable_collection = (
                        effective_gross
                        * (1 - fund_ratio)
                    )
                    # -------------------------------------------------
                    # تبدیل وصولی مشمول به خالص
                    # -------------------------------------------------
                    if (
                        policy.insurance_type
                        and policy.insurance_type.display_name
                        in VAT_EXEMPT_TYPES
                    ):
                        net_collection = (
                            commissionable_collection
                        )
                    else:
                        net_collection = (
                            commissionable_collection
                            / gross_factor
                        )
                    # -------------------------------------------------
                    # تجمع وصولی خالص
                    # -------------------------------------------------
                    cumulative_net_collection += (
                        net_collection
                    )
                    # -------------------------------------------------
                    # هزینه صدور تجمعی
                    # -------------------------------------------------
                    current_cumulative_issuance = (
                        calculate_base_issuance(
                            cumulative_net_collection,
                            issuance_percent,
                            first_step_commission
                        )
                    )
                    issuance_difference = (
                        current_cumulative_issuance
                        - previous_issuance
                    )
                    previous_issuance = (
                        current_cumulative_issuance
                    )
                    gross_issuance_difference = (
                        issuance_difference
                        * gross_factor
                    )
                    # -------------------------------------------------
                    # فقط صادرکننده current_agent
                    # -------------------------------------------------
                    if policy.issuer != current_agent:
                        continue
                    if not (
                        start_date
                        <= event["date"]
                        <= end_date
                    ):
                        continue
                    details.append({
                        "policy_id": policy.id,
                        "endorsement_number": (
                            policy.endorsement_number
                        ),
                        "date": event["date"],
                        "collection": effective_gross,
                        "net_collection": net_collection,
                        "issuance": issuance_difference,
                        "gross_issuance": (
                            gross_issuance_difference
                        ),
                    })
                    continue
                # =================================================
                # الحاقیه منفی
                # =================================================
                if event_type == "negative":
                    negative_gross = abs(amount)
                    # -------------------------------------------------
                    # ابتدا بدهی وصول‌نشده را کم می‌کند
                    # -------------------------------------------------
                    unpaid_offset = min(
                        negative_gross,
                        outstanding_gross
                    )
                    outstanding_gross -= unpaid_offset
                    remaining_negative = (
                        negative_gross
                        - unpaid_offset
                    )
                    # اگر کل الحاقیه منفی صرفاً بدهی وصول‌نشده
                    # را کم کرده باشد، هنوز اثری روی وصولی تجمعی
                    # ندارد.
                    if remaining_negative <= 0:
                        continue
                    # -------------------------------------------------
                    # کسر سهم صندوق از بخش برگشتی مؤثر
                    # -------------------------------------------------
                    commissionable_negative = (
                        remaining_negative
                        * (1 - fund_ratio)
                    )
                    # -------------------------------------------------
                    # بخش برگشتی که قبلاً وصول شده
                    # -------------------------------------------------
                    if (
                        policy.insurance_type
                        and policy.insurance_type.display_name
                        in VAT_EXEMPT_TYPES
                    ):
                        net_negative = (
                            commissionable_negative
                        )
                    else:
                        net_negative = (
                            commissionable_negative
                            / gross_factor
                        )
                    # -------------------------------------------------
                    # کاهش وصولی تجمعی
                    # -------------------------------------------------
                    cumulative_net_collection -= net_negative
                    # جلوگیری از منفی شدن
                    if cumulative_net_collection < 0:
                        cumulative_net_collection = 0
                    # -------------------------------------------------
                    # محاسبه هزینه صدور جدید
                    # -------------------------------------------------
                    current_cumulative_issuance = (
                        calculate_base_issuance(
                            cumulative_net_collection,
                            issuance_percent,
                            first_step_commission
                        )
                    )
                    issuance_difference = (
                        current_cumulative_issuance
                        - previous_issuance
                    )
                    previous_issuance = (
                        current_cumulative_issuance
                    )
                    gross_issuance_difference = (
                        issuance_difference
                        * gross_factor
                    )
                    # -------------------------------------------------
                    # فقط صادرکننده current_agent
                    # -------------------------------------------------
                    if policy.issuer != current_agent:
                        continue
                    if not (
                        start_date
                        <= event["date"]
                        <= end_date
                    ):
                        continue
                    details.append({
                        "policy_id": policy.id,
                        "endorsement_number": (
                            policy.endorsement_number
                        ),
                        "date": policy.issue_date,
                        "collection": -remaining_negative,
                        "net_collection": -net_negative,
                        "issuance": issuance_difference,
                        "gross_issuance": (
                            gross_issuance_difference
                        ),
                    })
        # =========================================================
        # TOTALS
        # =========================================================
        total_issuance = sum(
            detail.get("issuance", 0)
            for detail in details
        )
        total_gross_issuance = sum(
            detail.get("gross_issuance", 0)
            for detail in details
        )
        return {
            "details": details,
            "total_issuance": round(total_issuance),
            "total_gross_issuance": round(total_gross_issuance),
        }
    finally:
        db.close()'''
def calculate_marketer_share_from_commission(
    policy,
    commission
):
    if not policy.marketer:
        return 0
    if commission == 0:
        return 0
    rule = find_best_commission_rule(
        policy.marketer.id,
        policy
    )
    if rule:
        commission_percent = (
            rule.commission_percent
        )
    else:
        if policy.insurance_type.display_name == "شخص ثالث خودرو":
            commission_percent = (
                policy.marketer.third_party_commission
                or 0
            )
        else:
            commission_percent = (
                policy.marketer.other_commission
                or 0
            )
    return round(
        commission
        * commission_percent
        / 100
    )
