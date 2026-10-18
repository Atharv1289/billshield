import os, json, base64, re
from pathlib import Path
import requests
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mask import mask_pii
from checks import run_all

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "openai/gpt-oss-120b"

EXTRACT_PROMPT = """You are reading an Indian utility bill. Output ONLY JSON, no markdown, with this shape:
{"vendor": str, "bill_month": str, "items": [{"label": str, "units": number|null, "rate": number|null, "base": number|null, "pct": number|null, "amount": number}], "rebate": number|null, "roundoff": number|null, "net_payable": number, "total_units": number|null, "kwh": number|null, "kvah": number|null, "contract_kva": number|null, "billing_kva": number|null, "tod_parts": [number]|null, "due_date": str|null, "amount_after_due": number|null}
Rules:
- One entry per charge line. Include every charge, tax and duty that adds into the total (energy charges, FPPAS/fuel adjustments, electricity duty, demand charges, surcharges).
- Copy each charge's name VERBATIM from the bill text (e.g. "Electricity Duty", "FPPAS on Energy Charges"). Never use a meter-reading label (like "Transformer Loss" or "Adjustment") for a money line.
- Use units*rate for quantity-priced lines and base*pct for percentage lines.
- Rebate/discount lines go in "rebate" (positive number), not in items. The "roundoff" field takes the round-off adjustment.
- Layout note: the bill is two-column text. A charge's amount is in the right column and its formula (like "71 * 10.29" or "874.65 * 0.0459") is printed just below it. Connect each amount to the formula nearest below it to fill units/rate or base/pct.
- contract_kva comes from the header text "Cont. Demand <n> KVA"; billing_kva from the "Billing Demand" row in the readings table.
- Forbidden labels for money lines: Transformer Loss, Adjustment, Billing Demand, Max Demand, Reading, KWH, KVAH, TOD. If the true name is ambiguous, reuse the nearest charge-like name above the amount (e.g. "Additional Energy Charges").
- Never invent a number not printed on the bill."""

MESSAGE_PROMPT = """You write short, polite messages from a customer to their utility provider about their bill. Use only the facts given below. Never state any amount that is not listed. If the facts say everything checks out, the message instead thanks them and asks to keep the account details updated. Plain text, no markdown, under 120 words, no placeholders."""

def groq(messages, max_tokens=8192):
    import time
    body = {"model": MODEL, "messages": messages, "max_tokens": max_tokens,
            "temperature": 0.1}
    for attempt in range(4):
        r = requests.post(GROQ_URL, headers={"Authorization": f"Bearer {os.environ['GROQ_API_KEY']}"}, json=body, timeout=120)
        if r.status_code == 429:
            time.sleep(5 * (attempt + 1))   # free tier TPM limit; wait and retry
            continue
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    r.raise_for_status()

def parse_json(text):
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0)) if m else {}

def extract(bill_text_masked: str) -> dict:
    content = EXTRACT_PROMPT + "\n\nBILL:\n" + bill_text_masked
    raw = groq([{"role": "user", "content": content}])
    return parse_json(raw)

def build_message(vendor, promise, flags, passes, amounts):
    facts = {
        "vendor": vendor,
        "what_the_customer_was_promised": promise,
        "problems_found": [f for f in flags],
        "checks_that_passed": len(passes),
        "amounts_from_the_bill": amounts,
    }
    return groq([{"role": "user", "content": MESSAGE_PROMPT + "\n\nFACTS:\n" + json.dumps(facts, indent=2)}])

app = FastAPI()

class CheckIn(BaseModel):
    bill_text: str          # plain text of the bill (PDF-extracted or pasted)
    promise: str = ""       # what the customer was promised / expects

@app.post("/api/check")
def check(body: CheckIn):
    masked = mask_pii(body.bill_text)                 # 1. identity never reaches the model
    data = extract(masked)                            # 2. AI reads structure only
    items = data.get("items", [])
    results = run_all(items, data)                    # 3. code recomputes every rupee
    flags = [r for r in results if r["status"] == "flag"]
    passes = [r for r in results if r["status"] == "pass"]
    amounts = {"net_payable": data.get("net_payable"),
               "computed_total": next((r["expected"] for r in results if r["kind"] == "total"), None),
               "due_date": data.get("due_date"),
               "amount_after_due": data.get("amount_after_due")}
    message = build_message(data.get("vendor", "the provider"), body.promise, flags, passes, amounts)
    persist(data.get("vendor"), data.get("bill_month"), data.get("net_payable"),
            items, results, message)
    all_good = not flags
    return {
        "vendor": data.get("vendor"),
        "bill_month": data.get("bill_month"),
        "lines": items,
        "checks": results,
        "verdict": "Every line checks out." if all_good else f"{len(flags)} line(s) worth asking about.",
        "message": message,
    }

@app.get("/api/health")
def health():
    return {"ok": True}

# --- optional Supabase persistence (step 08): survives redeploys ---
_supabase = None
def sb():
    global _supabase
    if _supabase is None:
        url, key = os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_SERVICE_KEY")
        if url and key:
            from supabase import create_client
            _supabase = create_client(url, key)
    return _supabase

def persist(vendor, bill_month, net_payable, items, results, message):
    client = sb()
    if client is None:
        return
    bill = client.table("bills").insert({"user_id": 1, "vendor": vendor,
        "bill_month": bill_month, "net_payable": net_payable}).execute().data[0]
    status = {r["label"]: r["status"] for r in results}
    flagged_first = None
    for it in items:
        row = {"bill_id": bill["id"], "label": it.get("label"),
               "units": it.get("units"), "rate": it.get("rate"),
               "amount": it.get("amount"),
               "check_status": status.get(it.get("label"), "pass")}
        inserted = client.table("line_items").insert(row).execute().data[0]
        if flagged_first is None and row["check_status"] == "flag":
            flagged_first = inserted
    if flagged_first is not None:
        client.table("messages").insert({"line_item_id": flagged_first["id"],
            "body": message, "sent": False}).execute()
