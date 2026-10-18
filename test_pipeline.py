import json, sys, types
sys.path.insert(0, 'api')
import importlib.util
spec = importlib.util.spec_from_file_location("api_index", "api/index.py")
mod = importlib.util.module_from_spec(spec)

# stub the groq call before module load uses it (module only defines functions; no call at import)
spec.loader.exec_module(mod)

real_bill_extraction = {
  "vendor": "Madhya Pradesh Madhya Kshetra Vidyut Vitaran Co. Ltd.",
  "bill_month": "September-2026",
  "items": [
    {"label": "Energy Charges 71 x 10.29", "units": 71, "rate": 10.29, "base": None, "pct": None, "amount": 730.59},
    {"label": "Energy Charges 14 x 10.29", "units": 14, "rate": 10.29, "base": None, "pct": None, "amount": 144.06},
    {"label": "Additional Energy Charges 7 x 10.29", "units": 7, "rate": 10.29, "base": None, "pct": None, "amount": 72.03},
    {"label": "Additional Energy Charges 408 x 10.29", "units": 408, "rate": 10.29, "base": None, "pct": None, "amount": 4198.32},
    {"label": "FPPAS on Energy Charges", "units": None, "rate": None, "base": 874.65, "pct": 0.0459, "amount": 40.15},
    {"label": "FPPAS on Additional Energy Charges", "units": None, "rate": None, "base": 4270.35, "pct": 0.0459, "amount": 196.01},
    {"label": "Electricity Duty", "units": None, "rate": None, "base": 5381.16, "pct": 0.12, "amount": 646.00},
    {"label": "RKVAH Charges", "units": None, "rate": None, "base": 5660, "pct": 0.27, "amount": 1528.20}
  ],
  "rebate": 32.75, "roundoff": 0.39, "net_payable": 7523.00,
  "total_units": 500, "kwh": 500, "kvah": 600,
  "contract_kva": 1, "billing_kva": 7, "tod_parts": [300, 40, 20, 140],
  "due_date": "22-OCT-2026", "amount_after_due": 7617.00
}
mod.extract = lambda _: real_bill_extraction
mod.build_message = lambda *a, **k: "DRAFT MESSAGE (stubbed)"
out = mod.check(mod.CheckIn(bill_text=open('/home/sandbox/bill.txt').read(), promise="test"))
assert out["vendor"].startswith("Madhya Pradesh"), out["vendor"]
assert out["verdict"] == "2 line(s) worth asking about.", out["verdict"]
assert len(out["checks"]) == 12, len(out["checks"])
assert out["message"] == "DRAFT MESSAGE (stubbed)"
print("pipeline wiring ok:", out["verdict"], "| checks:", len(out["checks"]), "| message stubbed")
