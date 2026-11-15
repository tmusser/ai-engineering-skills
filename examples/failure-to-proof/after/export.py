"""Repaired example: always write the CSV header, even when empty."""

import csv
import io


def export_csv(orders: list[dict[str, str]], region: str) -> str:
    selected = [order for order in orders if order["region"] == region]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=("order_id", "region"), lineterminator="\n")
    writer.writeheader()
    writer.writerows(selected)
    return output.getvalue()
