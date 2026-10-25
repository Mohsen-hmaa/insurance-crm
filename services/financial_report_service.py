from database import SessionLocal
from models import Collection, Policy
from sqlalchemy.orm import joinedload
from services.date_service import convert_shamsi_to_date
COLLECTION_RECEIPT_TYPES = (
    "پيش دريافتي",
    "صندوق"
)
def _get_collections(
    from_date_shamsi,
    to_date_shamsi,
    receipt_types=None
):
    """
    وصولی‌های یک بازه‌ی تاریخی (بر اساس تاریخ وصول).
    اگر receipt_types داده شود فقط همان نوع‌های دریافتی برمی‌گردند؛
    اگر None باشد، همه‌ی نوع‌های دریافتی لحاظ می‌شوند.
    """
    from_date = convert_shamsi_to_date(from_date_shamsi)
    to_date = convert_shamsi_to_date(to_date_shamsi)
    if not from_date or not to_date:
        return []
    if from_date > to_date:
        return []
    with SessionLocal() as session:
        query = (
            session.query(Collection)
            .options(
                joinedload(Collection.policy).joinedload(Policy.customer),
                joinedload(Collection.policy).joinedload(Policy.insurance_type),
                joinedload(Collection.policy).joinedload(Policy.marketer),
            )
            .filter(
                Collection.collection_date >= from_date,
                Collection.collection_date <= to_date,
            )
        )
        if receipt_types:
            query = query.filter(
                Collection.receipt_type.in_(receipt_types)
            )
        return (
            query
            .order_by(
                Collection.collection_date,
                Collection.id
            )
            .all()
        )
def get_collection_financial_report(
    from_date_shamsi,
    to_date_shamsi
):
    """پرداختی‌ها از صندوق و پیش‌دریافتی."""
    return _get_collections(
        from_date_shamsi,
        to_date_shamsi,
        COLLECTION_RECEIPT_TYPES
    )
def get_total_payments_report(
    from_date_shamsi,
    to_date_shamsi
):
    """کل پرداختی‌ها (همه‌ی نوع‌های دریافتی) در یک بازه‌ی تاریخ وصول."""
    return _get_collections(
        from_date_shamsi,
        to_date_shamsi
    )
