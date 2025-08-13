# app.py

from flask import Flask, request, send_file, jsonify, render_template
from flask_cors import CORS
from fpdf import FPDF
import io
import os
import base64

# Initialize Flask app
app = Flask(__name__, static_folder='static')
CORS(app)

# Set the maximum content length for uploads to 200 MB (200 * 1024 * 1024 bytes)
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200 Megabytes

# Define the API endpoint for processing data and generating a single multi-page PDF
@app.route('/generate-pdfs-from-data', methods=['POST'])
def generate_pdfs_from_data():
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No JSON data received.'}), 400

    branch = data.get('branch', 'N/A')
    year = data.get('year', 'N/A')
    semester = data.get('semester', 'N/A')
    section = data.get('section', 'N/A')
    strength = data.get('strength', 'N/A')
    test = data.get('test', 'N/A')
    app_image_base64 = data.get('appImageBase64', '')
    all_subjects_data = data.get('allSubjectsData', {}) # New structure for all subjects

    try:
        # Create a single PDF object for all subjects
        pdf = FPDF()
        img_width_pdf = 180
        img_height_pdf = (img_width_pdf / 1000) * 250
        page_width = pdf.w
        img_x_pdf = (page_width - img_width_pdf) / 2

        def add_header_to_pdf(doc_instance, subject_name):
            doc_instance.set_font('Arial', '', 10)
            if app_image_base64:
                img_data_clean = app_image_base64.split(',')[1] if ',' in app_image_base64 else app_image_base64
                doc_instance.image(io.BytesIO(base64.b64decode(img_data_clean)), x=img_x_pdf, y=10, w=img_width_pdf, h=img_height_pdf, type='JPEG')
            
            doc_instance.set_xy(0, 10 + img_height_pdf + 5)
            doc_instance.set_font('Arial', '', 10)
            doc_instance.cell(w=page_width, h=0, txt=f"Branch: {branch} | Year: {year} | Semester: {semester} | Section: {section} | Test: {test}", align='C')
            doc_instance.line(10, 10 + img_height_pdf + 10, page_width - 10, 10 + img_height_pdf + 10)
            
            doc_instance.set_xy(0, 10 + img_height_pdf + 15)
            doc_instance.set_font('Arial', 'B', 14)
            doc_instance.cell(w=page_width, h=0, txt=f"Subject: {subject_name}", align='C')

        # Iterate through all subjects and add a new page for each report
        first_page = True
        for subject_name, subject_data in all_subjects_data.items():
            low_scorers = subject_data.get('lowScorers', [])
            absent_students = subject_data.get('absentStudents', [])

            if not low_scorers and not absent_students:
                continue # Skip subjects with no data to report

            # Add a new page for each subject's report
            pdf.add_page()
            add_header_to_pdf(pdf, subject_name)

            y_position_start = 10 + img_height_pdf + 30
            
            if low_scorers:
                pdf.set_font('Arial', 'B', 16)
                pdf.set_xy(0, y_position_start)
                pdf.cell(w=page_width, h=0, txt="Students Scoring Less Than 24", align='C')
                
                table_data = [['Roll No', 'Name', 'Score']]
                for s in low_scorers:
                    table_data.append([str(s['rollNo']), str(s['name']), str(s['score'])])
                
                pdf.set_font('Arial', '', 10)
                y_start = y_position_start + 15
                col_widths = [40, 70, 30]
                
                pdf.set_fill_color(76, 175, 80)
                pdf.set_text_color(255, 255, 255)
                pdf.set_font('Arial', 'B', 10)
                x_pos = 10
                for i, header in enumerate(table_data[0]):
                    pdf.set_xy(x_pos, y_start)
                    pdf.cell(col_widths[i], 10, header, 1, 0, 'C', 1)
                    x_pos += col_widths[i]
                pdf.ln(10)
                
                pdf.set_text_color(51, 51, 51)
                row_fill = False
                for row in table_data[1:]:
                    pdf.set_fill_color(245, 245, 245) if not row_fill else pdf.set_fill_color(255, 255, 255)
                    row_fill = not row_fill
                    x_pos = 10
                    # Check for page break
                    if pdf.get_y() + 10 > pdf.h - 20:
                        pdf.add_page()
                        add_header_to_pdf(pdf, subject_name)
                        y_start_new = 10 + img_height_pdf + 45
                        x_pos_new = 10
                        for i, cell_data in enumerate(table_data[0]):
                            pdf.set_xy(x_pos_new, y_start_new)
                            pdf.set_fill_color(76, 175, 80)
                            pdf.set_text_color(255, 255, 255)
                            pdf.set_font('Arial', 'B', 10)
                            pdf.cell(col_widths[i], 10, cell_data, 1, 0, 'C', 1)
                            x_pos_new += col_widths[i]
                        pdf.ln(10)
                        pdf.set_text_color(51, 51, 51)
                        
                    for i, cell_data in enumerate(row):
                        pdf.set_xy(x_pos, pdf.get_y())
                        pdf.cell(col_widths[i], 10, cell_data, 1, 0, 'C', 1)
                        x_pos += col_widths[i]
                    pdf.ln(10)

            if absent_students:
                if low_scorers:
                    if pdf.get_y() + 20 > pdf.h - 20:
                        pdf.add_page()
                        add_header_to_pdf(pdf, subject_name)
                        y_position_absent = 10 + img_height_pdf + 30
                    else:
                        y_position_absent = pdf.get_y() + 15
                else:
                    y_position_absent = y_position_start
                
                pdf.set_font('Arial', 'B', 16)
                pdf.set_xy(0, y_position_absent)
                pdf.cell(w=page_width, h=0, txt="Absent Students", align='C')

                table_data = [['Roll No', 'Name']]
                for s in absent_students:
                    table_data.append([str(s['rollNo']), str(s['name'])])
                
                pdf.set_font('Arial', '', 10)
                y_start = y_position_absent + 15
                col_widths = [60, 90]

                pdf.set_fill_color(255, 193, 7)
                pdf.set_text_color(255, 255, 255)
                pdf.set_font('Arial', 'B', 10)
                x_pos = 10
                for i, header in enumerate(table_data[0]):
                    pdf.set_xy(x_pos, y_start)
                    pdf.cell(col_widths[i], 10, header, 1, 0, 'C', 1)
                    x_pos += col_widths[i]
                pdf.ln(10)

                pdf.set_text_color(51, 51, 51)
                row_fill = False
                for row in table_data[1:]:
                    pdf.set_fill_color(255, 248, 220) if not row_fill else pdf.set_fill_color(255, 255, 255)
                    row_fill = not row_fill
                    x_pos = 10
                    # Check for page break
                    if pdf.get_y() + 10 > pdf.h - 20:
                        pdf.add_page()
                        add_header_to_pdf(pdf, subject_name)
                        y_start_new = 10 + img_height_pdf + 45
                        x_pos_new = 10
                        for i, cell_data in enumerate(table_data[0]):
                            pdf.set_xy(x_pos_new, y_start_new)
                            pdf.set_fill_color(255, 193, 7)
                            pdf.set_text_color(255, 255, 255)
                            pdf.set_font('Arial', 'B', 10)
                            pdf.cell(col_widths[i], 10, cell_data, 1, 0, 'C', 1)
                            x_pos_new += col_widths[i]
                        pdf.ln(10)
                        pdf.set_text_color(51, 51, 51)
                    for i, cell_data in enumerate(row):
                        pdf.set_xy(x_pos, pdf.get_y())
                        pdf.cell(col_widths[i], 10, cell_data, 1, 0, 'C', 1)
                        x_pos += col_widths[i]
                    pdf.ln(10)

        # Output the single PDF
        pdf_output = io.BytesIO()
        pdf.output(pdf_output)
        pdf_output.seek(0)
        return send_file(pdf_output, mimetype='application/pdf', as_attachment=True, download_name='student_reports.pdf')

    except Exception as e:
        print(f"Error processing request: {e}")
        return jsonify({'error': f'Error generating PDF: {str(e)}'}), 500

@app.route('/')
def serve_index():
    return render_template('index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
