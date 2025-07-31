# app.py
from flask import Flask, render_template, request, send_file, url_for, redirect
import pandas as pd
from fpdf import FPDF
import os

app = Flask(__name__)

# Define folders for uploads and generated PDFs
UPLOAD_FOLDER = 'uploads'
PDF_FOLDER = 'generated_pdfs'
LOGO_PATH = 'static/logo.jpg'

# Ensure these directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PDF_FOLDER, exist_ok=True)

# Custom PDF class for report generation
class PDF(FPDF):
    def header(self):
        # Increase the width and height of the image
        if os.path.exists(LOGO_PATH):
            self.image(LOGO_PATH, 10, 8, 40) # x, y, width
        self.set_font('Arial', 'B', 12)
        # Push the title down so it doesn't overlap with the logo
        self.ln(20) # Add a line break to create space
        self.cell(0, 10, 'Student Report - Marks Below 24 & Absent', border=False, ln=True, align='C')
        self.ln(10)

# Main dashboard route for displaying the form and handling file uploads
@app.route('/', methods=['GET', 'POST'])
def dashboard():
    if request.method == 'POST':
        branch = request.form['branch']
        year = request.form['year']
        semester = request.form['semester']
        section = request.form['section']
        strength = request.form['strength']
        test = request.form['test']

        file = request.files['file']
        if file:
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)
            pdf_filename = process_excel(filepath, branch, year, semester, section, strength, test)
            
            # Redirect to the new preview page
            return redirect(url_for('show_result', pdf_filename=pdf_filename))

    return render_template('dashboard.html')

# Function to process the Excel file and generate the PDF
def process_excel(filepath, branch, year, semester, section, strength, test):
    # Specify header row for pandas
    df = pd.read_excel(filepath, header=14)

    # Correctly identify the subject column(s)
    subject_columns = [col for col in df.columns if 'MID' in col.upper()]

    if not subject_columns:
        print("Warning: No 'MID' columns found. Please check Excel headers.")
        if len(df.columns) > 3:
            subject_columns = [df.columns[3]]
        else:
            raise ValueError("No subject columns found in the Excel file.")

    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Iterate through each identified subject column
    for subject in subject_columns:
        pdf.add_page()
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, f'Subject: {subject} | Test: {test}', ln=True)
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 7, f'Branch: {branch}, Year: {year}, Semester: {semester}, Section: {section}, Total Strength: {strength}', ln=True)
        pdf.ln(5)

        pdf.set_font('Arial', 'B', 12)
        pdf.cell(40, 10, 'Roll No', 1)
        pdf.cell(70, 10, 'Name', 1)
        pdf.cell(30, 10, 'Marks', 1)
        pdf.cell(40, 10, 'Status', 1)
        pdf.ln()

        for index, row in df.iterrows():
            roll_no = str(row['ROLL NO'])
            name = str(row['NAME '])
            marks = row[subject]
            status = ''
            display_marks = ''

            if pd.isna(marks) or (isinstance(marks, str) and marks.strip().upper() in ['AB', 'A', 'ABSENT', '']):
                status = 'Absent'
                display_marks = 'AB'
            else:
                try:
                    numeric_marks = float(marks)
                    if numeric_marks < 24:
                        status = 'Fail'
                        display_marks = str(numeric_marks)
                    else:
                        continue
                except (ValueError, TypeError):
                    status = 'Invalid Marks'
                    display_marks = str(marks)

            pdf.set_font('Arial', '', 12)
            pdf.cell(40, 10, roll_no, 1)
            pdf.cell(70, 10, name, 1)
            pdf.cell(30, 10, display_marks, 1)
            pdf.cell(40, 10, status, 1)
            pdf.ln()

    pdf_filename = f"report_{branch}_{year}_{semester}_{section}_{test}.pdf"
    pdf_output_path = os.path.join(PDF_FOLDER, pdf_filename)
    pdf.output(pdf_output_path)
    return pdf_filename

# NEW ROUTE: To show the PDF preview page
@app.route('/result/<pdf_filename>')
def show_result(pdf_filename):
    return render_template('result.html', pdf_filename=pdf_filename)

# NEW ROUTE: To serve the PDF for viewing in the iframe
@app.route('/view/<filename>')
def view_pdf(filename):
    return send_file(os.path.join(PDF_FOLDER, filename))

# ROUTE: To securely serve the generated PDF files for download
@app.route('/download/<filename>')
def download_pdf(filename):
    return send_file(os.path.join(PDF_FOLDER, filename), as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
