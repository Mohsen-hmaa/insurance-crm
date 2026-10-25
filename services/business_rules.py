from database import SessionLocal
from models import CommissionConfig
INTERNAL_REFERRERS = {
    "شعبه آپادانا کد 110002",
    "مرکز کد 110001",
}
VAT_EXEMPT_TYPES = {
    "درمان گروهي",
    "عمر",
    "عمر و پس انداز",
    "عمر گروهي",
    "مسافرتي خارج از كشور",
}
def get_commission_config_by_date(issue_date):
    db = SessionLocal()
    try:
        return (
            db.query(CommissionConfig)
            .filter(
                CommissionConfig.effective_date <= issue_date
            )
            .order_by(
                CommissionConfig.effective_date.desc()
            )
            .first()
        )
    finally:
        db.close()