from database import engine
from sqlalchemy import text
with engine.begin() as connection:
    connection.execute(
        text("""
            CREATE INDEX IF NOT EXISTS ix_collections_policy_id
            ON collections (policy_id)
        """)
    )
    connection.execute(
        text("""
            CREATE INDEX IF NOT EXISTS ix_policies_issue_code
            ON policies (issue_code)
        """)
    )
print("Indexes created successfully.")
