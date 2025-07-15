import qrcode
from io import BytesIO
import base64
import logging

logger = logging.getLogger(__name__)

def generate_qr_code(data: str, box_size: int = 10) -> str:
    """
    Generate a QR code from data and return as base64 encoded PNG image.
    
    Args:
        data: The data to encode in the QR code
        box_size: The size of each box in the QR code (default: 10)
        
    Returns:
        Base64 encoded PNG image data
    """
    try:
        # Create QR code instance
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=box_size,
            border=4,
        )
        
        # Add data
        qr.add_data(data)
        qr.make(fit=True)
        
        # Create image
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to bytes
        image_buffer = BytesIO()
        qr_image.save(image_buffer, format='PNG')
        image_buffer.seek(0)
        
        # Convert to base64
        base64_image = base64.b64encode(image_buffer.getvalue()).decode()
        
        return base64_image
        
    except Exception as e:
        logger.error(f"Failed to generate QR code: {e}")
        return None

def get_qr_code_html(data: str, box_size: int = 10) -> str:
    """
    Generate HTML img tag with base64 encoded QR code.
    
    Args:
        data: The data to encode in the QR code
        box_size: The size of each box in the QR code (default: 10)
        
    Returns:
        HTML img tag with base64 encoded QR code
    """
    qr_base64 = generate_qr_code(data, box_size)
    if qr_base64:
        return f'<img src="data:image/png;base64,{qr_base64}" alt="QR Code" />'
    return None 