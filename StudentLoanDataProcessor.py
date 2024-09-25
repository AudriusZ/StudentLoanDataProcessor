import xml.etree.ElementTree as ET
import pdfplumber
import re
from datetime import datetime, timedelta
import csv

class StudentLoanDataProcessor:
    def __init__(self, pdf_paths, xml_path):
        """
        Initializes the processor with the paths to the PDF files and XML file containing exchange rates.
        """
        self.pdf_paths = pdf_paths
        self.xml_path = xml_path
        self.data = {}
        self.filtered_year = None  # Stores the filtered year once data is filtered

    def import_pdfs(self):
        """
        Imports and extracts text data from the provided PDF files.
        """
        print("Importing PDFs and extracting data...")
        for pdf in self.pdf_paths:
            with pdfplumber.open(pdf) as pdf_file:
                pdf_text = ""
                for page in pdf_file.pages:
                    pdf_text += page.extract_text()
                self.data[pdf] = pdf_text  # Store the extracted text for processing
                print(f"Data extracted from {pdf}:\n{pdf_text}")

    def separate_data(self):
        """
        Separates the extracted data into two categories: repayments and interest.
        Uses regex patterns to find relevant transaction entries.
        """
        print("Separating data into repayments and interest...")

        repayments = []
        interest = []

        # Regex patterns for detecting repayments and interest in the PDF text
        repayment_pattern = re.compile(r'(\d{2}/\d{2}/\d{4})\s+Repayment Received\s+([\d,.]+)')
        interest_pattern = re.compile(r'(\d{2}/\d{2}/\d{4})\s+Interest\s+[\d.]+%\s+([\d,.]+)')

        # Loop through all extracted PDF data and separate repayments and interest
        for pdf, text in self.data.items():
            repayments_matches = repayment_pattern.findall(text)
            for match in repayments_matches:
                date, amount = match
                repayments.append((date, amount.replace(",", "")))  # Clean up commas from amounts

            interest_matches = interest_pattern.findall(text)
            for match in interest_matches:
                date, amount = match
                interest.append((date, amount.replace(",", "")))  # Clean up commas from amounts

        self.repayments = repayments
        self.interest = interest

        print("Repayments:", repayments)
        print("Interest:", interest)

    def filter_by_year(self, year):
        """
        Filters the repayment and interest data by the specified year.
        """
        print(f"Filtering data for the year {year}...")
        self.filtered_year = year  # Store the filtered year

        def parse_date(date_str):
            """Helper function to parse date strings into datetime objects."""
            try:
                return datetime.strptime(date_str, '%d/%m/%Y')
            except ValueError:
                return None

        # Filter repayments and interest for the given year
        self.repayments_filtered = [
            (date, amount) for date, amount in self.repayments 
            if parse_date(date) and parse_date(date).year == year
        ]

        self.interest_filtered = [
            (date, amount) for date, amount in self.interest
            if parse_date(date) and parse_date(date).year == year
        ]

        print(f"Repayments in {year}:", self.repayments_filtered)
        print(f"Interest in {year}:", self.interest_filtered)

    def import_exchange_rates(self):
        """
        Imports exchange rates from the provided XML file (assumed to be from the ECB).
        """
        print("Importing exchange rates from XML...")
        tree = ET.parse(self.xml_path)
        root = tree.getroot()
        
        self.exchange_rates = []
        for series in root.findall('.//{http://www.ecb.europa.eu/vocabulary/stats/exr/1}Series'):
            for obs in series.findall('{http://www.ecb.europa.eu/vocabulary/stats/exr/1}Obs'):
                date = obs.attrib['TIME_PERIOD']
                value = obs.attrib['OBS_VALUE']
                self.exchange_rates.append((date, float(value)))

        print("Exchange rates:", self.exchange_rates)

    def match_exchange_rates(self):
        """
        Matches exchange rates to the repayment and interest transactions by date.
        If a rate for a specific date isn't available, tries previous days.
        """
        print("Matching exchange rates with repayment and interest dates...")
        self.matched_repayments = []
        self.matched_interest = []

        def parse_date_to_iso(date_str):
            """Convert date from 'DD/MM/YYYY' to 'YYYY-MM-DD' format."""
            try:
                return datetime.strptime(date_str, '%d/%m/%Y').strftime('%Y-%m-%d')
            except ValueError:
                return None

        for date, amount in self.repayments_filtered:
            iso_date = parse_date_to_iso(date)
            rate = self.get_exchange_rate(iso_date)
            if rate:
                self.matched_repayments.append((iso_date, amount, rate))

        for date, amount in self.interest_filtered:
            iso_date = parse_date_to_iso(date)
            rate = self.get_exchange_rate(iso_date)
            if rate:
                self.matched_interest.append((iso_date, amount, rate))

        print("Matched exchange rates for repayments:", self.matched_repayments)
        print("Matched exchange rates for interest:", self.matched_interest)

    def get_exchange_rate(self, date):
        """
        Retrieves the exchange rate for a specific date.
        If not found, tries to get the rate from previous days (up to a week back).
        Returns 'error' if no rate is found.
        """
        for rate_date, rate_value in self.exchange_rates:
            if rate_date == date:
                return rate_value
        
        # If no rate is available for the exact date, try previous days (up to a week)
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        for i in range(1, 8):  # Look back up to 7 days
            previous_date = (date_obj - timedelta(days=i)).strftime('%Y-%m-%d')
            for rate_date, rate_value in self.exchange_rates:
                if rate_date == previous_date:
                    return rate_value

        return "error"

    def calculate_totals(self):
        """
        Calculates the total repayments and interest in both GBP and EUR.
        Also calculates the amount that went toward repaying the loan (in EUR).
        """
        total_repayments_gbp = 0.0
        total_interest_gbp = 0.0
        total_repayments_eur = 0.0
        total_interest_eur = 0.0

        # Sum repayments in GBP and EUR
        for date, amount_gbp, rate in self.matched_repayments:
            amount_gbp = float(amount_gbp)
            amount_eur = amount_gbp / rate
            total_repayments_gbp += amount_gbp
            total_repayments_eur += amount_eur

        # Sum interest in GBP and EUR
        for date, amount_gbp, rate in self.matched_interest:
            amount_gbp = float(amount_gbp)
            amount_eur = amount_gbp / rate
            total_interest_gbp += amount_gbp
            total_interest_eur += amount_eur

        total_loan_repaid_eur = total_repayments_eur - total_interest_eur

        return {
            "total_repayments_gbp": total_repayments_gbp,
            "total_interest_gbp": total_interest_gbp,
            "total_repayments_eur": total_repayments_eur,
            "total_interest_eur": total_interest_eur,
            "total_loan_repaid_eur": total_loan_repaid_eur
        }

    def export_to_csv(self, year=None):
        """
        Exports the processed data, including matched exchange rates and totals, to a CSV file.
        The file is named according to the filtered year (if provided).
        """
        if year is None:
            year = self.filtered_year
        filename = f"output_{year}.csv"
        print(f"Exporting data to {filename}...")

        # Perform the calculations
        totals = self.calculate_totals()

        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)

            # Write header
            writer.writerow(["Skaičiavimai"])
            writer.writerow(["Data", "Mokėjimo rūšis", "Suma GBP", "Valiutų kursas* EUR/GBP", "Suma EUR"])

            # Write repayment transactions
            for date, amount_gbp, rate in self.matched_repayments:
                amount_eur = float(amount_gbp) / rate
                writer.writerow([date, "Repayment", amount_gbp, rate, round(amount_eur, 2)])

            # Write interest transactions
            for date, amount_gbp, rate in self.matched_interest:
                amount_eur = float(amount_gbp) / rate
                writer.writerow([date, "Interest", amount_gbp, rate, round(amount_eur, 2)])

            # Write totals at the end
            writer.writerow([])
            writer.writerow([f"{year}", "Visos sumokėtos įmokos", "", "", round(totals["total_repayments_eur"], 2)])
            writer.writerow([f"{year}", "Palūkanų suma", "", "", round(totals["total_interest_eur"], 2)])
            writer.writerow([f"{year}", "Įmokų dalis paskolai dengti", "", "", round(totals["total_loan_repaid_eur"], 2)])

        print(f"Data successfully written to {filename}")

# Example usage:
pdf_paths = ['Student Finance Account _ 21-22.pdf', 'Student Finance Account _ 22-23.pdf']
xml_path = 'gbp.xml'

processor = StudentLoanDataProcessor(pdf_paths, xml_path)
processor.import_pdfs()  # Step 1: Import PDF data
processor.separate_data()  # Step 2: Separate data into repayments and interest
processor.filter_by_year(2022)  # Step 3: Filter data for the year 2022
processor.import_exchange_rates()  # Step 4: Import exchange rates from XML
processor.match_exchange_rates()  # Step 5: Match exchange rates to transactions
processor.export_to_csv()  # Step 6: Export the data to CSV file

