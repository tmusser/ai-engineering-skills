import io
import unittest
from contextlib import redirect_stdout

from discount_cli import main


class DiscountCliTest(unittest.TestCase):
    def test_limit_truncates_rows(self):
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            code = main(["--limit", "2"])

        self.assertEqual(code, 0)
        self.assertEqual(
            stdout.getvalue().splitlines(),
            [
                "sku | discount",
                "SKU-100 | 10%",
                "SKU-200 | 15%",
            ],
        )
