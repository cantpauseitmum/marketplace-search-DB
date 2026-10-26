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

if __name__ == "__main__":
    unittest.main()
