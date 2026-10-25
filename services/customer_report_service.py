from bisect import bisect_right
from database import SessionLocal
from sqlalchemy.orm import contains_eager
from models import Collection, Policy, InsuranceType,CommissionConfig
from services.business_rules import VAT_EXEMPT_TYPES
DEBT_TYPE_PREMIUM_DUE = "سررسيد حق بيمه"
def get_customer_payment_behavior(customer_id):
    """
    گزارش میزان خوش‌حسابی یک بیمه‌گذار.
    فقط وصولی‌هایی بررسی می‌شوند که:
    - نوع بدهی آن‌ها «سررسید حق بیمه» باشد.
    - تاریخ سررسید داشته باشند.
    - تاریخ وصول داشته باشند.
    - متعلق به بیمه‌نامه‌های این بیمه‌گذار باشند.
    وصول قبل از سررسید نیز بدون تأخیر محسوب می‌شود.
    """
    with SessionLocal() as session:
        collections = (
            session.query(Collection)
            .join(Collection.policy)
            .options(
                contains_eager(Collection.policy)
                .joinedload(Policy.customer)
            )
            .filter(
                Collection.debt_type == DEBT_TYPE_PREMIUM_DUE,
                Collection.due_date.isnot(None),
                Collection.collection_date.isnot(None),
            )
            .order_by(
                Policy.customer_id,
                Collection.due_date,
                Collection.id
            )
            .all()
        )
        total_collections = 0
        total_delay = 0
        on_time_count = 0
        one_day_late_count = 0
        up_to_5_days_count = 0
        up_to_10_days_count = 0
        up_to_15_days_count = 0
        over_15_days_count = 0
        for collection in collections:
            delay_days = (
                collection.collection_date
                - collection.due_date
            ).days
            # وصول قبل از سررسید = بدون تأخیر
            delay_days = max(delay_days, 0)
            total_collections += 1
            total_delay += delay_days
            if delay_days == 0:
                on_time_count += 1
            elif delay_days == 1:
                one_day_late_count += 1
            elif delay_days <= 5:
                up_to_5_days_count += 1
            elif delay_days <= 10:
                up_to_10_days_count += 1
            elif delay_days < 15:
                up_to_15_days_count += 1
            else:
                over_15_days_count += 1
        if total_collections == 0:
            average_delay = 0
        else:
            average_delay = total_delay / total_collections
        return {
            "customer_id": customer_id,
            "total_collections": total_collections,
            "average_delay": average_delay,
            "on_time_count": on_time_count,
            "one_day_late_count": one_day_late_count,
            "up_to_5_days_count": up_to_5_days_count,
            "up_to_10_days_count": up_to_10_days_count,
            "up_to_15_days_count": up_to_15_days_count,
            "over_15_days_count": over_15_days_count,
        }
def get_customers_with_average_delay_between(
    min_days=None,
    max_days=None
):
    """
    گزارش بیمه‌گذارانی که میانگین تأخیر وصولی‌های سررسیددار
    در بازه تعیین‌شده قرار دارد.
    min_days شامل می‌شود.
    max_days شامل نمی‌شود.
    """
    with SessionLocal() as session:
        collections = (
            session.query(Collection)
            .join(Collection.policy)
            .filter(
                Collection.debt_type == DEBT_TYPE_PREMIUM_DUE,
                Collection.due_date.isnot(None),
                Collection.collection_date.isnot(None),
            )
            .order_by(
                Policy.customer_id,
                Collection.due_date,
                Collection.id
            )
            .all()
        )
        customer_data = {}
        for collection in collections:
            customer = collection.policy.customer
            if customer is None:
                continue
            customer_id = customer.id
            if customer_id not in customer_data:
                customer_data[customer_id] = {
                    "customer_id": customer_id,
                    "customer_code": customer.customer_code or "",
                    "customer_name": customer.name,
                    "customer_family": customer.family or "",
                    "total_collections": 0,
                    "total_delay": 0,
                    "over_15_days_count": 0,
                }
            delay_days = (
                collection.collection_date
                - collection.due_date
            ).days
            delay_days = max(delay_days, 0)
            customer_data[customer_id]["total_collections"] += 1
            customer_data[customer_id]["total_delay"] += delay_days
            if delay_days >= 15:
                customer_data[customer_id]["over_15_days_count"] += 1
        results = []
        for data in customer_data.values():
            total_collections = data["total_collections"]
            average_delay = (
                data["total_delay"]
                / total_collections
            )
            if min_days is not None and average_delay < min_days:
                continue
            if max_days is not None and average_delay >= max_days:
                continue
            results.append({
                "customer_id": data["customer_id"],
                "customer_code": data["customer_code"],
                "customer_name": data["customer_name"],
                "customer_family": data["customer_family"],
                "total_collections": total_collections,
                "average_delay": average_delay,
                "over_15_days_count": data["over_15_days_count"],
            })
        results.sort(
            key=lambda item: item["average_delay"],
            reverse=True
        )
        return results
def get_customers_with_over_15_days_delay():
    """
    گزارش بیمه‌گذارانی که حداقل یک وصولی
    با تأخیر بیش از 15 روز دارند.
    مرتب‌سازی بر اساس تعداد موارد تأخیر بیش از 15 روز
    به صورت نزولی انجام می‌شود.
    """
    with SessionLocal() as session:
        collections = (
            session.query(Collection)
            .join(Collection.policy)
            .filter(
                Collection.debt_type == DEBT_TYPE_PREMIUM_DUE,
                Collection.due_date.isnot(None),
                Collection.collection_date.isnot(None),
            )
            .order_by(
                Policy.customer_id,
                Collection.due_date,
                Collection.id
            )
            .all()
        )
        customer_data = {}
        for collection in collections:
            customer = collection.policy.customer
            if customer is None:
                continue
            customer_id = customer.id
            if customer_id not in customer_data:
                customer_data[customer_id] = {
                    "customer_id": customer_id,
                    "customer_code": customer.customer_code or "",
                    "customer_name": customer.name,
                    "customer_family": customer.family or "",
                    "total_collections": 0,
                    "total_delay": 0,
                    "over_15_days_count": 0,
                }
            delay_days = (
                collection.collection_date
                - collection.due_date
            ).days
            delay_days = max(delay_days, 0)
            customer_data[customer_id]["total_collections"] += 1
            customer_data[customer_id]["total_delay"] += delay_days
            if delay_days >= 15:
                customer_data[customer_id]["over_15_days_count"] += 1
        results = []
        for data in customer_data.values():
            if data["over_15_days_count"] == 0:
                continue
            total_collections = data["total_collections"]
            average_delay = (
                data["total_delay"]
                / total_collections
            )
            results.append({
                "customer_id": data["customer_id"],
                "customer_code": data["customer_code"],
                "customer_name": data["customer_name"],
                "customer_family": data["customer_family"],
                "total_collections": total_collections,
                "average_delay": average_delay,
                "over_15_days_count": data[
                    "over_15_days_count"
                ],
            })
        results.sort(
            key=lambda item: item["over_15_days_count"],
            reverse=True
        )
        return results
def get_customers_by_total_premium(
    from_date=None,
    to_date=None
):
    """
    گزارش بیمه‌گذاران بر اساس مجموع حق‌بیمه خالص.
    اگر from_date و to_date مشخص باشند،
    فقط بیمه‌نامه‌های صادرشده در آن بازه بررسی می‌شوند.
    اگر هر دو None باشند، کل بیمه‌نامه‌ها بررسی می‌شوند.
    بیمه‌نامه‌های نوع «عمر و پس انداز» در گزارش لحاظ نمی‌شوند.
    """
    with SessionLocal() as session:
        # دریافت تمام تنظیمات VAT فقط یک بار
        commission_configs = (
            session.query(CommissionConfig)
            .order_by(
                CommissionConfig.effective_date
            )
            .all()
        )
        config_dates = [
            config.effective_date
            for config in commission_configs
        ]
        query = (
            session.query(Policy)
            .join(Policy.customer)
            .join(Policy.insurance_type)
            .options(
                contains_eager(Policy.customer),
                contains_eager(Policy.insurance_type),
            )
            .filter(
                Policy.issue_date.isnot(None),
                InsuranceType.display_name != "عمر و پس انداز",
            )
        )
        if from_date is not None:
            query = query.filter(
                Policy.issue_date >= from_date
            )
        if to_date is not None:
            query = query.filter(
                Policy.issue_date <= to_date
            )
        policies = (
            query
            .order_by(
                Policy.customer_id,
                Policy.issue_date,
                Policy.id
            )
            .all()
        )
        customer_data = {}
        for policy in policies:
            customer = policy.customer
            if customer is None:
                continue
            customer_id = customer.id
            if customer_id not in customer_data:
                customer_data[customer_id] = {
                    "customer_id": customer_id,
                    "customer_code": customer.customer_code or "",
                    "customer_name": customer.name,
                    "customer_family": customer.family or "",
                    "policy_count": 0,
                    "total_premium": 0,
                }
            premium = policy.premium or 0
            if premium == 0:
                net_premium = 0
            else:
                # پیدا کردن آخرین تنظیمی که
                # effective_date <= issue_date باشد
                config_index = bisect_right(
                    config_dates,
                    policy.issue_date
                ) - 1
                if config_index < 0:
                    continue
                vat_config = commission_configs[config_index]
                vat = vat_config.vat or 0
                insurance_type = policy.insurance_type
                is_exempt = (
                    insurance_type
                    and
                    insurance_type.display_name
                    in VAT_EXEMPT_TYPES
                )
                if is_exempt:
                    net_premium = premium
                else:
                    vat_factor = 1 + vat
                    net_premium = (
                        premium / vat_factor
                        if vat_factor
                        else premium
                    )
            customer_data[customer_id]["policy_count"] += 1
            customer_data[customer_id]["total_premium"] += net_premium
        results = list(customer_data.values())
        results.sort(
            key=lambda item: item["total_premium"],
            reverse=True
        )
        return results