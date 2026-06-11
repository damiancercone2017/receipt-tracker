import anthropic
import base64
import json
import re
from PIL import Image
import io

SYSTEM_PROMPT = """You are a receipt data extraction assistant.
Extract exactly these fields from the receipt image or document:
  date, vendor, category, amount, payment_method, notes

Category must be one of:
  Meals | Office Supplies | Travel | Software | Utilities | Other

Return ONLY valid JSON. No markdown, no explanation, no code fences.
If a field cannot be determined, return null for that field and set confidence to "low", otherwise "high".

Schema:
{
  "date": "MM/DD/YYYY or null",
  "vendor": "string or null",
  "category": "string",
  "amount": number or null,
  "payment_method": "string or null",
  "notes": "string or null",
  "confidence": "high" or "low"
}"""


def extract_from_file(file_bytes: bytes, filename: str, api_key: str) -> dict:
    client = anthropic.Anthropic(api_key=api_key)
    ext = filename.lower().split(".")[-1]

    if ext == "pdf":
        image_data = _pdf_to_image(file_bytes)
        media_type = "image/png"
    else:
        image_data = base64.standard_b64encode(file_bytes).decode("utf-8")
        media_type = "image/jpeg" if ext in ("jpg", "jpeg") else "image/png"

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                    {"type": "text", "text": "Extract the expense data from this receipt."},
                ],
            }
        ],
    )

    raw = message.content[0].text.strip()
    raw = re.sub(r"^```(?:json)?", "", raw).strip()
    raw = re.sub(r"```$", "", raw).strip()
    result = json.loads(raw)
    result["source_file"] = filename
    return result


def _pdf_to_image(pdf_bytes: bytes) -> str:
    try:
        import pdf2image
        images = pdf2image.convert_from_bytes(pdf_bytes, first_page=1, last_page=1)
        buf = io.BytesIO()
        images[0].save(buf, format="PNG")
        return base64.standard_b64encode(buf.getvalue()).decode("utf-8")
    except Exception:
        # Fallback: pass raw PDF as base64 document block handled in caller
        raise RuntimeError("pdf2image unavailable — please upload receipt as JPG or PNG")
