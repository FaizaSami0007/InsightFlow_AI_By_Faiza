import asyncio
import sqlite3
import os
from app.database.session import async_session_factory
from app.users.service import get_user_by_email, create_user
from app.users.schemas import UserCreate

def check_sqlite_schema():
    for db_file in ["insightflow.db", "test.db"]:
        if os.path.exists(db_file):
            conn = sqlite3.connect(db_file)
            cur = conn.cursor()
            try:
                cur.execute("PRAGMA table_info(users)")
                cols = [c[1] for c in cur.fetchall()]
                if cols and "role" not in cols:
                    print(f"Adding role column to users table in {db_file}...")
                    cur.execute("ALTER TABLE users ADD COLUMN role VARCHAR(32) DEFAULT 'admin'")
                    conn.commit()
            except Exception as e:
                print(f"Error checking {db_file}: {e}")
            finally:
                conn.close()

async def ensure_demo_user():
    async with async_session_factory() as session:
        user = await get_user_by_email(session, "demo@insightflow.ai")
        if not user:
            user = await create_user(
                session,
                UserCreate(
                    email="demo@insightflow.ai",
                    password="DemoPassword123!",
                    full_name="Demo Analyst"
                )
            )
            print("Demo user created successfully: demo@insightflow.ai / DemoPassword123!")
        else:
            print("Demo user already exists: demo@insightflow.ai")

if __name__ == "__main__":
    check_sqlite_schema()
    asyncio.run(ensure_demo_user())
