import os
from flask import Flask, render_template, request, send_file
from paddleocr import PaddleOCR
import pandas as pd
import re

app = Flask(__name__)

# Create uploads folder if it doesn't exist
os.makedirs("uploads", exist_ok=True)

# Initialize OCR engine (this runs once when app starts)
print("Loading PaddleOCR model... this may take a minute...")
ocr = PaddleOCR(use_angle_cls=True, lang='en')

def extract_invoice_data(file_path):
    """Extract data from invoice image"""
    result = ocr.ocr(file_path, cls=True)
    
    # Convert OCR results to text
    text_lines = [line[1][0] for res in result for line in res]
    full_text = " ".join(text_lines)
    
    print("Extracted text:", full_text)
    
    # Extract information using regex patterns
    data = {
        "Supplier Name": text_lines[0] if text_lines else "N/A",
        "GSTIN": extract_pattern(r'\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}', full_text),
        "Invoice Number": extract_pattern(r'(?i)Inv(?:oice)?\s*(?:No)?[:.\-\s]*(\w+)', full_text),
        "Date": extract_pattern(r'\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4}', full_text),
        "Total Amount": extract_pattern(r'(?i)(?:Total|Net|Amount)[:.\-\s]*([\d,]+\.?\d*)', full_text),
    }
    
    return data

def extract_pattern(pattern, text):
    """Helper function to extract data using regex"""
    match = re.search(pattern, text)
    if match:
        return match.group(1) if match.groups() else match.group(0)
    return "N/A"

@app.route('/', methods=['GET', 'POST'])
def index():
    """Main page - handle file upload"""
    data = None
    excel_ready = False
    
    if request.method == 'POST':
        # Check if file was uploaded
        if 'file' not in request.files:
            return render_template('index.html', error="No file uploaded")
        
        file = request.files['file']
        
        if file.filename == '':
            return render_template('index.html', error="No file selected")
        
        # Save uploaded file
        file_path = os.path.join("uploads", file.filename)
        file.save(file_path)
        
        try:
            # Extract data from image
            data = extract_invoice_data(file_path)
            
            # Save to Excel
            df = pd.DataFrame([data])
            excel_path = os.path.join("uploads", "invoice_data.xlsx")
            df.to_excel(excel_path, index=False)
            
            excel_ready = True
            
        except Exception as e:
            return render_template('index.html', error=f"Error processing image: {str(e)}")
    
    return render_template('index.html', data=data, excel_ready=excel_ready)

@app.route('/download')
def download():
    """Download the Excel file"""
    try:
        return send_file(
            os.path.join("uploads", "invoice_data.xlsx"),
            as_attachment=True,
            download_name="invoice_data.xlsx"
        )
    except Exception as e:
        return f"Error downloading file: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
