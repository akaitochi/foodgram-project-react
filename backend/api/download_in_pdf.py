import io

from django.http import FileResponse
from foodgram.settings import FONTS_FILES_DIR
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


def create_pdf_file(request):
    # Устанавливаем шрифты
    pdfmetrics.registerFont(
        TTFont('Helvetica', FONTS_FILES_DIR, 'UTF-8')
    )
    # Создаём буфер
    buf = io.BytesIO()
    # Создаём канвас
    pdf = canvas.Canvas(buf, pagesize=letter, bottomup=0)
    # Создаём строковый объект
    pdf.translate(cm, cm)
    pdf.setFont('Helvetica', 18)
    pdf.drawString(200, 5, 'Список покупок:')
    pdf.setFont('Helvetica', 14)
    down_param = 20
    for number, ingredient in enumerate(request, start=1):
        pdf.drawString(
            10,
            down_param,
            f"{number}. {ingredient['ingredient__name']}, "
            f"{ingredient['total_ingredient_amount']} "
            f"{ingredient['ingredient__measurement_unit']}.",
        )
        down_param += 20
        if down_param >= 780:
            down_param = 20
            pdf.showPage()
            pdf.setFont('Helvetica', 16)
    pdf.showPage()
    pdf.save()
    buf.seek(0)
    return FileResponse(
        buf,
        as_attachment=True,
        filename='shopping_list.pdf'
    )
