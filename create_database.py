from datetime import date

from database import engine, Base, SessionLocal
from models import CommissionConfig, SystemConfig


def initialize_database():
    # ساخت جداول دیتابیس
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        commission_configs = [
            {
                "effective_date": date(2023, 3, 21),
                "first_step_commission": 12_500_000_000,
                "vat": 0.09,
            },
            {
                "effective_date": date(2024, 3, 20),
                "first_step_commission": 15_000_000_000,
                "vat": 0.10,
            },
            {
                "effective_date": date(2025, 3, 21),
                "first_step_commission": 18_000_000_000,
                "vat": 0.10,
            },
            {
                "effective_date": date(2026, 3, 21),
                "first_step_commission": 21_600_000_000,
                "vat": 0.10,
            },
        ]

        for config_data in commission_configs:
            existing = (
                db.query(CommissionConfig)
                .filter(
                    CommissionConfig.effective_date
                    == config_data["effective_date"]
                )
                .first()
            )

            if not existing:
                db.add(
                    CommissionConfig(
                        effective_date=config_data["effective_date"],
                        first_step_commission=(
                            config_data["first_step_commission"]
                        ),
                        vat=config_data["vat"],
                    )
                )

        existing_system_config = db.query(SystemConfig).first()

        if not existing_system_config:
            db.add(
                SystemConfig(
                current_agent="محسن حاج ميرزاعلي اکبر کد 210412"
                )
            )

        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    initialize_database()
    print("Database created successfully!")
