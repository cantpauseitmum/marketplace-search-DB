"""
Unit tests for DatabaseManager
"""
import unittest
import os
try:
    from db_manager import DatabaseManager
except ImportError:
    from database.db_manager import DatabaseManager

class TestDatabaseManager(unittest.TestCase):
    def setUp(self):
        self.test_db = "test_marketplace.db"
        self.db = DatabaseManager(self.test_db)

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_schema_creation(self):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            self.assertIn("search_queries", tables)
            self.assertIn("offers", tables)
            self.assertIn("scraper_logs", tables)

    def test_record_search_query(self):
        q_id = self.db.record_search_query("Switch 2", "Warszawa", 25)
        self.assertGreater(q_id, 0)
        history = self.db.get_search_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["query_text"], "Switch 2")

    def test_upsert_and_deduplication(self):
        offer = {
            "source": "OLX",
            "url": "https://www.olx.pl/d/oferta/test-1",
            "title": "Nintendo Switch 2",
            "price": 1800.0,
            "location": "Warszawa",
        }
        id1 = self.db.upsert_offer(offer)
        self.assertGreater(id1, 0)

        # Update price on duplicate
        offer["price"] = 1750.0
        id2 = self.db.upsert_offer(offer)
        self.assertEqual(id1, id2)

        res = self.db.get_offers(query="Switch 2")
        self.assertEqual(res["total"], 1)
        self.assertEqual(res["items"][0]["price"], 1750.0)

    def test_bookmarks(self):
        offer = {
            "source": "Allegro",
            "url": "https://allegro.pl/oferta/test-bm",
            "title": "PS5 Pro",
            "price": 3200.0,
        }
        offer_id = self.db.upsert_offer(offer)
        self.assertTrue(self.db.toggle_bookmark(offer_id))
        self.assertFalse(self.db.toggle_bookmark(offer_id))

    def test_watchlist_crud_and_export(self):
        # 1. Dodanie do listy monitorowanych (co 1h)
        item = self.db.add_watched_search(
            query_text="Nintendo Switch 2",
            location="Poznań",
            radius_km=25,
            search_in_description=True,
            min_price=1000.0,
            max_price=2000.0,
            sources=["OLX", "Allegro Lokalnie"],
            title="Switch 2 Konsola",
            sort_by="price_asc",
            interval_seconds=3600,
        )
        self.assertIsNotNone(item)
        watched_id = item["id"]
        self.assertGreater(watched_id, 0)
        self.assertEqual(item["title"], "Switch 2 Konsola")
        self.assertEqual(item["location"], "Poznań")
        self.assertEqual(item["radius_km"], 25)
        self.assertEqual(item["sources"], ["OLX", "Allegro Lokalnie"])

        # 2. Pobranie listy monitorowanych
        active_items = self.db.get_watched_searches(active_only=True)
        self.assertGreaterEqual(len(active_items), 1)
        found = any(it["id"] == watched_id for it in active_items)
        self.assertTrue(found)

        # 3. Zapisanie ofert powiązanych z monitorowanym zapytaniem
        offer = {
            "source": "OLX",
            "url": "https://www.olx.pl/d/oferta/switch-2-poz",
            "title": "Nowy Nintendo Switch 2 Folia",
            "price": 1499.0,
            "location": "Poznań",
            "watched_search_id": watched_id,
        }
        self.db.upsert_offer(offer, watched_search_id=watched_id)
        self.db.update_watched_search_result(watched_id, 1)

        # 4. Pobranie ofert dla wybranego przedmiotu z listy
        watched_res = self.db.get_offers_for_watched_search(watched_id)
        self.assertEqual(watched_res["total"], 1)
        self.assertEqual(watched_res["items"][0]["title"], "Nowy Nintendo Switch 2 Folia")
        self.assertEqual(watched_res["watched"]["title"], "Switch 2 Konsola")

        # 5. Usunięcie z listy automatycznej
        deleted = self.db.delete_watched_search(watched_id)
        self.assertTrue(deleted)
        self.assertIsNone(self.db.get_watched_search(watched_id))

if __name__ == "__main__":
    unittest.main()
