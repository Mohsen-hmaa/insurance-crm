import time
from datetime import date, timedelta
from database import SessionLocal
from models import Customer, Policy, Collection
from services.agency_performance_service import (
    get_agency_performance_report,
)
from services.policy_report_service import (
    load_expiry_policies,
)
def get_dashboard_data():
    total_start = time.perf_counter()
    # ---------------------------------------------------------
    # Today
    # ---------------------------------------------------------
    today = date.today()
    start_of_year = date(
        today.year,
        1,
        1,
    )
    # ---------------------------------------------------------
    # Agency performance
    # ---------------------------------------------------------
    start = time.perf_counter()
    performance = get_agency_performance_report(
        start_of_year,
        today,
    )
    # ---------------------------------------------------------
    # Database information
    # ---------------------------------------------------------
    db = SessionLocal()
    try:
        start = time.perf_counter()
        # تعداد کل بیمه‌گذاران
        customer_count = (
            db.query(Customer)
            .count()
        )
        # آخرین تاریخ صدور بیمه‌نامه
        latest_policy_date = (
            db.query(Policy.issue_date)
            .filter(
                Policy.issue_date.isnot(None)
            )
            .order_by(
                Policy.issue_date.desc()
            )
            .first()
        )
        # آخرین تاریخ وصولی
        latest_collection_date = (
            db.query(Collection.collection_date)
            .filter(
                Collection.collection_date.isnot(None)
            )
            .order_by(
                Collection.collection_date.desc()
            )
            .first()
        )
    finally:
        db.close()
    # ---------------------------------------------------------
    # Extract dates
    # ---------------------------------------------------------
    latest_policy_date = (
        latest_policy_date[0]
        if latest_policy_date
        else None
    )
    latest_collection_date = (
        latest_collection_date[0]
        if latest_collection_date
        else None
    )
    dates = [
        current_date
        for current_date in (
            latest_policy_date,
            latest_collection_date,
        )
        if current_date is not None
    ]
    latest_update_date = (
        max(dates)
        if dates
        else None
    )
    # ---------------------------------------------------------
    # Expiry policies
    # ---------------------------------------------------------
    start = time.perf_counter()
    expiry_policies = load_expiry_policies(
        today,
        today + timedelta(days=2),
    )
    # ---------------------------------------------------------
    # Separate expiry policies by day
    # ---------------------------------------------------------
    expiry_today = []
    expiry_tomorrow = []
    expiry_day_after = []
    tomorrow = today + timedelta(days=1)
    day_after = today + timedelta(days=2)
    for policy in expiry_policies:
        if policy.end_date == today:
            expiry_today.append(policy)
        elif policy.end_date == tomorrow:
            expiry_tomorrow.append(policy)
        elif policy.end_date == day_after:
            expiry_day_after.append(policy)
    # ---------------------------------------------------------
    # Total
    # ---------------------------------------------------------
    # ---------------------------------------------------------
    # Return
    # ---------------------------------------------------------
    return {
        "today": today,
        "latest_update_date": latest_update_date,
        "customer_count": customer_count,
        "policy_count": performance["policy_count"],
        "production": performance["net_sales"],
        "expiry_today": expiry_today,
        "expiry_tomorrow": expiry_tomorrow,
        "expiry_day_after": expiry_day_after,
        "sales_by_insurance_type": (
            performance["sales_by_insurance_type"]
        ),
    }