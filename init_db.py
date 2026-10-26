"""
CLI tool for MarketplaceSearch Database
"""
import argparse
import sys
import os
from db_manager import DatabaseManager, DEFAULT_DB_PATH

def main():
    parser = argparse.ArgumentParser(description="MarketplaceSearch Database Manager CLI")
    parser.add_argument("--init", action="store_true", help="Initialize database schema")
    parser.add_argument("--seed", action="store_true", help="Seed initial test data")
    parser.add_argument("--db", type=str, default=DEFAULT_DB_PATH, help="Path to SQLite database file")
    parser.add_argument("--stats", action="store_true", help="Show database statistics")
    parser.add_argument("--reset", action="store_true", help="Delete existing database and re-initialize")

    args = parser.parse_args()

    if args.reset:
        if os.path.exists(args.db):
            os.remove(args.db)
            print(f"🗑️ Removed database at {args.db}")

    db = DatabaseManager(args.db)
    print(f"✅ Database initialized at: {db.db_path}")

    if args.seed:
        db.seed_initial_data()
        print("🌱 Seed data populated successfully!")

    if args.stats or (not args.init and not args.seed and not args.reset):
        offers = db.get_offers(limit=1)
        history = db.get_search_history(limit=5)
        print("=" * 50)
        print("📊 MarketplaceSearch DB Statistics")
        print("=" * 50)
        print(f"• Total offers in DB:    {offers['total']}")
        print(f"• Search queries logged: {len(history)}")
        print(f"• Sources represented:   {len(offers.get('sources_stats', []))}")
        for s in offers.get('sources_stats', []):
            print(f"   - {s['source']}: {s['count']} offers")
        print("=" * 50)

if __name__ == "__main__":
    main()
