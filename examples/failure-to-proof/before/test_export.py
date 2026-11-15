"""The old suite tests only the normal result path."""

import unittest

from export import export_csv


class ExportTests(unittest.TestCase):
    def test_matching_region_keeps_schema(self) -> None:
        rows = [{"order_id": "42", "region": "west"}, {"order_id": "43", "region": "east"}]
        self.assertEqual(export_csv(rows, "west"), "order_id,region\n42,west\n")


if __name__ == "__main__":
    unittest.main()
