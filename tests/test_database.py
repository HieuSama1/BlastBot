import unittest
from datetime import timedelta

from utils.database import LRUCache


class LRUCacheTests(unittest.TestCase):
    def test_get_returns_copy_and_evicts_oldest(self):
        cache = LRUCache(maxsize=2, ttl_seconds=60)

        value = {"points": 5}
        cache.set(1, value)
        value["points"] = 10

        self.assertEqual(cache.get(1), {"points": 5})

        cache.set(2, {"points": 2})
        cache.set(3, {"points": 3})

        self.assertIsNone(cache.get(1))
        self.assertEqual(cache.get(2), {"points": 2})
        self.assertEqual(cache.get(3), {"points": 3})

    def test_get_expires_entries(self):
        cache = LRUCache(maxsize=2, ttl_seconds=1)
        cache.set(1, {"points": 1})
        cache.timestamps[1] = cache.timestamps[1] - timedelta(seconds=2)

        self.assertIsNone(cache.get(1))


if __name__ == "__main__":
    unittest.main()