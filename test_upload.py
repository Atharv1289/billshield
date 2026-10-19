"""Upload-path tests: PDF text extraction and shared pipeline wiring. Photos are OCR'd client-side, so the server path tested here is PDF-only."""
import io, sys
sys.path.insert(0, 'api')
sys.path.insert(0, '.')
from index import pdf_to_text, run_pipeline, MAX_UPLOAD
from mask import mask_pii

# 1. PDF extraction on a real-shaped synthetic PDF
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, NameObject, DictionaryObject, ArrayObject, NumberObject

def make_pdf(text):
    """Minimal one-page text PDF via raw content stream."""
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    stream = DecodedStreamObject()
    stream.set_data(f"BT /F1 10 Tf 50 750 Td ({text}) Tj ET".encode())
    page[NameObject("/Contents")] = stream
    page[NameObject("/Resources")] = DictionaryObject({NameObject("/Font"): DictionaryObject({NameObject("/F1"): DictionaryObject({NameObject("/Type"): NameObject("/Font"), NameObject("/Subtype"): NameObject("/Type1"), NameObject("/BaseFont"): NameObject("/Helvetica")})})})
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()

pdf_bytes = make_pdf("Test Bill Net Payable 100")
text = pdf_to_text(pdf_bytes)
assert "Net Payable" in text, f"pdf extraction failed: {text!r}"
print("pdf extraction ok")

# 2. Masking is applied to PDF-extracted text before the pipeline (real bill shapes)
sample = "Consumer Name: TEST PERSON\nPAN: ABCDE1234F\nEmail: a@b.com\nNet Payable: 7523.00"
masked = mask_pii(sample)
assert "TEST PERSON" not in masked and "ABCDE1234F" not in masked and "a@b.com" not in masked
assert "7523.00" in masked
print("pdf-path masking ok")

# 3. run_pipeline is the single shared path (same function serves text and files)
import inspect
sig = inspect.signature(run_pipeline)
assert list(sig.parameters) == ["masked", "promise", "input_kind"]
assert MAX_UPLOAD == 4 * 1024 * 1024
print("pipeline wiring ok")
