from billing.invoice import legacy_round


def monthly_total(rows):
    return legacy_round(sum(r.amount for r in rows))
