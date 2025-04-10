from django.core.exceptions import ValidationError
import qrcode  
from io import BytesIO  
from django.http import HttpResponse  
from django.shortcuts import render, reverse  
from django.conf import settings  
import urllib.parse  

def generate_deposit_qrcode(number):
        deposit_url_path = reverse('deposit_number', args=[number])
        full_url = urllib.parse.urljoin(settings.BASE_URL, deposit_url_path)
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(full_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, 'PNG')
        buffer.seek(0)
        return buffer
    


def generate_qrcode(data):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, 'PNG')
        buffer.seek(0)
        return buffer
    
