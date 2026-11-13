def format_amount(cents: int) -> str:
    return f"{cents:.2f}"


def legacy_round(value: float) -> int:
    """Round half up, the way the 2019 reports did."""
    return int(value + 0.5)
