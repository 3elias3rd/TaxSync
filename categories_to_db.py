from models import Category
from models import SessionLocal

db = SessionLocal()

def seed_categories():
    if db.query(Category).count() == 0:

        categories = [
            Category(
            name="client_entertainment",
            deductible_pct=0.5
            ),
            Category(
            name="rent_and_utilities",
            deductible_pct=1.0
            ),
            Category(
            name="marketing_and_ads",
            deductible_pct=1.0
            ),
            Category(
            name="salaries_and_visas",
            deductible_pct=1.0
            ),
            Category(
            name="fines_and_penalties",
            deductible_pct=0
            )
        ]

    db.add_all(categories)
    db.commit()
    db.close()

    return {"status": "Categories successfuly seeded"}

if db.query(Category).count() == 0:
    seed_categories()