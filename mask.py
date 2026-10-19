import re

# Best-effort PII masking applied to bill text BEFORE any AI call.
# Known limits: only the patterns below are masked. Free-text the user types
# (e.g. the promise field) is sent as-is, so the UI tells users not to put
# personal details there. Masking is a safeguard, not a guarantee.

def mask_pii(text: str) -> str:
    t = text
    # Email (any case)
    t = re.sub(r'\b[\w.+-]+@[\w-]+\.[\w.]+\b', '[EMAIL MASKED]', t, flags=re.IGNORECASE)
    # PAN: 5 letters + 4 digits + 1 letter (synthetic example: ABCDE1234F), any case
    t = re.sub(r'\b[A-Z]{5}[0-9]{4}[A-Z]\b', '[PAN MASKED]', t, flags=re.IGNORECASE)
    # Consumer / account codes: 1-2 letters followed by 8-12 digits (synthetic example: X0000000000)
    t = re.sub(r'\b[A-Z]{1,2}\d{8,12}\b', '[CONSUMER CODE MASKED]', t, flags=re.IGNORECASE)
    # Long numeric account / consumer numbers (11-16 digits)
    t = re.sub(r'\b\d{11,16}\b', '[ACCOUNT NO MASKED]', t)
    # Meter numbers: 1-2 letters + 6-8 digits (synthetic example: Z000000)
    t = re.sub(r'\b[A-Z]{1,2}\d{6,8}\b', '[METER NO MASKED]', t, flags=re.IGNORECASE)
    # Phone numbers: 10-digit Indian mobiles, +91 prefixed, or partially masked like ******0000
    t = re.sub(r'\+91[\s-]?\d{10}', '[PHONE MASKED]', t)
    t = re.sub(r'\*{3,}\d{4}', '[PHONE MASKED]', t)
    t = re.sub(r'\b[6-9]\d{9}\b', '[PHONE MASKED]', t)
    # Labeled name lines: "Name: ..." / "NAME ..."
    t = re.sub(r'(?im)^\s*(consumer\s+)?name\s*[:\-]\s*.+$', '[NAME MASKED]', t)
    # Address blocks: lines with address keywords or "Address: ..."
    t = re.sub(r'(?im)^.*\b(village|tehsil|taluka|district|dist|ward|road|street|nagar|colony|pin\s*code?)\b.*$', '[ADDRESS MASKED]', t)
    t = re.sub(r'(?im)^\s*address\s*[:\-]\s*.+$', '[ADDRESS MASKED]', t)

    # Long mixed alphanumeric tokens (14+ chars with letters and digits): virtual account
    # numbers and IDs that can embed consumer codes (synthetic example: AB0000X0000000000)
    t = re.sub(r'\b(?=[A-Z0-9]*[A-Z])(?=[A-Z0-9]*\d)[A-Z0-9]{14,}\b', '[ACCOUNT NO MASKED]', t)
    # Name before a consumer-code label on the same line
    t = re.sub(r'(?im)^[^\n]*?(\bCons\.?\s*Code\b)', '[NAME MASKED] \\1', t)
    # Feeder / division / subdivision names identify the location: mask their values
    t = re.sub(r'(?im)(\b(?:feeder|division|sub\s*division)\s*name\s*:?)\s*\S.*?(?=\s{3,}|$)', '\\1 [LOCATION MASKED]', t)
    # Loc/circle codes and circle names identify the area
    t = re.sub(r'(?im)(\bcircle\s*:?)\s*\S+', '\\1 [LOCATION MASKED]', t)
    t = re.sub(r'(?i)\bloc\s*code\s*\d+', 'Loc Code [LOCATION MASKED]', t)
    # PIN-led address lines (start with a 6-digit code)
    t = re.sub(r'(?im)^\s*\d{6}\s+\D.*$', '[ADDRESS MASKED]', t)
    # PIN codes
    t = re.sub(r'\b[1-9]\d{5}\b', '[PIN MASKED]', t)
    # Standalone ALL-CAPS personal-name lines (PDF text extraction scrambles
    # two-column layouts, so the name can land on its own line)
    t = _mask_caps_name_lines(t)
    return t

# Bill vocabulary that keeps a line from being treated as a personal name
_CAPS_KEEP = ('VIDYUT', 'LTD', 'LIMITED', 'COMPANY', 'CORPORATION', 'ELECTRICITY',
              'ENERGY', 'POWER', 'DISCOM', 'BOARD', 'GOVERNMENT', 'BILL', 'INVOICE',
              'NOTICE', 'DATE', 'TOTAL', 'TAX', 'CHARGES', 'MONTH', 'YEAR', 'PAGE',
              'KWH', 'KVAH', 'KVA', 'TOD', 'KV', 'HT', 'LT', 'DUTY', 'RATE', 'UNITS',
              'AMOUNT', 'PAYABLE', 'DEMAND', 'READING', 'CONSUMPTION', 'ADJUSTMENT')

def _mask_caps_name_lines(t):
    """Standalone ALL-CAPS 2-4 word lines (how a consumer name often prints)
    are masked unless they are bill vocabulary."""
    out = []
    for line in t.split('\n'):
        s = line.strip()
        if (5 <= len(s) <= 40 and re.fullmatch(r'[A-Z][A-Z ]{4,}', s)
                and 2 <= len(s.split()) <= 4
                and not any(k in s for k in _CAPS_KEEP)):
            out.append('[NAME MASKED]')
        else:
            out.append(line)
    return '\n'.join(out)


