# BillShield

One confusing bill in, one message worth sending out.

- **Code decides the maths.** Every charge line, percentage, and the final total is recomputed in `checks.py`. The model never states an amount code did not compute.
- **AI reads and writes.** Groq (`openai/gpt-oss-120b`) reads the masked bill text into line items and drafts the message to the provider. "Every line checks out" is a valid answer.
- **Best-effort identity masking before the model.** `mask.py` strips PANs, consumer/account codes, meter numbers, phone numbers, emails, name lines, address lines and PIN codes from the bill text before any AI call. This is a safeguard, not a guarantee: unusual formats can slip through, and the free-text "promise" box is sent as typed, so keep personal details out of it. Check the masked output before sharing results.

## Layout (course repo steps 01-08 shape)
- `api/index.py` - FastAPI: POST /api/check (mask -> extract -> recompute -> message -> persist)
- `checks.py` - all rupee maths: line arithmetic, percentage charges, total, TOD splits, power factor, demand
- `mask.py` - PII masking before any model call
- `public/index.html` - the page (no key in the browser)
- `client/app.py` - Gradio client for local testing
- `schema.sql` - users, bills, line_items, messages (message -> line_item)

## Run locally
```bash
pip install -r requirements.txt
cp .env.example .env   # add GROQ_API_KEY (SUPABASE_* optional)
uvicorn api.index:app --reload
```

## Deploy
Vercel serves `api/` as Python functions and `public/` as the site. Set GROQ_API_KEY (and SUPABASE_URL / SUPABASE_SERVICE_KEY) as environment variables.
