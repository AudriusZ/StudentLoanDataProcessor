from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from PyPDF2 import PdfMerger
import os

# Register the special font for Lithuanian characters
pdfmetrics.registerFont(TTFont('LithuanianFont', 'dejavu-sans/DejaVuSans.ttf'))

class PDFGenerator:
    def __init__(self, output_path, formatted_data, pdf_paths):
        """
        Initialize the PDFGenerator with the path for output and the formatted data.
        """
        self.output_path = output_path
        self.formatted_data = formatted_data  # Pass the formatted data here
        self.pdf_paths = pdf_paths

    def generate_pdf(self):
        """
        Generate a PDF with the table using the formatted data, and merge with original PDFs.
        """
        # Setup document
        doc = SimpleDocTemplate(self.output_path, pagesize=A4, rightMargin=1 * cm, leftMargin=1 * cm, topMargin=2 * cm, bottomMargin=2 * cm)
        elements = []

        # Create the table
        table = Table(self.formatted_data, colWidths=[3 * cm, 4 * cm, 3 * cm, 4 * cm, 3 * cm])
        table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'LithuanianFont'),  # Ensure proper font for special characters
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'LithuanianFont'),  # Set font for the table
            ('FONTSIZE', (0, 0), (-1, -1), 8),  # Adjust font size for table contents
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
        ]))

        # Add the table to elements
        elements.append(table)

        # Build the PDF
        try:
            doc.build(elements, onFirstPage=self.add_pdf_header, onLaterPages=self.add_pdf_header)
            print(f"PDF successfully generated at {self.output_path}")

            # Now proceed with merging the PDFs
            self.merge_with_original_pdfs()

        except Exception as e:
            print(f"Error during PDF generation: {e}")

    def add_pdf_header(self, canvas, doc):
        """
        Add a header to the PDF pages.
        """
        canvas.setFont('LithuanianFont', 12)
        canvas.drawString(100, 820, "Skaičiavimai:")

    def merge_with_original_pdfs(self):
        """
        Merge the generated PDF with the original PDFs, with error handling for corrupted files.
        """
        # Initialize a PdfMerger
        merger = PdfMerger()

        try:
            # Add the newly generated report
            if os.path.exists(self.output_path):
                merger.append(self.output_path)
            else:
                print(f"Error: Generated PDF {self.output_path} does not exist or is invalid.")
                return  # Stop the process if the generated PDF is invalid

            # Add the original PDFs one by one
            for pdf_path in self.pdf_paths:
                try:
                    if os.path.exists(pdf_path):
                        merger.append(pdf_path)
                    else:
                        print(f"Warning: File {pdf_path} does not exist.")
                except Exception as e:
                    print(f"Error: Could not merge {pdf_path}. Reason: {e}")

            # Write the final output with merged PDFs
            base_name, extension = os.path.splitext(self.output_path)
            merged_output_path = f"{base_name}_su_priedais{extension}"
            with open(merged_output_path, "wb") as output_pdf:
                merger.write(output_pdf)

            print(f"PDF successfully generated and merged at: {merged_output_path}")

        except Exception as e:
            print(f"Error during merging: {e}")
        finally:
            # Close the merger object
            merger.close()


# Example usage of PDFGenerator with formatted data

"""
formatted_data = [
    ['Data', 'Mokėjimo rūšis', 'Suma GBP', 'Valiutų kursas EUR/GBP', 'Suma EUR'],
    ['2022-01-10', 'Repayment', '7.00', 0.83398, 8.39],
    ['2022-02-10', 'Repayment', '7.00', 0.84248, 8.31],
    # Add more rows here...
    ['Total (GBP)', '', 459.0, '', 532.63],
    ['Total Interest (GBP)', '', 161.34, '', 187.47],
    ['Amount Toward Loan Repayment (EUR)', '', '', '', 345.15]
]

original_pdfs = ['Student Finance Account _ 21-22.pdf', 'Student Finance Account _ 22-23.pdf']
output_pdf = "final_output_report.pdf"

# Initialize and generate the PDF
pdf_generator = PDFGenerator(output_pdf, formatted_data, original_pdfs)
pdf_generator.generate_pdf()
"""