import operator
from services.date_service import convert_shamsi_to_date
# ==================================================
# شرط‌های جستجو
#
# پنجره‌های جستجو همین فهرست‌ها را import می‌کنند تا املای شرط‌ها
# در رابط کاربری و در منطق فیلتر همیشه یکی باشد.
# ==================================================
BETWEEN = "مابین"
COMPARISON_OPERATORS = {
    "برابر با": operator.eq,
    "کوچکتر از": operator.lt,
    "کوچکتر مساوی": operator.le,
    "بزرگتر از": operator.gt,
    "بزرگتر مساوی": operator.ge,
}
# شرط‌های تاریخ (صدور، شروع، پایان)
DATE_CONDITIONS = list(COMPARISON_OPERATORS) + [BETWEEN]
# شرط‌های عددی (حق‌بیمه، سهم صندوق)
NUMBER_CONDITIONS = list(COMPARISON_OPERATORS)
def format_policy_number(value):
    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    # حذف اعشار صفر:
    # 4.0 -> 4
    # 4.00 -> 4
    # 208.000 -> 208
    if "." in text:
        integer_part, decimal_part = text.split(".", 1)
        if decimal_part.strip("0") == "":
            return integer_part
    return text
def _parse_shamsi(date_text):
    """تاریخ شمسی را به date تبدیل می‌کند؛ در صورت نامعتبر بودن None."""
    try:
        return convert_shamsi_to_date(date_text)
    except (ValueError, AttributeError, TypeError):
        return None
def _to_date(value):
    """datetime را به date تبدیل می‌کند تا با تاریخ جستجو قابل مقایسه باشد."""
    if value is not None and hasattr(value, "date"):
        return value.date()
    return value
def filter_date(
    policies,
    attribute,
    condition,
    date_text,
    date_text2=""
):
    date_text = (date_text or "").strip()
    # ---------------- مابین ----------------
    if condition == BETWEEN:
        date_text2 = (date_text2 or "").strip()
        if len(date_text) != 10 or len(date_text2) != 10:
            return policies
        date_from = _parse_shamsi(date_text)
        date_to = _parse_shamsi(date_text2)
        if date_from is None or date_to is None:
            return policies
        if date_from > date_to:
            return []
        def matches(policy_date):
            return date_from <= policy_date <= date_to
    # ---------------- برابر / کوچکتر / بزرگتر (و حالت‌های مساوی) ----------------
    else:
        compare = COMPARISON_OPERATORS.get(condition)
        if compare is None or len(date_text) != 10:
            return policies
        target_date = _parse_shamsi(date_text)
        if target_date is None:
            return policies
        def matches(policy_date):
            return compare(policy_date, target_date)
    result = []
    for policy in policies:
        policy_date = _to_date(getattr(policy, attribute, None))
        if policy_date is None:
            continue
        if matches(policy_date):
            result.append(policy)
    return result
def filter_number(
    policies,
    attribute,
    condition,
    target
):
    """
    فیلتر عددی (حق‌بیمه، سهم صندوق).
    مقدار خالی (None) مثل صفر حساب می‌شود، همان‌طور که در جدول
    نمایش داده می‌شود؛ پس مقایسه‌ی <، <=، > و >= خطا نمی‌دهد.
    """
    compare = COMPARISON_OPERATORS.get(condition)
    if compare is None:
        return policies
    return [
        policy
        for policy in policies
        if compare(getattr(policy, attribute, None) or 0, target)
    ]
def filter_policies(
    policies,
    customer_ids=None,
    policy_number="",
    policy_number_condition="برابر با",
    insurance_type_id=None,
    issue_date=None,
    start_date=None,
    end_date=None,
    referrer_condition=None,
    referrer="",
    marketer_condition=None,
    marketer_id=None,
    record_type=None,
    premium=None,
    premium_condition="برابر با",
    fund=None,
    fund_condition="برابر با",
    mortgage=None,
    current_agent=None,
):
    filtered_policies = list(policies)
    # ---------------- بیمه‌گذار ----------------
    if customer_ids:
        customer_ids = set(customer_ids)
        filtered_policies = [
            policy
            for policy in filtered_policies
            if policy.customer_id in customer_ids
        ]
    # ---------------- شماره بیمه‌نامه ----------------
    if policy_number:
        search_number = format_policy_number(policy_number)
        if policy_number_condition == "برابر با":
            filtered_policies = [
                policy
                for policy in filtered_policies
                if format_policy_number(policy.policy_number)
                == search_number
            ]
    # ---------------- نوع بیمه ----------------
    if insurance_type_id is not None:
        filtered_policies = [
            policy
            for policy in filtered_policies
            if policy.insurance_type_id == insurance_type_id
        ]
    # ---------------- تاریخ صدور ----------------
    if issue_date:
        condition, date_text, date_text2 = issue_date
        filtered_policies = filter_date(
            filtered_policies,
            "issue_date",
            condition,
            date_text,
            date_text2,
        )
    # ---------------- تاریخ شروع ----------------
    if start_date:
        condition, date_text, date_text2 = start_date
        filtered_policies = filter_date(
            filtered_policies,
            "start_date",
            condition,
            date_text,
            date_text2,
        )
    # ---------------- تاریخ پایان ----------------
    if end_date:
        condition, date_text, date_text2 = end_date
        filtered_policies = filter_date(
            filtered_policies,
            "end_date",
            condition,
            date_text,
            date_text2,
        )
    # ---------------- معرف ----------------
    if referrer_condition:
        if referrer_condition == "معرف دارد":
            filtered_policies = [
                policy
                for policy in filtered_policies
                if (
                    policy.referrer
                    and policy.referrer.strip() != ""
                    and policy.referrer.strip() != current_agent
                )
            ]
        elif referrer_condition == "بدون معرف":
            filtered_policies = [
                policy
                for policy in filtered_policies
                if (
                    not policy.referrer
                    or policy.referrer.strip() == ""
                    or policy.referrer.strip() == current_agent
                )
            ]
        elif referrer_condition == "برابر با":
            if referrer:
                filtered_policies = [
                    policy
                    for policy in filtered_policies
                    if (
                        (policy.referrer or "") == referrer
                        and policy.referrer != current_agent
                    )
                ]
        elif referrer_condition == "شامل":
            if referrer:
                filtered_policies = [
                    policy
                    for policy in filtered_policies
                    if (
                        referrer in (policy.referrer or "")
                        and policy.referrer != current_agent
                    )
                ]
    # ---------------- بازاریاب ----------------
    if marketer_condition:
        if marketer_condition == "بازاریاب دارد":
            filtered_policies = [
                policy
                for policy in filtered_policies
                if policy.marketer is not None
            ]
        elif marketer_condition == "بدون بازاریاب":
            filtered_policies = [
                policy
                for policy in filtered_policies
                if policy.marketer is None
            ]
        elif marketer_condition == "برابر با":
            if marketer_id is not None:
                filtered_policies = [
                    policy
                    for policy in filtered_policies
                    if policy.marketer_id == marketer_id
                ]
    # ---------------- نوع رکورد ----------------
    if record_type:
        if record_type == "بیمه‌نامه":
            filtered_policies = [
                policy
                for policy in filtered_policies
                if policy.endorsement_number == 0
            ]
        elif record_type == "الحاقیه":
            filtered_policies = [
                policy
                for policy in filtered_policies
                if policy.endorsement_number != 0
            ]
    # ---------------- حق بیمه ----------------
    if premium is not None:
        filtered_policies = filter_number(
            filtered_policies,
            "premium",
            premium_condition,
            premium,
        )
    # ---------------- صندوق ----------------
    if fund is not None:
        filtered_policies = filter_number(
            filtered_policies,
            "fund",
            fund_condition,
            fund,
        )
    # ---------------- مرهوناتی ----------------
    if mortgage:
        if mortgage == "مرهوناتی":
            filtered_policies = [
                policy
                for policy in filtered_policies
                if policy.is_mortgage
            ]
        elif mortgage == "غیر مرهوناتی":
            filtered_policies = [
                policy
                for policy in filtered_policies
                if not policy.is_mortgage
            ]
    return filtered_policies