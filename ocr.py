import pytesseract
from PIL import Image
import os
import fitz  # PyMuPDF for PDF handling
import tempfile
import io

# Manually point to the installed tesseract.exe if needed:
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_text(file_path):
    """
    Extract text from an image or PDF using OCR
    """
    try:
        # Check if file is PDF
        if file_path.lower().endswith('.pdf'):
            return extract_from_pdf(file_path)
        else:
            # Process as image
            img = Image.open(file_path)
            text = pytesseract.image_to_string(img)
            return text
    except Exception as e:
        print(f"❌ OCR Error: {str(e)}")
        return f"Error during OCR: {str(e)}"

def extract_from_pdf(pdf_path):
    """Extract text from PDF files - first tries direct extraction, then OCR if needed"""
    try:
        # Open the PDF
        pdf_document = fitz.open(pdf_path)
        text_content = ""
        
        # First attempt: Try to extract text directly
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            text_content += page.get_text()
        
        # If direct extraction yielded meaningful text, return it
        if len(text_content.strip()) > 50:  # Arbitrary threshold to determine if extraction worked
            return text_content
            
        # If direct extraction didn't yield good results, try OCR on rendered images
        print("Direct PDF text extraction didn't yield good results. Attempting OCR...")
        text_content = ""
        
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            
            # Render page to an image with higher resolution for better OCR
            pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
            
            # Convert to PIL Image
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            # Perform OCR
            page_text = pytesseract.image_to_string(img)
            text_content += page_text + "\n\n"
            
        return text_content
        
    except Exception as e:
        print(f"❌ PDF Processing Error: {str(e)}")
        return f"Error processing PDF: {str(e)}"
