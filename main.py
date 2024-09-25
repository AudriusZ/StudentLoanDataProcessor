from StudentLoanDataProcessor import StudentLoanDataProcessor
from PDFCreator import PDFGenerator

def main():
    pdf_paths = ['Student Finance Account _ 21-22.pdf', 'Student Finance Account _ 22-23.pdf']
    xml_path = 'gbp.xml'
    year = 2022

    processor = StudentLoanDataProcessor(pdf_paths, xml_path)
    processor.import_pdfs()  # Step 1: Import PDF data
    processor.separate_data()  # Step 2: Separate data into repayments and interest
    processor.filter_by_year(year)  # Step 3: Filter data for the year 2022
    processor.import_exchange_rates()  # Step 4: Import exchange rates from XML
    processor.match_exchange_rates()  # Step 5: Match exchange rates to transactions
    raw_data = processor.process_data_for_export(2022)
    formatted_data = processor.format_for_exporting(raw_data)    
    output_pdf = f"Skaičiavimai_{year}.pdf"
    original_pdfs = ['Student Finance Account _ 21-22.pdf', 'Student Finance Account _ 22-23.pdf']

    pdf_generator = PDFGenerator(output_pdf, formatted_data, original_pdfs)
    
    pdf_generator.generate_pdf()

if __name__ == "__main__":
    main()
