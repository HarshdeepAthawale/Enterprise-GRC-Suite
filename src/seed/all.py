import asyncio
from src.core.database import async_session, engine
from src.models.base import Base
from src.seed.import_nist_csf import import_nist_csf
from src.models.risk import RiskMatrix
from src.core.security import hash_password
from src.models.user import User
from sqlalchemy import select

DEFAULT_MATRIX_DATA = {
    "likelihood": ["Rare", "Unlikely", "Possible", "Likely", "Almost Certain"],
    "impact": ["Insignificant", "Minor", "Moderate", "Major", "Critical"],
    "grid": [
        [1, 2, 3, 4, 5],
        [2, 4, 6, 8, 10],
        [3, 6, 9, 12, 15],
        [4, 8, 12, 16, 20],
        [5, 10, 15, 20, 25],
    ],
}


async def seed_all():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_session() as db:
        # 1. Create admin user if not exists
        result = await db.execute(select(User).where(User.email == "admin@grcsuite.com"))
        if not result.scalar_one_or_none():
            admin = User(
                email="admin@grcsuite.com",
                display_name="Admin",
                hashed_password=hash_password("admin123"),
                role="admin",
            )
            db.add(admin)
            print("Created admin user: admin@grcsuite.com / admin123")
        else:
            print("Admin user already exists")

        # 2. Import NIST CSF 2.0
        await import_nist_csf(db)

        # 3. Create default risk matrix
        result = await db.execute(select(RiskMatrix).limit(1))
        if not result.scalar_one_or_none():
            matrix = RiskMatrix(
                name="Default 5x5",
                likelihood_labels=DEFAULT_MATRIX_DATA["likelihood"],
                impact_labels=DEFAULT_MATRIX_DATA["impact"],
                matrix=DEFAULT_MATRIX_DATA["grid"],
            )
            db.add(matrix)
            print("Created default risk matrix")
        else:
            print("Risk matrix already exists")

        await db.commit()
        print("Seed complete")


if __name__ == "__main__":
    asyncio.run(seed_all())
