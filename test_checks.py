from checks import run_all

# The real MPMKVVCL Sept 2026 bill numbers
items = [
    {"label": "Energy Charges 71 x 10.29", "units": 71, "rate": 10.29, "amount": 730.59},
    {"label": "Energy Charges 14 x 10.29", "units": 14, "rate": 10.29, "amount": 144.06},
    {"label": "Additional Energy Charges 7 x 10.29", "units": 7, "rate": 10.29, "amount": 72.03},
    {"label": "Additional Energy Charges 408 x 10.29", "units": 408, "rate": 10.29, "amount": 4198.32},
    {"label": "FPPAS on Energy Charges 874.65 x 0.0459", "base": 874.65, "pct": 0.0459, "amount": 40.15},
    {"label": "FPPAS on Additional Energy Charges 4270.35 x 0.0459", "base": 4270.35, "pct": 0.0459, "amount": 196.01},
    {"label": "Electricity Duty 5381.16 x 12%", "base": 5381.16, "pct": 0.12, "amount": 646.00},
    {"label": "RKVAH Charges 5660 x 0.27", "base": 5660, "pct": 0.27, "amount": 1528.20},
]
meta = {"rebate": 32.75, "roundoff": 0.39, "net_payable": 7523.00,
        "tod_parts": [300, 40, 20, 140], "total_units": 500,
        "kwh": 500, "kvah": 600, "contract_kva": 1, "billing_kva": 7}

results = run_all(items, meta)
for r in results:
    print(f"{r['status'].upper():5} {r['kind']:12} {r['label'][:50]:52} expected={r['expected']} actual={r['actual']}")
flags = [r for r in results if r["status"] == "flag"]
print(f"\n{len(results)} checks, {len(flags)} flags")
assert len(flags) == 2, "expected exactly power factor + demand flags"
# negative test: corrupt one amount, expect a flag
items[0]["amount"] = 999.00
r2 = run_all(items, meta)
assert any(x["kind"] == "line_maths" and x["status"] == "flag" for x in r2), "corrupt line not caught"
assert any(x["kind"] == "total" and x["status"] == "flag" for x in r2), "corrupt total not caught"
print("negative tests pass")
