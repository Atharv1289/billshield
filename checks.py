"""All rupee maths lives here. The AI extracts line items; code verifies them.
A check result is a dict: {kind, status: pass|flag, label, expected, actual, note}"""

TOL = 0.5  # rupees

def _close(a, b, tol=TOL):
    try:
        return abs(float(a) - float(b)) <= tol
    except (TypeError, ValueError):
        return False

def check_line_arithmetic(item):
    """units x rate == amount, when all three are present."""
    u, r, a = item.get("units"), item.get("rate"), item.get("amount")
    if u is None or r is None or a is None:
        return None
    exp = round(float(u) * float(r), 2)
    return {
        "kind": "line_maths",
        "label": item.get("label", "line item"),
        "expected": exp,
        "actual": a,
        "status": "pass" if _close(exp, a) else "flag",
    }

def check_percentage(item):
    """base x pct == amount for charges written like '874.65 * 0.0459'."""
    base, pct, a = item.get("base"), item.get("pct"), item.get("amount")
    if base is None or pct is None or a is None:
        return None
    exp = round(float(base) * float(pct), 2)
    # allow rupee rounding up to 1
    return {
        "kind": "percentage",
        "label": item.get("label", "percentage charge"),
        "expected": exp,
        "actual": a,
        "status": "pass" if _close(exp, a, tol=1.0) else "flag",
    }

def check_total(items, rebate, roundoff, stated_total):
    """sum(charges) - rebate + roundoff == stated net payable."""
    charges = [float(i["amount"]) for i in items
               if i.get("amount") is not None and i.get("counts_toward_total", True)]
    if not charges or stated_total is None:
        return None
    exp = round(sum(charges) - float(rebate or 0) + float(roundoff or 0), 2)
    return {
        "kind": "total",
        "label": "net bill payable",
        "expected": exp,
        "actual": stated_total,
        "status": "pass" if _close(exp, stated_total, tol=1.0) else "flag",
    }

def check_split_sums(label, parts, total):
    """A stated breakdown (like TOD buckets) must sum to the stated total."""
    if not parts or total is None:
        return None
    exp = sum(float(p) for p in parts)
    return {
        "kind": "split_sum",
        "label": label,
        "expected": round(exp, 2),
        "actual": total,
        "status": "pass" if _close(exp, total) else "flag",
    }

def check_power_factor(kwh, kvah):
    """PF = kwh/kvah. Below 0.9 is worth a question to the provider."""
    if not kwh or not kvah:
        return None
    pf = float(kwh) / float(kvah)
    return {
        "kind": "power_factor",
        "label": "power factor (KWH / KVAH)",
        "expected": ">= 0.90",
        "actual": round(pf, 3),
        "status": "pass" if pf >= 0.9 else "flag",
        "note": "A low power factor can mean you pay for capacity you cannot use.",
    }

def check_demand(contract_kva, billing_kva):
    if contract_kva is None or billing_kva is None:
        return None
    ok = float(billing_kva) <= float(contract_kva)
    return {
        "kind": "demand",
        "label": "billing demand vs contract demand",
        "expected": f"<= {contract_kva} KVA",
        "actual": f"{billing_kva} KVA",
        "status": "pass" if ok else "flag",
        "note": "Billing above contract demand is unusual; ask the provider to explain.",
    }

def run_all(items, meta):
    out = []
    for it in items:
        for fn in (check_line_arithmetic, check_percentage):
            r = fn(it)
            if r: out.append(r)
    for r in (check_total(items, meta.get("rebate"), meta.get("roundoff"), meta.get("net_payable")),
              check_split_sums("TOD breakdown", meta.get("tod_parts"), meta.get("total_units")),
              check_power_factor(meta.get("kwh"), meta.get("kvah")),
              check_demand(meta.get("contract_kva"), meta.get("billing_kva"))):
        if r: out.append(r)
    return out
