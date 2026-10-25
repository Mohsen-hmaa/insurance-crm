from bisect import bisect_right
from database import SessionLocal
from sqlalchemy.orm import joinedload
from services.commission_service import (
    calculate_marketer_share_from_commission,
    calculate_split_collection_commission,
    calculate_base_issuance,
    calculate_base_commission,
    calculate_collection_commission_amount,
    get_commission_config_by_date,
    get_insurance_type_commission_by_date,
    VAT_EXEMPT_TYPES,
)
from datetime import date
from decimal import Decimal
from models import (
    Policy,
    Collection,
    CommissionConfig,
    InsuranceTypeCommission,
)
from services.system_config_service import get_current_agent
# =========================================================
# محاسبه هزینه صدور تمام الحاقیه‌های یک issue_code
# مبنا: حق بیمه
# =========================================================
def calculate_issue_code_issuance_map(issue_code):
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
                Policy.endorsement_number.asc()
            )
            .all()
        )
        if not policies:
            return {}
        original_policy = policies[0]
        commission_config = get_commission_config_by_date(
            original_policy.issue_date
        )
        if not commission_config:
            return {
                policy.id: (0, 0)
                for policy in policies
            }
        insurance_type_commission = (
            get_insurance_type_commission_by_date(
                original_policy.insurance_type_id,
                original_policy.issue_date
            )
        )
        if not insurance_type_commission:
            return {
                policy.id: (0, 0)
                for policy in policies
            }
        issuance_percent = (
            insurance_type_commission.issuance_percent or 0
        )
        first_step_commission = (
            commission_config.first_step_commission or 0
        )
        issuance_map = {}
        cumulative_premium = Decimal("0")
        for policy in policies:
            premium = policy.premium or 0
            if premium == 0:
                issuance_map[policy.id] = (0, 0)
                continue
            vat_config = get_commission_config_by_date(
                policy.issue_date
            )
            vat = (
                vat_config.vat
                if vat_config
                else 0
            )
            vat_factor = (
                Decimal("1")
                + Decimal(str(vat))
            )
            if (
                policy.insurance_type
                and policy.insurance_type.display_name
                in VAT_EXEMPT_TYPES
            ):
                net_premium = premium
            else:
                if vat_factor:
                    net_premium = (
                        premium / vat_factor
                    )
                else:
                    net_premium = premium
            previous_cumulative = cumulative_premium
            cumulative_premium += net_premium
            previous_issuance = calculate_base_issuance(
                previous_cumulative,
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
                * vat_factor
            )
            issuance_map[policy.id] = (
                issuance_difference,
                gross_issuance_difference
            )
        return issuance_map
    finally:
        db.close()
# =========================================================
# گزارش کارمزد نمایندگی
# =========================================================
def get_agent_commission_report(
    basis,
    start_date,
    end_date,
    insurance_type_id=None,
    issue_code=None
):
    db = SessionLocal()
    try:
        current_agent = get_current_agent()
        # =====================================================
        # Policyها
        # =====================================================
        query = (
            db.query(Policy)
            .options(
                joinedload(Policy.customer),
                joinedload(Policy.insurance_type),
                joinedload(Policy.marketer),
            )
            .filter(
                Policy.issue_date <= end_date
            )
        )
        if insurance_type_id is not None:
            query = query.filter(
                Policy.insurance_type_id == insurance_type_id
            )
        if issue_code is not None:
            query = query.filter(
                Policy.issue_code == issue_code
            )
        policies = query.all()
        policies_by_id = {
            policy.id: policy
            for policy in policies
        }
        issue_codes = {
            policy.issue_code
            for policy in policies
            if policy.issue_code
        }
        # =====================================================
        # Collectionها
        # =====================================================
        collections = []
        if basis == "collection" and policies:
            policy_ids = [
                policy.id
                for policy in policies
            ]
            collections = (
                db.query(Collection)
                .filter(
                    Collection.policy_id.in_(policy_ids),
                    Collection.collection_date <= end_date
                )
                .all()
            )
        # =====================================================
        # هزینه صدور
        # =====================================================
        issuance_reports = (
            calculate_batch_issuance_reports(
                policies=policies,
                collections=collections,
                basis=basis,
                start_date=start_date,
                end_date=end_date,
                current_agent=current_agent
            )
        )
        # =====================================================
        # گزارش کمیسیون همه issue_codeها
        #
        # این تابع نباید Policy را بر اساس معرف فیلتر کند.
        # چون ممکن است Policy برای نمایندگی هزینه صدور داشته باشد.
        # =====================================================
        commission_reports = (
            calculate_batch_commission_reports(
                policies=policies,
                collections=collections,
                basis=basis,
                start_date=start_date,
                end_date=end_date
            )
        )
        # =====================================================
        # جمع مبالغ
        # =====================================================
        details = []
        total_premium = 0
        total_net_premium = 0
        total_collection = 0
        total_net_collection = 0
        total_commission = 0
        total_gross_commission = 0
        total_marketer_commission = 0
        total_net_issuance = 0
        total_gross_issuance = 0
        # =====================================================
        # Policyهایی که از طریق commission report وارد شده‌اند
        #
        # برای جلوگیری از ساخت ردیف تکراری
        # =====================================================
        commission_policy_ids = set()
        # =====================================================
        # پردازش جزئیات کارمزد
        # =====================================================
        for issue_code in issue_codes:
            report = commission_reports.get(
                issue_code,
                {}
            )
            issuance_map = issuance_reports.get(
                issue_code,
                {}
            )
            for detail in report.get(
                "details",
                []
            ):
                policy_id = detail["policy_id"]
                policy = policies_by_id.get(
                    policy_id
                )
                if not policy:
                    continue
                # =================================================
                # کارمزد فقط برای واحد معرف فعلی
                # =================================================
                if (
                    policy.referrer_work_unit
                    == current_agent
                ):
                    commission = (
                        detail["commission"]
                    )
                    gross_commission = (
                        detail["gross_commission"]
                    )
                    marketer_share = (
                        calculate_marketer_share_from_commission(
                            policy,
                            commission
                        )
                    )
                else:
                    commission = 0
                    gross_commission = 0
                    marketer_share = 0
                # =================================================
                # هزینه صدور
                #
                # در حالت collection:
                # issuance_map با collection_id کلیدگذاری شده
                # و باید از collection_id موجود در detail استفاده شود.
                # =================================================
                if basis == "collection":
                    collection_id = detail.get(
                        "collection_id"
                    )
                    if collection_id is not None:
                        issuance_data = (
                            issuance_map.get(
                                collection_id,
                                {}
                            )
                        )
                    else:
                        issuance_data = (
                            issuance_map.get(
                                policy_id,
                                {}
                            )
                        )
                else:
                    issuance_data = (
                        issuance_map.get(
                            policy_id,
                            {}
                        )
                    )
                net_issuance = issuance_data.get(
                    "net_issuance",
                    0
                )
                gross_issuance = issuance_data.get(
                    "gross_issuance",
                    0
                )
                # =================================================
                # مبلغ وصولی باید مستقیماً از Commission Detail
                # گرفته شود، نه از issuance_map
                # =================================================
                if basis == "collection":
                    collection_amount = detail.get(
                        "collection_amount",
                        0
                    )
                    net_collection = detail.get(
                        "net_collection_amount",
                        0
                    )
                else:
                    collection_amount = 0
                    net_collection = 0
                # =================================================
                # اگر نه کارمزد داریم و نه هزینه صدور،
                # نیازی به نمایش این ردیف نیست.
                #
                # نکته:
                # commission_policy_ids فقط بعد از این بررسی
                # اضافه می‌شود تا ردیف‌های صرفاً هزینه صدور
                # حذف نشوند.
                # =================================================
                if (
                    commission == 0
                    and gross_commission == 0
                    and net_issuance == 0
                    and gross_issuance == 0
                ):
                    continue
                commission_policy_ids.add(
                    policy_id
                )
                # =================================================
                # مشتری
                # =================================================
                customer_name = ""
                if policy.customer:
                    customer_name = (
                        f"{policy.customer.name or ''} "
                        f"{policy.customer.family or ''}"
                    ).strip()
                # =================================================
                # ساخت ردیف
                # =================================================
                row = {
                    **detail,
                    "policy_number":
                        policy.policy_number,
                    "insurance_type_name": (
                        policy.insurance_type.display_name
                        if policy.insurance_type
                        else ""
                    ),
                    "customer_name":
                        customer_name,
                    "commission":
                        commission,
                    "gross_commission":
                        gross_commission,
                    "marketer_commission":
                        marketer_share,
                    "collection":
                        collection_amount,
                    "net_collection":
                        net_collection,
                    "net_issuance":
                        net_issuance,
                    "gross_issuance":
                        gross_issuance,
                }
                details.append(row)
                # =================================================
                # جمع‌ها
                # =================================================
                total_premium += detail.get(
                    "premium",
                    0
                )
                total_net_premium += detail.get(
                    "net_premium",
                    0
                )
                total_collection += (
                    collection_amount
                )
                total_net_collection += (
                    net_collection
                )
                total_commission += (
                    commission
                )
                total_gross_commission += (
                    gross_commission
                )
                total_marketer_commission += (
                    marketer_share
                )
                total_net_issuance += (
                    net_issuance
                )
                total_gross_issuance += (
                    gross_issuance
                )
        # =====================================================
        # Policyهایی که فقط هزینه صدور دارند
        #
        # مثال:
        # 3916
        #
        # اگر واحد معرفش نمایندگی فعلی نباشد،
        # کارمزدش صفر می‌شود،
        # ولی اگر issuer نمایندگی فعلی باشد،
        # هزینه صدورش باید در گزارش بیاید.
        # =====================================================
        for issue_code in issue_codes:
            issuance_map = issuance_reports.get(
                issue_code,
                {}
            )
            for policy_id, issuance_data in (
                issuance_map.items()
            ):
                # =================================================
                # در حالت collection، ورودی‌هایی که collection_id
                # دارند مربوط به یک وصول مشخص هستند، نه Policy.
                #
                # اینها قبلاً در حلقه commission details پردازش
                # شده‌اند و نباید دوباره اینجا به عنوان policy
                # پردازش شوند.
                # =================================================
                if (
                    basis == "collection"
                    and issuance_data.get(
                        "collection_id"
                    ) is not None
                ):
                    continue
                policy = policies_by_id.get(
                    policy_id
                )
                if not policy:
                    continue
                net_issuance = issuance_data.get(
                    "net_issuance",
                    0
                )
                gross_issuance = issuance_data.get(
                    "gross_issuance",
                    0
                )
                collection_amount = issuance_data.get(
                    "collection",
                    0
                )
                net_collection = issuance_data.get(
                    "net_collection",
                    0
                )
                # =================================================
                # اگر قبلاً همین Policy از طریق commission
                # دارای ردیف شده، ردیف جداگانه نساز.
                #
                # چون ممکن است همان Policy هم کارمزد داشته
                # و هم هزینه صدور.
                # =================================================
                if policy_id in commission_policy_ids:
                    continue
                # =================================================
                # اگر هیچ هزینه صدوری وجود ندارد، ردیف نساز.
                # =================================================
                if (
                    net_issuance == 0
                    and gross_issuance == 0
                    and collection_amount == 0
                    and net_collection == 0
                ):
                    continue
                customer_name = ""
                if policy.customer:
                    customer_name = (
                        f"{policy.customer.name or ''} "
                        f"{policy.customer.family or ''}"
                    ).strip()
                # =================================================
                # ساخت ردیف Policy فقط با هزینه صدور
                # =================================================
                row = {
                    "policy_id":
                        policy.id,
                    "policy_number":
                        policy.policy_number,
                    "insurance_type_name": (
                        policy.insurance_type.display_name
                        if policy.insurance_type
                        else ""
                    ),
                    "endorsement_number":
                        policy.endorsement_number,
                    "date":
                        policy.issue_date,
                    "premium":
                        policy.premium or 0,
                    "net_premium":
                        0,
                    "commission_percent":
                        0,
                    "commission":
                        0,
                    "gross_commission":
                        0,
                    "customer_name":
                        customer_name,
                    "marketer_commission":
                        0,
                    "collection":
                        collection_amount,
                    "net_collection":
                        net_collection,
                    "net_issuance":
                        net_issuance,
                    "gross_issuance":
                        gross_issuance,
                }
                details.append(row)
                # =================================================
                # جمع‌ها
                # =================================================
                total_premium += (
                    policy.premium or 0
                )
                total_collection += (
                    collection_amount
                )
                total_net_collection += (
                    net_collection
                )
                total_net_issuance += (
                    net_issuance
                )
                total_gross_issuance += (
                    gross_issuance
                )
        # =====================================================
        # مرتب‌سازی نهایی
        # =====================================================
        details.sort(
            key=lambda item: (
                item.get("date") or 0,
                item.get("policy_id") or 0
            )
        )
        # =====================================================
        # خروجی نهایی
        # =====================================================
        return {
            "details":
                details,
            "total_premium":
                total_premium,
            "total_net_premium":
                total_net_premium,
            "total_collection":
                round(
                    total_collection
                ),
            "total_net_collection":
                round(
                    total_net_collection
                ),
            "total_commission":
                round(
                    total_commission
                ),
            "total_gross_commission":
                round(
                    total_gross_commission
                ),
            "total_marketer_commission":
                round(
                    total_marketer_commission
                ),
            "total_net_issuance":
                round(
                    total_net_issuance
                ),
            "total_gross_issuance":
                round(
                    total_gross_issuance
                ),
        }
    finally:
        db.close()
# =========================================================
# گزارش هزینه صدور به صورت Batch
# =========================================================
def calculate_batch_issuance_reports(
    policies,
    collections,
    basis,
    start_date,
    end_date,
    current_agent
):
    if basis not in {"premium", "collection"}:
        raise ValueError(
            "basis must be 'premium' or 'collection'"
        )
    if not policies:
        return {}
    # =========================================================
    # فقط Policyهای تا پایان بازه
    # =========================================================
    policies = [
        policy
        for policy in policies
        if policy.issue_date
        and policy.issue_date <= end_date
    ]
    if not policies:
        return {}
    # =========================================================
    # گروه‌بندی Policyها بر اساس issue_code
    # =========================================================
    policies_by_issue_code = {}
    for policy in policies:
        issue_code = policy.issue_code
        if not issue_code:
            continue
        policies_by_issue_code.setdefault(
            issue_code,
            []
        ).append(policy)
    # =========================================================
    # مرتب‌سازی Policyها
    # =========================================================
    for issue_policies in policies_by_issue_code.values():
        issue_policies.sort(
            key=lambda policy: (
                policy.endorsement_number or 0,
                policy.id
            )
        )
    # =========================================================
    # Collectionها بر اساس policy_id
    # =========================================================
    collections_by_policy_id = {}
    if basis == "collection":
        for collection in collections:
            if not collection.policy_id:
                continue
            collection_date = (
                collection.collection_date
            )
            if not collection_date:
                continue
            if collection_date > end_date:
                continue
            collections_by_policy_id.setdefault(
                collection.policy_id,
                []
            ).append(collection)
        for policy_collections in (
            collections_by_policy_id.values()
        ):
            policy_collections.sort(
                key=lambda collection: (
                    collection.collection_date,
                    collection.id
                )
            )
    # =========================================================
    # خواندن Configها یک بار
    # =========================================================
    db = SessionLocal()
    try:
        commission_configs = (
            db.query(CommissionConfig)
            .order_by(
                CommissionConfig.effective_date.asc()
            )
            .all()
        )
        insurance_type_commissions = (
            db.query(InsuranceTypeCommission)
            .order_by(
                InsuranceTypeCommission.insurance_type_id.asc(),
                InsuranceTypeCommission.effective_date.asc()
            )
            .all()
        )
    finally:
        db.close()
    # =========================================================
    # Configها به شکل مناسب برای bisect
    # =========================================================
    config_dates = [
        config.effective_date
        for config in commission_configs
    ]
    # =========================================================
    # InsuranceTypeCommissionها
    # =========================================================
    type_commission_dates = {}
    type_commission_values = {}
    for item in insurance_type_commissions:
        insurance_type_id = (
            item.insurance_type_id
        )
        type_commission_dates.setdefault(
            insurance_type_id,
            []
        ).append(
            item.effective_date
        )
        type_commission_values.setdefault(
            insurance_type_id,
            []
        ).append(
            item
        )
    # =========================================================
    # Cache تنظیمات تاریخ
    # =========================================================
    config_cache = {}
    def get_config(issue_date):
        cached = config_cache.get(issue_date)
        if cached is not None:
            return cached
        if not commission_configs:
            config_cache[issue_date] = None
            return None
        index = (
            bisect_right(
                config_dates,
                issue_date
            )
            - 1
        )
        if index < 0:
            config = None
        else:
            config = commission_configs[index]
        config_cache[issue_date] = config
        return config
    # =========================================================
    # Cache تنظیمات رشته
    # =========================================================
    type_commission_cache = {}
    def get_type_commission(
        insurance_type_id,
        issue_date
    ):
        key = (
            insurance_type_id,
            issue_date
        )
        cached = type_commission_cache.get(key)
        if cached is not None:
            return cached
        dates = type_commission_dates.get(
            insurance_type_id
        )
        values = type_commission_values.get(
            insurance_type_id
        )
        if not dates:
            type_commission_cache[key] = None
            return None
        index = (
            bisect_right(
                dates,
                issue_date
            )
            - 1
        )
        if index < 0:
            item = None
        else:
            item = values[index]
        type_commission_cache[key] = item
        return item
    result = {}
    # =========================================================
    # پردازش issue_codeها
    # =========================================================
    for issue_code, issue_policies in (
        policies_by_issue_code.items()
    ):
        if not issue_policies:
            continue
        original_policy = issue_policies[0]
        # =====================================================
        # نسبت صندوق بیمه‌نامه اصلی
        # =====================================================
        fund_ratio = Decimal("0")
        if (
            original_policy.insurance_type
            and
            "شخص ثالث خودرو"
            in original_policy.insurance_type.display_name
        ):
            original_premium = (
                original_policy.premium or 0
            )
            original_fund = (
                original_policy.fund or 0
            )
            fund_ratio = Decimal("0")
            if original_premium:
                fund_ratio = (
                    Decimal(str(original_fund))
                    / Decimal(str(original_premium))
                )
        # =====================================================
        # تنظیمات اصلی issue_code
        # =====================================================
        original_config = get_config(
            original_policy.issue_date
        )
        if not original_config:
            result[issue_code] = {}
            continue
        insurance_type_commission = (
            get_type_commission(
                original_policy.insurance_type_id,
                original_policy.issue_date
            )
        )
        if not insurance_type_commission:
            result[issue_code] = {}
            continue
        issuance_percent = (
            insurance_type_commission.issuance_percent
            or 0
        )
        first_step_commission = (
            original_config.first_step_commission
            or 0
        )
        # =====================================================
        # PREMIUM BASIS
        # =====================================================
        if basis == "premium":
            issuance_map = {}
            cumulative_net_premium = 0
            previous_issuance = Decimal("0")
            calculate_issuance = (
                calculate_base_issuance
            )
            for policy in issue_policies:
                premium = policy.premium or 0
                if premium == 0:
                    if policy.issuer == current_agent:
                        issuance_map.setdefault(
                            policy.id,
                            {
                                "net_issuance": 0,
                                "gross_issuance": 0,
                            }
                        )
                    continue
                # -------------------------------------------------
                # VAT تاریخ خود Policy
                # -------------------------------------------------
                vat_config = get_config(
                    policy.issue_date
                )
                if not vat_config:
                    continue
                vat = vat_config.vat or 0
                vat_factor = (
                    Decimal("1")
                    + Decimal(str(vat))
                )
                insurance_type = (
                    policy.insurance_type
                )
                is_exempt = (
                    insurance_type
                    and
                    insurance_type.display_name
                    in VAT_EXEMPT_TYPES
                )
                # -------------------------------------------------
                # کسر صندوق
                # -------------------------------------------------
                commissionable_premium = (
                    premium
                    * (1 - fund_ratio)
                )
                if is_exempt:
                    net_premium = (
                        commissionable_premium
                    )
                    gross_factor = 1
                else:
                    gross_factor = vat_factor
                    net_premium = (
                        commissionable_premium
                        / gross_factor
                        if gross_factor
                        else commissionable_premium
                    )
                # -------------------------------------------------
                # تجمعی
                # -------------------------------------------------
                cumulative_net_premium += (
                    net_premium
                )
                current_issuance = (
                    calculate_issuance(
                        cumulative_net_premium,
                        issuance_percent,
                        first_step_commission
                    )
                )
                issuance_difference = (
                    current_issuance
                    - previous_issuance
                )
                previous_issuance = (
                    current_issuance
                )
                gross_issuance_difference = (
                    issuance_difference
                    * vat_factor
                )
                # -------------------------------------------------
                # فقط issuer فعلی و تاریخ داخل گزارش
                # -------------------------------------------------
                if policy.issuer != current_agent:
                    continue
                if not (
                    start_date
                    <= policy.issue_date
                    <= end_date
                ):
                    continue
                issuance_map[policy.id] = {
                    "net_issuance":
                        issuance_difference,
                    "gross_issuance":
                        gross_issuance_difference,
                }
            result[issue_code] = issuance_map
        # =====================================================
        # COLLECTION BASIS
        # =====================================================
        else:
            events = []
            append_event = events.append
            for policy in issue_policies:
                vat_config = get_config(
                    policy.issue_date
                )
                if not vat_config:
                    continue
                vat = vat_config.vat or 0
                vat_factor = (
                    Decimal("1")
                    + Decimal(str(vat))
                )
                insurance_type = (
                    policy.insurance_type
                )
                is_exempt = (
                    insurance_type
                    and
                    insurance_type.display_name
                    in VAT_EXEMPT_TYPES
                )
                if is_exempt:
                    gross_factor = 1
                else:
                    gross_factor = vat_factor
                premium = policy.premium or 0
                # -------------------------------------------------
                # Premium
                # -------------------------------------------------
                if premium > 0:
                    append_event((
                        policy.issue_date,
                        0,
                        policy.id,
                        "premium",
                        policy,
                        premium,
                        vat_factor,
                        gross_factor,
                    ))
                # -------------------------------------------------
                # Negative endorsement
                # -------------------------------------------------
                elif premium < 0:
                    append_event((
                        policy.issue_date,
                        2,
                        policy.id,
                        "negative",
                        policy,
                        abs(premium),
                        vat_factor,
                        gross_factor,
                    ))
                # -------------------------------------------------
                # Collections
                # -------------------------------------------------
                policy_collections = (
                    collections_by_policy_id.get(
                        policy.id,
                        ()
                    )
                )
                for collection in policy_collections:
                    amount = Decimal(str(
                        collection.settlement_amount
                        or 0
                    ))
                    if amount <= 0:
                        continue
                    append_event((
                        collection.collection_date,
                        1,
                        collection.id,
                        "collection",
                        policy,
                        amount,
                        vat_factor,
                        gross_factor,
                        collection,
                    ))
            # -------------------------------------------------
            # sort
            # -------------------------------------------------
            events.sort(
                key=lambda event: (
                    event[0],
                    event[1],
                    event[2]
                )
            )
            issuance_map = {}
            cumulative_net_collection = 0
            outstanding_gross = 0
            calculate_issuance = (
                calculate_base_issuance
            )
            calculate_local_issuance = (
                calculate_issuance
            )
            # =================================================
            # پردازش eventها
            # =================================================
            for event in events:
                # event مربوط به collection یک عضو اضافه دارد
                if event[3] == "collection":
                    (
                        event_date,
                        event_order,
                        event_id,
                        event_type,
                        policy,
                        amount,
                        vat_factor,
                        gross_factor,
                        collection,
                    ) = event
                else:
                    (
                        event_date,
                        event_order,
                        event_id,
                        event_type,
                        policy,
                        amount,
                        vat_factor,
                        gross_factor,
                    ) = event
                    collection = None
                # -------------------------------------------------
                # Premium
                # -------------------------------------------------
                if event_type == "premium":
                    outstanding_gross += amount
                    continue
                # -------------------------------------------------
                # Collection
                # -------------------------------------------------
                if event_type == "collection":
                    # =================================================
                    # مهم:
                    # برای محاسبه هزینه صدور، کل مبلغ همین وصول
                    # وارد محاسبات می‌شود.
                    # =================================================
                    effective_gross = amount
                    if effective_gross <= 0:
                        continue
                    # -------------------------------------------------
                    # outstanding_gross
                    # برای منطق برگشتی نگه داشته می‌شود
                    # -------------------------------------------------
                    outstanding_gross = max(
                        outstanding_gross
                        - effective_gross,
                        0
                    )
                    # -------------------------------------------------
                    # کسر صندوق
                    # -------------------------------------------------
                    commissionable_collection = (
                        effective_gross
                        * (1 - fund_ratio)
                    )
                    if (
                        policy.insurance_type
                        and
                        policy.insurance_type.display_name
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
                    # =================================================
                    # محاسبه تجمعی هزینه صدور
                    # =================================================
                    previous_collection = (
                        cumulative_net_collection
                    )
                    previous_issuance = (
                        calculate_local_issuance(
                            previous_collection,
                            issuance_percent,
                            first_step_commission
                        )
                    )
                    cumulative_net_collection += (
                        net_collection
                    )
                    current_issuance = (
                        calculate_local_issuance(
                            cumulative_net_collection,
                            issuance_percent,
                            first_step_commission
                        )
                    )
                    issuance_difference = (
                        current_issuance
                        - previous_issuance
                    )
                    gross_issuance_difference = (
                        issuance_difference
                        * vat_factor
                    )
                    # -------------------------------------------------
                    # فقط issuer فعلی
                    # -------------------------------------------------
                    if policy.issuer != current_agent:
                        continue
                    if not (
                        start_date
                        <= event_date
                        <= end_date
                    ):
                        continue
                    # =================================================
                    # هر وصول با collection.id ذخیره می‌شود
                    # =================================================
                    issuance_map[collection.id] = {
                        "policy_id":
                            policy.id,
                        "collection_id":
                            collection.id,
                        "collection":
                            effective_gross,
                        "net_collection":
                            net_collection,
                        "net_issuance":
                            issuance_difference,
                        "gross_issuance":
                            gross_issuance_difference,
                    }
                    continue
                # -------------------------------------------------
                # Negative endorsement
                # -------------------------------------------------
                if event_type == "negative":
                    negative_gross = amount
                    unpaid_offset = min(
                        negative_gross,
                        outstanding_gross
                    )
                    outstanding_gross -= (
                        unpaid_offset
                    )
                    remaining_negative = (
                        negative_gross
                        - unpaid_offset
                    )
                    if remaining_negative <= 0:
                        continue
                    # -------------------------------------------------
                    # کسر صندوق از مبلغ برگشتی
                    # -------------------------------------------------
                    commissionable_negative = (
                        remaining_negative
                        * (1 - fund_ratio)
                    )
                    if (
                        policy.insurance_type
                        and
                        policy.insurance_type.display_name
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
                    # =================================================
                    # قبل از کاهش cumulative،
                    # هزینه صدور مربوط به وضعیت قبلی را محاسبه می‌کنیم.
                    # =================================================
                    previous_collection = (
                        cumulative_net_collection
                    )
                    previous_issuance = (
                        calculate_local_issuance(
                            previous_collection,
                            issuance_percent,
                            first_step_commission
                        )
                    )
                    # -------------------------------------------------
                    # کاهش cumulative
                    # -------------------------------------------------
                    cumulative_net_collection -= (
                        net_negative
                    )
                    if cumulative_net_collection < 0:
                        cumulative_net_collection = 0
                    # =================================================
                    # هزینه صدور بعد از برگشتی
                    # =================================================
                    current_issuance = (
                        calculate_local_issuance(
                            cumulative_net_collection,
                            issuance_percent,
                            first_step_commission
                        )
                    )
                    issuance_difference = (
                        current_issuance
                        - previous_issuance
                    )
                    gross_issuance_difference = (
                        issuance_difference
                        * vat_factor
                    )
                    # -------------------------------------------------
                    # فقط issuer فعلی
                    # -------------------------------------------------
                    if policy.issuer != current_agent:
                        continue
                    if not (
                        start_date
                        <= event_date
                        <= end_date
                    ):
                        continue
                    # -------------------------------------------------
                    # برگشتی policy-level نگه داشته می‌شود
                    # چون collection_id ندارد
                    # -------------------------------------------------
                    data = issuance_map.get(
                        policy.id
                    )
                    if data is None:
                        data = {
                            "policy_id":
                                policy.id,
                            "collection":
                                0,
                            "net_collection":
                                0,
                            "net_issuance":
                                0,
                            "gross_issuance":
                                0,
                        }
                        issuance_map[
                            policy.id
                        ] = data
                    data["collection"] -= (
                        remaining_negative
                    )
                    data["net_collection"] -= (
                        net_negative
                    )
                    data["net_issuance"] += (
                        issuance_difference
                    )
                    data["gross_issuance"] += (
                        gross_issuance_difference
                    )
            result[issue_code] = issuance_map
    return result
# =========================================================
# گزارش کمیسیون به صورت Batch
# =========================================================
def calculate_batch_commission_reports(
    policies,
    collections,
    basis,
    start_date,
    end_date
):
    if basis not in {"premium", "collection"}:
        raise ValueError(
            "basis must be 'premium' or 'collection'"
        )
    if not policies:
        return {}
    # =========================================================
    # گروه‌بندی Policyها بر اساس issue_code
    # =========================================================
    policies_by_issue_code = {}
    for policy in policies:
        if not policy.issue_code:
            continue
        policies_by_issue_code.setdefault(
            policy.issue_code,
            []
        ).append(policy)
    for issue_code in policies_by_issue_code:
        policies_by_issue_code[issue_code].sort(
            key=lambda policy: (
                policy.endorsement_number or 0,
                policy.id
            )
        )
    # =========================================================
    # گروه‌بندی Collectionها بر اساس policy_id
    # =========================================================
    collections_by_policy_id = {}
    for collection in collections:
        if not collection.policy_id:
            continue
        if not collection.collection_date:
            continue
        if collection.collection_date > end_date:
            continue
        collections_by_policy_id.setdefault(
            collection.policy_id,
            []
        ).append(collection)
    for policy_id in collections_by_policy_id:
        collections_by_policy_id[policy_id].sort(
            key=lambda collection: (
                collection.collection_date,
                collection.id
            )
        )
    # =========================================================
    # Preload تنظیمات
    # =========================================================
    db = SessionLocal()
    try:
        commission_configs = (
            db.query(CommissionConfig)
            .order_by(
                CommissionConfig.effective_date.asc()
            )
            .all()
        )
        insurance_type_commissions = (
            db.query(InsuranceTypeCommission)
            .order_by(
                InsuranceTypeCommission.insurance_type_id.asc(),
                InsuranceTypeCommission.effective_date.asc()
            )
            .all()
        )
    finally:
        db.close()
    # =========================================================
    # Cache برای CommissionConfig
    # =========================================================
    commission_config_cache = {}
    def get_config(issue_date):
        if issue_date in commission_config_cache:
            return commission_config_cache[issue_date]
        selected = None
        for config in commission_configs:
            if config.effective_date <= issue_date:
                selected = config
            else:
                break
        commission_config_cache[issue_date] = selected
        return selected
    # =========================================================
    # Cache برای InsuranceTypeCommission
    # =========================================================
    insurance_type_commission_cache = {}
    def get_type_commission(
        insurance_type_id,
        issue_date
    ):
        key = (
            insurance_type_id,
            issue_date
        )
        if key in insurance_type_commission_cache:
            return insurance_type_commission_cache[key]
        selected = None
        for item in insurance_type_commissions:
            if (
                item.insurance_type_id
                != insurance_type_id
            ):
                continue
            if item.effective_date <= issue_date:
                selected = item
            else:
                break
        insurance_type_commission_cache[key] = selected
        return selected
    # =========================================================
    # محاسبه مبلغ خالص با VAT و صندوق
    # =========================================================
    def calculate_net_amount(
        amount,
        policy,
        fund_ratio
    ):
        amount = Decimal(str(amount or 0))
        config = get_config(policy.issue_date)
        if not config:
            return None, None
        vat_factor = (
            Decimal("1")
            + Decimal(str(config.vat))
        )
        insurance_type = policy.insurance_type
        is_vat_exempt = (
            insurance_type
            and insurance_type.display_name
            in VAT_EXEMPT_TYPES
        )
        commissionable_amount = (
            amount
            * (
                Decimal("1")
                - fund_ratio
            )
        )
        if is_vat_exempt:
            net_amount = commissionable_amount
        else:
            net_amount = (
                commissionable_amount
                / vat_factor
            )
        return net_amount, vat_factor
    # =========================================================
    # محاسبه کمیسیون یک Event با split Normal / Mortgage
    #
    # Tier فقط بر اساس total_amount است.
    # =========================================================
    def calculate_split_event_commission(
        event_total,
        event_mortgage,
        cumulative_before,
        cumulative_after,
        normal_rate,
        mortgage_rate,
        first_step_commission
    ):
        event_total = Decimal(
            str(event_total or 0)
        )
        event_mortgage = Decimal(
            str(event_mortgage or 0)
        )
        cumulative_before = Decimal(
            str(cumulative_before or 0)
        )
        cumulative_after = Decimal(
            str(cumulative_after or 0)
        )
        normal_rate = Decimal(
            str(normal_rate or 0)
        )
        mortgage_rate = Decimal(
            str(mortgage_rate or 0)
        )
        first_step_commission = Decimal(
            str(first_step_commission or 0)
        )
        event_normal = (
            event_total
            - event_mortgage
        )
        # -----------------------------------------------------
        # مبلغ Event صفر است.
        # -----------------------------------------------------
        if event_total == 0:
            return (
                event_normal
                * normal_rate
                / Decimal("100")
                +
                event_mortgage
                * mortgage_rate
                / Decimal("100")
            )
        # -----------------------------------------------------
        # محاسبه مقدار پلکان روی کل مبلغ
        # -----------------------------------------------------
        previous_tier = calculate_base_commission(
            cumulative_before,
            Decimal("100"),
            first_step_commission
        )
        current_tier = calculate_base_commission(
            cumulative_after,
            Decimal("100"),
            first_step_commission
        )
        tier_increment = (
            current_tier
            - previous_tier
        )
        tier_factor = (
            tier_increment
            / event_total
        )
        commission = (
            event_normal
            * normal_rate
            / Decimal("100")
            * tier_factor
            +
            event_mortgage
            * mortgage_rate
            / Decimal("100")
            * tier_factor
        )
        return commission
    result = {}
    # =========================================================
    # پردازش هر issue_code
    # =========================================================
    for issue_code, issue_policies in (
        policies_by_issue_code.items()
    ):
        if not issue_policies:
            continue
        details = []
        total_commission = Decimal("0")
        total_gross_commission = Decimal("0")
        # =====================================================
        # PREMIUM BASIS
        # =====================================================
        if basis == "premium":
            cumulative_premium = Decimal("0")
            cumulative_mortgage = Decimal("0")
            for policy in issue_policies:
                premium = Decimal(
                    str(policy.premium or 0)
                )
                mortgage_premium = Decimal(
                    str(
                        policy.mortgage_premium
                        or 0
                    )
                )
                # -------------------------------------------------
                # نرخ همان Policy
                # -------------------------------------------------
                type_commission = (
                    get_type_commission(
                        policy.insurance_type_id,
                        policy.issue_date
                    )
                )
                if not type_commission:
                    continue
                normal_rate = Decimal(
                    str(
                        type_commission.normal_commission
                        or 0
                    )
                )
                mortgage_rate = Decimal(
                    str(
                        type_commission.mortgage_commission
                        or 0
                    )
                )
                config = get_config(
                    policy.issue_date
                )
                if not config:
                    continue
                first_step_commission = Decimal(
                    str(
                        config.first_step_commission
                    )
                )
                # -------------------------------------------------
                # Fund
                # -------------------------------------------------
                fund_ratio = Decimal("0")
                if (
                    policy.insurance_type
                    and
                    "شخص ثالث"
                    in policy.insurance_type.display_name
                ):
                    original_premium = Decimal(
                        str(
                            policy.premium
                            or 0
                        )
                    )
                    original_fund = Decimal(
                        str(
                            policy.fund
                            or 0
                        )
                    )
                    if original_premium != 0:
                        fund_ratio = (
                            original_fund
                            / original_premium
                        )
                # -------------------------------------------------
                # premium صفر
                # -------------------------------------------------
                if premium == 0:
                    net_mortgage, gross_factor = (
                        calculate_net_amount(
                            mortgage_premium,
                            policy,
                            fund_ratio
                        )
                    )
                    if net_mortgage is None:
                        continue
                    net_normal = (
                        -net_mortgage
                    )
                    commission = (
                        net_normal
                        * normal_rate
                        / Decimal("100")
                        +
                        net_mortgage
                        * mortgage_rate
                        / Decimal("100")
                    )
                    gross_commission = (
                        commission
                        * gross_factor
                    )
                    if (
                        start_date
                        <= policy.issue_date
                        <= end_date
                    ):
                        details.append({
                            "policy_id":
                                policy.id,
                            "endorsement_number":
                                policy.endorsement_number,
                            "date":
                                policy.issue_date,
                            "premium":
                                0,
                            "net_premium":
                                0,
                            "commission_percent":
                                None,
                            "normal_commission_percent":
                                normal_rate,
                            "mortgage_commission_percent":
                                mortgage_rate,
                            "commission":
                                round(commission),
                            "gross_commission":
                                round(
                                    gross_commission
                                ),
                        })
                        total_commission += (
                            round(commission)
                        )
                        total_gross_commission += (
                            round(
                                gross_commission
                            )
                        )
                    continue
                # -------------------------------------------------
                # مبلغ عادی و مرهوناتی Policy
                # -------------------------------------------------
                net_premium, gross_factor = (
                    calculate_net_amount(
                        premium,
                        policy,
                        fund_ratio
                    )
                )
                if net_premium is None:
                    continue
                # mortgage_premium در DB شامل VAT است.
                net_mortgage, _ = (
                    calculate_net_amount(
                        mortgage_premium,
                        policy,
                        fund_ratio
                    )
                )
                if net_mortgage is None:
                    continue
                # -------------------------------------------------
                # برای endorsement منفی
                # mortgage_premium در DB مثبت است
                # ولی سهم آن در premium منفی است.
                # -------------------------------------------------
                if premium < 0:
                    net_mortgage = (
                        -abs(net_mortgage)
                    )
                    net_normal = (
                        net_premium
                        - net_mortgage
                    )
                else:
                    if premium != 0:
                        net_mortgage = min(
                            net_mortgage,
                            net_premium
                        )
                    net_normal = (
                        net_premium
                        - net_mortgage
                    )
                # -------------------------------------------------
                # cumulative قبل و بعد
                # -------------------------------------------------
                cumulative_before = (
                    cumulative_premium
                )
                mortgage_before = (
                    cumulative_mortgage
                )
                cumulative_after = (
                    cumulative_before
                    + net_premium
                )
                mortgage_after = (
                    mortgage_before
                    + net_mortgage
                )
                # -------------------------------------------------
                # tier بر اساس total premium
                #
                # برای allocation واقعی Event،
                # فقط سهم همین Event را استفاده می‌کنیم.
                # -------------------------------------------------
                commission = (
                    calculate_split_event_commission(
                        net_premium,
                        net_mortgage,
                        cumulative_before,
                        cumulative_after,
                        normal_rate,
                        mortgage_rate,
                        first_step_commission
                    )
                )
                gross_commission = (
                    commission
                    * gross_factor
                )
                cumulative_premium = (
                    cumulative_after
                )
                cumulative_mortgage = (
                    mortgage_after
                )
                if not (
                    start_date
                    <= policy.issue_date
                    <= end_date
                ):
                    continue
                details.append({
                    "policy_id":
                        policy.id,
                    "endorsement_number":
                        policy.endorsement_number,
                    "date":
                        policy.issue_date,
                    "premium":
                        round(premium),
                    "net_premium":
                        round(net_premium),
                    "commission_percent":
                        None,
                    "normal_commission_percent":
                        normal_rate,
                    "mortgage_commission_percent":
                        mortgage_rate,
                    "commission":
                        round(commission),
                    "gross_commission":
                        round(gross_commission),
                })
                total_commission += (
                    round(commission)
                )
                total_gross_commission += (
                    round(gross_commission)
                )
        # =========================================================
        # COLLECTION BASIS
        # =========================================================
        else:
            events = []
            # -----------------------------------------------------
            # ساخت Eventها
            # -----------------------------------------------------
            for policy in issue_policies:
                premium = Decimal(
                    str(policy.premium or 0)
                )
                config = get_config(
                    policy.issue_date
                )
                if not config:
                    continue
                vat_factor = (
                    Decimal("1")
                    + Decimal(str(config.vat))
                )
                insurance_type = (
                    policy.insurance_type
                )
                is_vat_exempt = (
                    insurance_type
                    and insurance_type.display_name
                    in VAT_EXEMPT_TYPES
                )
                gross_factor = (
                    Decimal("1")
                    if is_vat_exempt
                    else vat_factor
                )
                # ---------------------------------------------
                # Premium
                # ---------------------------------------------
                if premium > 0:
                    events.append({
                        "event_type":
                            "premium",
                        "date":
                            policy.issue_date,
                        "id":
                            policy.id,
                        "policy":
                            policy,
                        "amount":
                            premium,
                        "gross_factor":
                            gross_factor,
                    })
                # ---------------------------------------------
                # premium صفر
                # ---------------------------------------------
                elif premium == 0:
                    events.append({
                        "event_type":
                            "zero_premium",
                        "date":
                            policy.issue_date,
                        "id":
                            policy.id,
                        "policy":
                            policy,
                        "amount":
                            Decimal("0"),
                        "gross_factor":
                            gross_factor,
                    })
                # ---------------------------------------------
                # Negative endorsement
                # ---------------------------------------------
                elif premium < 0:
                    events.append({
                        "event_type":
                            "negative_endorsement",
                        "date":
                            policy.issue_date,
                        "id":
                            policy.id,
                        "policy":
                            policy,
                        "amount":
                            abs(premium),
                        "gross_factor":
                            gross_factor,
                    })
                # ---------------------------------------------
                # Collection
                # ---------------------------------------------
                for collection in (
                    collections_by_policy_id.get(
                        policy.id,
                        []
                    )
                ):
                    amount = Decimal(
                        str(
                            collection.settlement_amount
                            or 0
                        )
                    )
                    if amount <= 0:
                        continue
                    events.append({
                        "event_type":
                            "collection",
                        "date":
                            collection.collection_date,
                        "id":
                            collection.id,
                        "policy":
                            policy,
                        "collection":
                            collection,
                        "amount":
                            amount,
                        "gross_factor":
                            gross_factor,
                    })
            # -----------------------------------------------------
            # ترتیب رویدادها
            # -----------------------------------------------------
            event_order = {
                "premium": 0,
                "collection": 1,
                "zero_premium": 2,
                "negative_endorsement": 2,
            }
            events.sort(
                key=lambda event: (
                    event["date"],
                    event_order[
                        event["event_type"]
                    ],
                    event["id"]
                )
            )
            # -----------------------------------------------------
            # وضعیت تجمعی
            # -----------------------------------------------------
            cumulative_collection = Decimal("0")
            cumulative_mortgage_collection = Decimal("0")
            outstanding_gross = Decimal("0")
            # -----------------------------------------------------
            # پردازش Eventها
            # -----------------------------------------------------
            for event in events:
                event_type = (
                    event["event_type"]
                )
                policy = event["policy"]
                amount = Decimal(
                    str(event["amount"] or 0)
                )
                gross_factor = (
                    event["gross_factor"]
                )
                # =================================================
                # PREMIUM
                # =================================================
                if event_type == "premium":
                    outstanding_gross += amount
                    continue
                # =================================================
                # ZERO PREMIUM
                # =================================================
                if event_type == "zero_premium":
                    type_commission = (
                        get_type_commission(
                            policy.insurance_type_id,
                            policy.issue_date
                        )
                    )
                    if not type_commission:
                        continue
                    config = get_config(
                        policy.issue_date
                    )
                    if not config:
                        continue
                    normal_rate = Decimal(
                        str(
                            type_commission.normal_commission
                            or 0
                        )
                    )
                    mortgage_rate = Decimal(
                        str(
                            type_commission.mortgage_commission
                            or 0
                        )
                    )
                    mortgage_premium = Decimal(
                        str(
                            policy.mortgage_premium
                            or 0
                        )
                    )
                    fund_ratio = Decimal("0")
                    if (
                        policy.insurance_type
                        and
                        "شخص ثالث"
                        in policy.insurance_type.display_name
                    ):
                        policy_premium = Decimal(
                            str(
                                policy.premium
                                or 0
                            )
                        )
                        policy_fund = Decimal(
                            str(
                                policy.fund
                                or 0
                            )
                        )
                        if policy_premium != 0:
                            fund_ratio = (
                                policy_fund
                                / policy_premium
                            )
                    net_mortgage, zero_gross_factor = (
                        calculate_net_amount(
                            mortgage_premium,
                            policy,
                            fund_ratio
                        )
                    )
                    if net_mortgage is None:
                        continue
                    net_normal = (
                        -net_mortgage
                    )
                    commission = (
                        net_normal
                        * normal_rate
                        / Decimal("100")
                        +
                        net_mortgage
                        * mortgage_rate
                        / Decimal("100")
                    )
                    gross_commission = (
                        commission
                        * zero_gross_factor
                    )
                    if not (
                        start_date
                        <= event["date"]
                        <= end_date
                    ):
                        continue
                    details.append({
                        "policy_id":
                            policy.id,
                        "endorsement_number":
                            policy.endorsement_number,
                        "date":
                            event["date"],
                        "collection_amount":
                            0,
                        "net_collection_amount":
                            0,
                        "cumulative_net_collection":
                            round(
                                cumulative_collection
                            ),
                        "commission_percent":
                            None,
                        "normal_commission_percent":
                            normal_rate,
                        "mortgage_commission_percent":
                            mortgage_rate,
                        "commission":
                            round(commission),
                        "gross_commission":
                            round(
                                gross_commission
                            ),
                    })
                    total_commission += (
                        round(commission)
                    )
                    total_gross_commission += (
                        round(gross_commission)
                    )
                    continue
                # =================================================
                # COLLECTION
                # =================================================
                if event_type == "collection":
                    outstanding_gross = max(
                        outstanding_gross - amount,
                        Decimal("0")
                    )
                    config = get_config(
                        policy.issue_date
                    )
                    if not config:
                        continue
                    type_commission = (
                        get_type_commission(
                            policy.insurance_type_id,
                            policy.issue_date
                        )
                    )
                    if not type_commission:
                        continue
                    normal_rate = Decimal(
                        str(
                            type_commission.normal_commission
                            or 0
                        )
                    )
                    mortgage_rate = Decimal(
                        str(
                            type_commission.mortgage_commission
                            or 0
                        )
                    )
                    # -------------------------------------------------
                    # Fund ratio
                    # -------------------------------------------------
                    fund_ratio = Decimal("0")
                    if (
                        policy.insurance_type
                        and
                        "شخص ثالث"
                        in policy.insurance_type.display_name
                    ):
                        policy_premium = Decimal(
                            str(
                                policy.premium
                                or 0
                            )
                        )
                        policy_fund = Decimal(
                            str(
                                policy.fund
                                or 0
                            )
                        )
                        if policy_premium != 0:
                            fund_ratio = (
                                policy_fund
                                / policy_premium
                            )
                    # -------------------------------------------------
                    # مبلغ خالص وصولی
                    # -------------------------------------------------
                    net_amount, collection_gross_factor = (
                        calculate_net_amount(
                            amount,
                            policy,
                            fund_ratio
                        )
                    )
                    if net_amount is None:
                        continue
                    # -------------------------------------------------
                    # نسبت مرهوناتی فقط برای Policy با premium != 0
                    # -------------------------------------------------
                    policy_premium = Decimal(
                        str(
                            policy.premium
                            or 0
                        )
                    )
                    policy_mortgage = Decimal(
                        str(
                            policy.mortgage_premium
                            or 0
                        )
                    )
                    if policy_premium != 0:
                        mortgage_ratio = (
                            policy_mortgage
                            / policy_premium
                        )
                        mortgage_collection = (
                            net_amount
                            * mortgage_ratio
                        )
                    else:
                        mortgage_collection = (
                            Decimal("0")
                        )
                    normal_collection = (
                        net_amount
                        - mortgage_collection
                    )
                    cumulative_before = (
                        cumulative_collection
                    )
                    mortgage_before = (
                        cumulative_mortgage_collection
                    )
                    cumulative_after = (
                        cumulative_before
                        + net_amount
                    )
                    mortgage_after = (
                        mortgage_before
                        + mortgage_collection
                    )
                    commission = (
                        calculate_split_event_commission(
                            net_amount,
                            mortgage_collection,
                            cumulative_before,
                            cumulative_after,
                            normal_rate,
                            mortgage_rate,
                            Decimal(
                                str(
                                    config.first_step_commission
                                )
                            )
                        )
                    )
                    cumulative_collection = (
                        cumulative_after
                    )
                    cumulative_mortgage_collection = (
                        mortgage_after
                    )
                    gross_commission = (
                        commission
                        * collection_gross_factor
                    )
                    if not (
                        start_date
                        <= event["date"]
                        <= end_date
                    ):
                        continue
                    details.append({
                        "policy_id":
                            policy.id,
                        "collection_id":
                            event["collection"].id,
                        "endorsement_number":
                            policy.endorsement_number,
                        "date":
                            event["date"],
                        "collection_amount":
                            round(amount),
                        "net_collection_amount":
                            round(net_amount),
                        "cumulative_net_collection":
                            round(
                                cumulative_collection
                            ),
                        "commission_percent":
                            None,
                        "normal_commission_percent":
                            normal_rate,
                        "mortgage_commission_percent":
                            mortgage_rate,
                        "commission":
                            round(commission),
                        "gross_commission":
                            round(
                                gross_commission
                            ),
                    })
                    total_commission += (
                        round(commission)
                    )
                    total_gross_commission += (
                        round(gross_commission)
                    )
                    continue
                # =================================================
                # NEGATIVE ENDORSEMENT
                # =================================================
                if event_type == "negative_endorsement":
                    returned_amount_gross = (
                        amount
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
                    outstanding_gross = max(
                        outstanding_gross
                        - returned_amount_gross,
                        Decimal("0")
                    )
                    if effective_return_gross <= 0:
                        continue
                    config = get_config(
                        policy.issue_date
                    )
                    if not config:
                        continue
                    type_commission = (
                        get_type_commission(
                            policy.insurance_type_id,
                            policy.issue_date
                        )
                    )
                    if not type_commission:
                        continue
                    normal_rate = Decimal(
                        str(
                            type_commission.normal_commission
                            or 0
                        )
                    )
                    mortgage_rate = Decimal(
                        str(
                            type_commission.mortgage_commission
                            or 0
                        )
                    )
                    # -------------------------------------------------
                    # Fund
                    # -------------------------------------------------
                    fund_ratio = Decimal("0")
                    if (
                        policy.insurance_type
                        and
                        "شخص ثالث"
                        in policy.insurance_type.display_name
                    ):
                        original_premium = Decimal(
                            str(
                                policy.premium
                                or 0
                            )
                        )
                        original_fund = Decimal(
                            str(
                                policy.fund
                                or 0
                            )
                        )
                        if original_premium != 0:
                            fund_ratio = (
                                original_fund
                                / original_premium
                            )
                    effective_return_net, return_gross_factor = (
                        calculate_net_amount(
                            effective_return_gross,
                            policy,
                            fund_ratio
                        )
                    )
                    if effective_return_net is None:
                        continue
                    # -------------------------------------------------
                    # برگشتی روی cumulative اثر می‌گذارد
                    # -------------------------------------------------
                    cumulative_before = max(
                        cumulative_collection,
                        Decimal("0")
                    )
                    cumulative_after = max(
                        cumulative_before
                        - effective_return_net,
                        Decimal("0")
                    )
                    # -------------------------------------------------
                    # سهم Normal / Mortgage برگشتی
                    #
                    # premium منفی است و mortgage_premium مثبت ذخیره شده.
                    # -------------------------------------------------
                    policy_premium = Decimal(
                        str(
                            policy.premium
                            or 0
                        )
                    )
                    policy_mortgage = Decimal(
                        str(
                            policy.mortgage_premium
                            or 0
                        )
                    )
                    if policy_premium != 0:
                        mortgage_ratio = (
                            policy_mortgage
                            / abs(policy_premium)
                        )
                        mortgage_return = (
                            effective_return_net
                            * mortgage_ratio
                        )
                    else:
                        mortgage_return = (
                            Decimal("0")
                        )
                    normal_return = (
                        effective_return_net
                        - mortgage_return
                    )
                    # -------------------------------------------------
                    # Tier کاهش‌یافته
                    # -------------------------------------------------
                    previous_tier = calculate_base_commission(
                        cumulative_before,
                        Decimal("100"),
                        Decimal(
                            str(
                                config.first_step_commission
                            )
                        )
                    )
                    current_tier = calculate_base_commission(
                        cumulative_after,
                        Decimal("100"),
                        Decimal(
                            str(
                                config.first_step_commission
                            )
                        )
                    )
                    tier_reduction = (
                        previous_tier
                        - current_tier
                    )
                    tier_factor = Decimal("0")
                    if effective_return_net != 0:
                        tier_factor = (
                            tier_reduction
                            / effective_return_net
                        )
                    return_commission = (
                        normal_return
                        * normal_rate
                        / Decimal("100")
                        * tier_factor
                        +
                        mortgage_return
                        * mortgage_rate
                        / Decimal("100")
                        * tier_factor
                    )
                    commission = (
                        -return_commission
                    )
                    gross_commission = (
                        commission
                        * return_gross_factor
                    )
                    cumulative_collection = (
                        cumulative_after
                    )
                    # سهم mortgage cumulative نیز باید کم شود
                    cumulative_mortgage_collection = max(
                        cumulative_mortgage_collection
                        - mortgage_return,
                        Decimal("0")
                    )
                    if not (
                        start_date
                        <= event["date"]
                        <= end_date
                    ):
                        continue
                    details.append({
                        "policy_id":
                            policy.id,
                        "endorsement_number":
                            policy.endorsement_number,
                        "date":
                            event["date"],
                        "collection_amount":
                            -round(
                                effective_return_gross
                            ),
                        "net_collection_amount":
                            -round(
                                effective_return_net
                            ),
                        "cumulative_net_collection":
                            round(
                                cumulative_collection
                            ),
                        "commission_percent":
                            None,
                        "normal_commission_percent":
                            normal_rate,
                        "mortgage_commission_percent":
                            mortgage_rate,
                        "commission":
                            round(commission),
                        "gross_commission":
                            round(
                                gross_commission
                            ),
                    })
                    total_commission += (
                        round(commission)
                    )
                    total_gross_commission += (
                        round(gross_commission)
                    )
            details.sort(
                key=lambda item: (
                    item["date"],
                    item["policy_id"]
                )
            )
        result[issue_code] = {
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
                round(
                    total_gross_commission
                ),
        }
    return result
# =========================================================
# گزارش کارمزد بازاریاب
# =========================================================
def get_marketer_commission_report(
    marketer_id,
    basis,
    start_date,
    end_date
):
    db = SessionLocal()
    try:
        # =========================================================
        # 1) بیمه‌نامه‌های متعلق به بازاریاب
        # =========================================================
        marketer_policies = (
            db.query(Policy)
            .options(
                joinedload(Policy.customer),
                joinedload(Policy.insurance_type),
                joinedload(Policy.marketer),
            )
            .filter(
                Policy.marketer_id == marketer_id
            )
            .all()
        )
        if not marketer_policies:
            return {
                "details": [],
                "total_premium": 0,
                "total_net_premium": 0,
                "total_commission": 0,
                "total_gross_commission": 0,
                "total_marketer_commission": 0,
            }
        # =========================================================
        # 2) issue_codeهای مربوط به بیمه‌نامه‌های بازاریاب
        # =========================================================
        issue_codes = {
            policy.issue_code
            for policy in marketer_policies
            if policy.issue_code
        }
        if not issue_codes:
            return {
                "details": [],
                "total_premium": 0,
                "total_net_premium": 0,
                "total_commission": 0,
                "total_gross_commission": 0,
                "total_marketer_commission": 0,
            }
        # =========================================================
        # 3) همه Policyهای این issue_codeها
        # =========================================================
        all_policies = (
            db.query(Policy)
            .options(
                joinedload(Policy.customer),
                joinedload(Policy.insurance_type),
                joinedload(Policy.marketer),
            )
            .filter(
                Policy.issue_code.in_(issue_codes)
            )
            .all()
        )
        # ---------------------------------------------------------
        # Policyهای بازاریاب برای تشخیص اینکه کدام Detail
        # باید وارد گزارش شود.
        # ---------------------------------------------------------
        marketer_policy_ids = {
            policy.id
            for policy in marketer_policies
        }
        marketer_policies_by_id = {
            policy.id: policy
            for policy in marketer_policies
        }
        # =========================================================
        # 4) Collectionها
        # =========================================================
        collections = []
        if basis == "collection":
            all_policy_ids = [
                policy.id
                for policy in all_policies
            ]
            if all_policy_ids:
                collections = (
                    db.query(Collection)
                    .filter(
                        Collection.policy_id.in_(
                            all_policy_ids
                        ),
                        Collection.collection_date <= end_date
                    )
                    .all()
                )
        # =========================================================
        # 5) محاسبه Batch
        # =========================================================
        batch_reports = calculate_batch_commission_reports(
            policies=all_policies,
            collections=collections,
            basis=basis,
            start_date=start_date,
            end_date=end_date
        )
        # =========================================================
        # 6) ساخت خروجی بازاریاب
        # =========================================================
        details = []
        total_premium = 0
        total_net_premium = 0
        total_commission = 0
        total_gross_commission = 0
        total_marketer_commission = 0
        for issue_code in issue_codes:
            report = batch_reports.get(
                issue_code
            )
            if not report:
                continue
            for detail in report.get(
                "details",
                []
            ):
                policy_id = detail.get(
                    "policy_id"
                )
                # -------------------------------------------------
                # فقط Policyهای متعلق به همین بازاریاب
                # -------------------------------------------------
                if policy_id not in marketer_policy_ids:
                    continue
                policy = marketer_policies_by_id.get(
                    policy_id
                )
                if not policy:
                    continue
                commission = detail.get(
                    "commission",
                    0
                ) or 0
                gross_commission = detail.get(
                    "gross_commission",
                    0
                ) or 0
                # -------------------------------------------------
                # سهم بازاریاب
                # -------------------------------------------------
                marketer_share = (
                    calculate_marketer_share_from_commission(
                        policy,
                        commission
                    )
                )
                # -------------------------------------------------
                # نام بیمه‌گذار
                # -------------------------------------------------
                customer_name = ""
                if policy.customer:
                    customer_name = (
                        f"{policy.customer.name or ''} "
                        f"{policy.customer.family or ''}"
                    ).strip()
                # -------------------------------------------------
                # رشته بیمه
                # -------------------------------------------------
                insurance_type_name = ""
                if policy.insurance_type:
                    insurance_type_name = (
                        policy.insurance_type.display_name
                        or ""
                    )
                # -------------------------------------------------
                # ساخت Row
                # -------------------------------------------------
                row = {
                    **detail,
                    "policy_number":
                        policy.policy_number,
                    "customer_name":
                        customer_name,
                    "insurance_type_name":
                        insurance_type_name,
                    "marketer_commission":
                        marketer_share,
                }
                details.append(row)
                # -------------------------------------------------
                # Totals
                # -------------------------------------------------
                total_premium += (
                    detail.get(
                        "premium",
                        0
                    ) or 0
                )
                total_net_premium += (
                    detail.get(
                        "net_premium",
                        0
                    ) or 0
                )
                total_commission += commission
                total_gross_commission += (
                    gross_commission
                )
                total_marketer_commission += (
                    marketer_share
                )
        # =========================================================
        # 7) مرتب‌سازی نهایی
        # =========================================================
        details.sort(
            key=lambda item: (
                item.get("date") or start_date,
                item.get("policy_id") or 0
            )
        )
        # =========================================================
        # 8) خروجی
        # =========================================================
        return {
            "details":
                details,
            "total_premium":
                total_premium,
            "total_net_premium":
                total_net_premium,
            "total_commission":
                total_commission,
            "total_gross_commission":
                total_gross_commission,
            "total_marketer_commission":
                total_marketer_commission,
        }
    finally:
        db.close()
def get_policy_commission_report(
    issue_code,
    as_of_date=None
):
    db = SessionLocal()
    try:
        if not issue_code:
            return None
        if as_of_date is None:
            as_of_date = date.today()
        current_agent = get_current_agent()
        # =====================================================
        # تمام بیمه‌نامه‌ها و الحاقیه‌های این issue_code
        # =====================================================
        policies = (
            db.query(Policy)
            .options(
                joinedload(Policy.customer),
                joinedload(Policy.insurance_type),
                joinedload(Policy.marketer),
            )
            .filter(
                Policy.issue_code == issue_code,
                Policy.issue_date <= as_of_date
            )
            .order_by(
                Policy.endorsement_number.asc(),
                Policy.id.asc()
            )
            .all()
        )
        if not policies:
            return None
        policies_by_id = {
            policy.id: policy
            for policy in policies
        }
        policy_ids = [
            policy.id
            for policy in policies
        ]
        issue_dates = [
            policy.issue_date
            for policy in policies
            if policy.issue_date
        ]
        if not issue_dates:
            return None
        start_date = min(issue_dates)
        # =====================================================
        # بیمه‌نامه اصلی
        # =====================================================
        original_policy = next(
            (
                policy
                for policy in policies
                if (policy.endorsement_number or 0) == 0
            ),
            policies[0]
        )
        original_policy_id = original_policy.id
        # =====================================================
        # Collectionها
        # =====================================================
        collections = (
            db.query(Collection)
            .filter(
                Collection.policy_id.in_(policy_ids),
                Collection.collection_date <= as_of_date
            )
            .all()
        )
        # =====================================================
        # گزارش حق بیمه
        # =====================================================
        premium_reports = (
            calculate_batch_commission_reports(
                policies=policies,
                collections=collections,
                basis="premium",
                start_date=start_date,
                end_date=as_of_date
            )
        )
        premium_report = premium_reports.get(
            issue_code,
            {}
        )
        # =====================================================
        # گزارش وصولی
        # =====================================================
        collection_reports = (
            calculate_batch_commission_reports(
                policies=policies,
                collections=collections,
                basis="collection",
                start_date=start_date,
                end_date=as_of_date
            )
        )
        collection_report = collection_reports.get(
            issue_code,
            {}
        )
        # =====================================================
        # هزینه صدور - حق بیمه
        # =====================================================
        premium_issuance_reports = (
            calculate_batch_issuance_reports(
                policies=policies,
                collections=collections,
                basis="premium",
                start_date=start_date,
                end_date=as_of_date,
                current_agent=current_agent
            )
        )
        premium_issuance_map = premium_issuance_reports.get(
            issue_code,
            {}
        )
        # =====================================================
        # هزینه صدور - وصولی
        # =====================================================
        collection_issuance_reports = (
            calculate_batch_issuance_reports(
                policies=policies,
                collections=collections,
                basis="collection",
                start_date=start_date,
                end_date=as_of_date,
                current_agent=current_agent
            )
        )
        collection_issuance_map = collection_issuance_reports.get(
            issue_code,
            {}
        )
        # =====================================================
        # مبلغ حق بیمه اصلی و الحاقیه‌ها
        # =====================================================
        original_gross_premium = 0
        original_net_premium = 0
        endorsement_gross_premium = 0
        endorsement_net_premium = 0
        for detail in premium_report.get(
            "details",
            []
        ):
            policy = policies_by_id.get(
                detail.get("policy_id")
            )
            if not policy:
                continue
            premium = (
                detail.get("premium", 0)
                or 0
            )
            net_premium = (
                detail.get("net_premium", 0)
                or 0
            )
            if policy.id == original_policy_id:
                original_gross_premium += premium
                original_net_premium += net_premium
            else:
                endorsement_gross_premium += premium
                endorsement_net_premium += net_premium
        # =====================================================
        # مجموع وصولی
        # =====================================================
        total_collection = sum(
            (
                collection.settlement_amount
                or 0
            )
            for collection in collections
        )
        total_gross_premium = (
            original_gross_premium
            + endorsement_gross_premium
        )
        remaining_uncollected = max(
            total_gross_premium
            - total_collection,
            0
        )
        # =====================================================
        # جزئیات حق بیمه
        # =====================================================
        premium_details = []
        premium_net_commission = 0
        premium_gross_commission = 0
        premium_marketer_share = 0
        premium_net_issuance = 0
        premium_gross_issuance = 0
        for detail in premium_report.get(
            "details",
            []
        ):
            policy = policies_by_id.get(
                detail.get("policy_id")
            )
            if not policy:
                continue
            commission = (
                detail.get("commission", 0)
                or 0
            )
            gross_commission = (
                detail.get("gross_commission", 0)
                or 0
            )
            if (
                policy.referrer_work_unit
                == current_agent
            ):
                marketer_share = (
                    calculate_marketer_share_from_commission(
                        policy,
                        commission
                    )
                )
            else:
                commission = 0
                gross_commission = 0
                marketer_share = 0
            issuance_data = (
                premium_issuance_map.get(
                    policy.id,
                    {}
                )
            )
            net_issuance = (
                issuance_data.get(
                    "net_issuance",
                    0
                )
                or 0
            )
            gross_issuance = (
                issuance_data.get(
                    "gross_issuance",
                    0
                )
                or 0
            )
            if (
                commission == 0
                and gross_commission == 0
                and net_issuance == 0
                and gross_issuance == 0
            ):
                continue
            customer_name = ""
            if policy.customer:
                customer_name = (
                    f"{policy.customer.name or ''} "
                    f"{policy.customer.family or ''}"
                ).strip()
            premium_details.append({
                **detail,
                "policy_number":
                    policy.policy_number,
                "customer_name":
                    customer_name,
                "insurance_type_name": (
                    policy.insurance_type.display_name
                    if policy.insurance_type
                    else ""
                ),
                "commission":
                    commission,
                "gross_commission":
                    gross_commission,
                "marketer_commission":
                    marketer_share,
                "net_issuance":
                    net_issuance,
                "gross_issuance":
                    gross_issuance,
            })
            premium_net_commission += commission
            premium_gross_commission += gross_commission
            premium_marketer_share += marketer_share
            premium_net_issuance += net_issuance
            premium_gross_issuance += gross_issuance
        # =====================================================
        # اضافه کردن Policyهایی که فقط هزینه صدور دارند
        # =====================================================
        for policy_id, issuance_data in (
            premium_issuance_map.items()
        ):
            policy = policies_by_id.get(
                policy_id
            )
            if not policy:
                continue
            already_exists = any(
                detail.get("policy_id") == policy_id
                for detail in premium_details
            )
            if already_exists:
                continue
            net_issuance = (
                issuance_data.get(
                    "net_issuance",
                    0
                )
                or 0
            )
            gross_issuance = (
                issuance_data.get(
                    "gross_issuance",
                    0
                )
                or 0
            )
            if (
                net_issuance == 0
                and gross_issuance == 0
            ):
                continue
            customer_name = ""
            if policy.customer:
                customer_name = (
                    f"{policy.customer.name or ''} "
                    f"{policy.customer.family or ''}"
                ).strip()
            premium_details.append({
                "policy_id":
                    policy.id,
                "endorsement_number":
                    policy.endorsement_number,
                "date":
                    policy.issue_date,
                "premium":
                    policy.premium or 0,
                "net_premium":
                    0,
                "commission_percent":
                    0,
                "commission":
                    0,
                "gross_commission":
                    0,
                "policy_number":
                    policy.policy_number,
                "customer_name":
                    customer_name,
                "insurance_type_name": (
                    policy.insurance_type.display_name
                    if policy.insurance_type
                    else ""
                ),
                "marketer_commission":
                    0,
                "net_issuance":
                    net_issuance,
                "gross_issuance":
                    gross_issuance,
            })
            premium_net_issuance += net_issuance
            premium_gross_issuance += gross_issuance
        # =====================================================
        # جزئیات وصولی
        # =====================================================
        collection_details = []
        collection_net_commission = 0
        collection_gross_commission = 0
        collection_marketer_share = 0
        collection_net_issuance = 0
        collection_gross_issuance = 0
        for detail in collection_report.get(
            "details",
            []
        ):
            policy = policies_by_id.get(
                detail.get("policy_id")
            )
            if not policy:
                continue
            commission = (
                detail.get("commission", 0)
                or 0
            )
            gross_commission = (
                detail.get("gross_commission", 0)
                or 0
            )
            if (
                policy.referrer_work_unit
                == current_agent
            ):
                marketer_share = (
                    calculate_marketer_share_from_commission(
                        policy,
                        commission
                    )
                )
            else:
                commission = 0
                gross_commission = 0
                marketer_share = 0
            collection_id = detail.get(
                "collection_id"
            )
            if collection_id is not None:
                issuance_data = (
                    collection_issuance_map.get(
                        collection_id,
                        {}
                    )
                )
            else:
                issuance_data = (
                    collection_issuance_map.get(
                        policy.id,
                        {}
                    )
                )
            net_issuance = (
                issuance_data.get(
                    "net_issuance",
                    0
                )
                or 0
            )
            gross_issuance = (
                issuance_data.get(
                    "gross_issuance",
                    0
                )
                or 0
            )
            if (
                commission == 0
                and gross_commission == 0
                and net_issuance == 0
                and gross_issuance == 0
            ):
                continue
            customer_name = ""
            if policy.customer:
                customer_name = (
                    f"{policy.customer.name or ''} "
                    f"{policy.customer.family or ''}"
                ).strip()
            collection_details.append({
                **detail,
                "policy_number":
                    policy.policy_number,
                "customer_name":
                    customer_name,
                "insurance_type_name": (
                    policy.insurance_type.display_name
                    if policy.insurance_type
                    else ""
                ),
                "commission":
                    commission,
                "gross_commission":
                    gross_commission,
                "marketer_commission":
                    marketer_share,
                "net_issuance":
                    net_issuance,
                "gross_issuance":
                    gross_issuance,
            })
            collection_net_commission += commission
            collection_gross_commission += gross_commission
            collection_marketer_share += marketer_share
            collection_net_issuance += net_issuance
            collection_gross_issuance += gross_issuance
        # =====================================================
        # مرتب‌سازی
        # =====================================================
        premium_details.sort(
            key=lambda item: (
                item.get("date") or start_date,
                item.get("policy_id") or 0
            )
        )
        collection_details.sort(
            key=lambda item: (
                item.get("date") or start_date,
                item.get("policy_id") or 0
            )
        )
        # =====================================================
        # خروجی
        # =====================================================
        return {
            "issue_code":
                issue_code,
            "policy_number":
                original_policy.policy_number,
            "start_date":
                start_date,
            "as_of_date":
                as_of_date,
            "original_gross_premium":
                original_gross_premium,
            "original_net_premium":
                original_net_premium,
            "endorsement_gross_premium":
                endorsement_gross_premium,
            "endorsement_net_premium":
                endorsement_net_premium,
            "total_collection":
                round(total_collection),
            "remaining_uncollected":
                round(remaining_uncollected),
            "premium_net_commission":
                round(premium_net_commission),
            "premium_gross_commission":
                round(premium_gross_commission),
            "collection_net_commission":
                round(collection_net_commission),
            "collection_gross_commission":
                round(collection_gross_commission),
            "premium_marketer_share":
                round(premium_marketer_share),
            "collection_marketer_share":
                round(collection_marketer_share),
            "premium_net_issuance":
                round(premium_net_issuance),
            "premium_gross_issuance":
                round(premium_gross_issuance),
            "collection_net_issuance":
                round(collection_net_issuance),
            "collection_gross_issuance":
                round(collection_gross_issuance),
            "premium_details":
                premium_details,
            "collection_details":
                collection_details,
        }
    finally:
        db.close()
