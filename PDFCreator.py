from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.pdfgen import canvas
from PyPDF2 import PdfReader, PdfWriter
import os

# Register the special font if necessary for Lithuanian characters
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

# Register the font for Lithuanian characters
pdfmetrics.registerFont(TTFont('LithuanianFont', 'dejavu-sans/DejaVuSans.ttf'))

class PDFGenerator:
    def __init__(self, output_path, data, pdf_paths):
        self.output_path = output_path
        self.data = data
        self.pdf_paths = pdf_paths

    def generate_pdf(self):
        # Setup document
        doc = SimpleDocTemplate(self.output_path, pagesize=A4, rightMargin=1 * cm, leftMargin=1 * cm, topMargin=1 * cm, bottomMargin=1 * cm)
        elements = []

        # Define table data and column widths
        data_table = [["Data (Date)", "Mokėjimo rūšis", "Suma (Amount) GBP", "Valiutų kursas* EUR/GBP", "Suma (Amount) EUR"]]
        for row in self.data:
            data_table.append(row)

        # Create table with adjusted font and layout
        table = Table(data_table, colWidths=[3 * cm, 4 * cm, 3 * cm, 4 * cm, 3 * cm])
        table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'LithuanianFont'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'LithuanianFont'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
        ]))

        elements.append(table)

        # Build the PDF content
        doc.build(elements, onFirstPage=self.add_pdf_background, onLaterPages=self.add_pdf_background)

        # After generating the main PDF, merge with the original PDFs
        self.merge_with_original_pdfs()

    def add_pdf_background(self, canvas, doc):
        """
        Adds a title or background info to each page.
        """
        canvas.setFont('LithuanianFont', 12)
        canvas.drawString(100, 820, "Financial Data with Lithuanian Characters Support")

    def merge_with_original_pdfs(self):
        """
        Merges the generated PDF with the original PDFs.
        """
        writer = PdfWriter()

        # First, add the generated PDF content
        with open(self.output_path, 'rb') as generated_pdf:
            reader = PdfReader(generated_pdf)
            for page in range(len(reader.pages)):
                writer.add_page(reader.pages[page])

        # Now, append each of the original PDFs
        for pdf_path in self.pdf_paths:
            with open(pdf_path, 'rb') as original_pdf:
                reader = PdfReader(original_pdf)
                for page in range(len(reader.pages)):
                    writer.add_page(reader.pages[page])

        # Write the final combined output
        with open(self.output_path, 'wb') as output_pdf:
            writer.write(output_pdf)

# Example usage
output_pdf = "final_output2.pdf"
original_pdfs = ['Student Finance Account _ 21-22.pdf', 'Student Finance Account _ 22-23.pdf']

# Example data for the table
data = [
    ["10/01/2022", "Repayment", "7.00", "0.83398", "5.83786"],
    ["10/02/2022", "Repayment", "7.00", "0.84248", "5.89736"],
    # Add more rows as needed
]

# Initialize and generate the PDF
pdf_generator = PDFGenerator(output_pdf, data, original_pdfs)
pdf_generator.generate_pdf()
