"""
seed.py
One-time script to populate MongoDB Atlas with sample products and an admin user.
Run with: python seed.py
"""

from app import create_app
from services.product_service import seed_products
from services.user_service import seed_admin

app = create_app()

with app.app_context():
    print("🌱 Seeding admin user...")
    seed_admin(email='admin@pickles.com', password='Admin@1234')
    print("   ✅ Admin ready → email: admin@pickles.com | password: Admin@1234")

    print("\n🌱 Seeding sample products...")
    seed_products()
    print("   ✅ 12 products added (Pickles, Snacks, Combos, Gift Packs)")

    print("\n🎉 Database seeded successfully! Run 'python app.py' to start the shop.")
