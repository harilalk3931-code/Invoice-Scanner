import os
import re
import pandas as pd
from flask import Flask, render_template, request, send_file
from paddleocr import PaddleOCR

app = Flask(__name__)
# Initialize OCR (This will download models on first run)
ocr = PaddleOCR(use_textline_orientation=True, lang='en')

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            img_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(img_path)
            
            # OCR Processing
            result = ocr.ocr(img_path, cls=True)
            text_lines = [line[1][0] for res in result for line in res]
            full_text = " ".join(text_lines)

            # Extraction Logic (GST, Invoice No, Total)
            data = {
                "Supplier": text_lines[0] if text_lines else "Unknown",
                "GSTIN": re.search(r'\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}', full_text),
                "Total Amt": re.search(r'Total[:\s]*([\d,]+\.\d{2})', full_text, re.IGNORECASE)
            }
            
            # Clean results
            clean_data = {k: (v.group(1) if hasattr(v, 'group') else v) for k, v in data.items()}
            
            # Save to Excel
            df = pd.DataFrame([clean_data])
            df.to_excel(os.path.join(UPLOAD_FOLDER, 'report.xlsx'), index=False)
            
            return render_template('index.html', data=clean_data)
    return render_template('index.html')

@app.route('/download')
def download():
    return send_file(os.path.join(UPLOAD_FOLDER, 'report.xlsx'), as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)