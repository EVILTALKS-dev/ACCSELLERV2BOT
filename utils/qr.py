import qrcode, io, random
from config import UPI_ID, UPI_NAME

def make_upi_qr(amount: float, order_id: int):
    paise = random.randint(1, 98)
    exact = round(amount + paise / 100, 2)
    upi = (
        f"upi://pay?pa={UPI_ID}&pn={UPI_NAME.replace(' ','%20')}"
        f"&am={exact:.2f}&cu=INR&tn=Order{order_id}"
    )
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
    qr.add_data(upi)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#111111", back_color="#ffffff")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.read(), exact
