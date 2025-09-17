import qrcode
import base64
from io import BytesIO

def generate_event_qr_base64(event):
    url = f"https://your-domain.com/events/{event.id}/"
    qr = qrcode.make(url)

    buffer = BytesIO()
    qr.save(buffer, format="PNG")

    qr_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    event.qr_code_text = qr_base64
    event.save()
