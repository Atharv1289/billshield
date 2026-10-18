import os
import requests, gradio as gr

API = os.environ.get("BILLSHIELD_API", "https://billshield-beta.vercel.app/api/check")

def check(bill_text, promise, history):
    if not bill_text.strip():
        return "Paste your bill text first."
    r = requests.post(API, json={"bill_text": bill_text, "promise": promise}, timeout=120)
    d = r.json()
    lines = [d["verdict"], ""]
    for c in d["checks"]:
        mark = "OK " if c["status"] == "pass" else "ASK"
        lines.append(f"[{mark}] {c['label']}: expected {c['expected']}, bill says {c['actual']}")
    lines += ["", "Message you can send:", d["message"]]
    return "\n".join(lines)

gr.ChatInterface(
    fn=check,
    title="BillShield",
    description="Paste your bill text and what you were promised (keep personal details out of the promise box). The maths is recomputed by code; the AI only reads and writes.",
    textbox=gr.Textbox(placeholder="Paste bill text here...", lines=6),
    additional_inputs=[gr.Textbox(label="What were you promised?", placeholder="e.g. a fixed solar rate of Rs 10/unit")],
).launch()
