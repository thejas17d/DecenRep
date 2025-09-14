# DecenRep - Decentralized Medical Report Analysis

DecenRep is an enterprise-grade Flask-based web application designed for medical report processing and verification. It combines Optical Character Recognition (OCR), AI-driven summarization, and blockchain certification to provide a secure, reliable platform for medical report analysis.

## Features

- **Advanced OCR**: Extract text from both images and PDF medical reports
- **AI-Powered Analysis**: Smart summarization of medical terminology with layman explanations
- **Blockchain Certification**: Secure, tamper-proof certification of medical reports
- **PDF Generation**: Create professional, printable reports of analysis results
- **Modern UI**: Clean, responsive interface with dark mode support

## Project Structure

```
DecenRep
├── app.py                # Main Flask application
├── requirements.txt      # Python dependencies
├── README.md
├── templates/            # HTML templates
│   └── index.html
├── static/               # Static assets (CSS, JS)
│   ├── certificate.css
│   ├── modal.css
│   ├── script.js
│   ├── style.css
│   └── utilities.css
├── frontend/            # React frontend components
├── uploads/             # User uploaded files directory
├── utils/               # Core processing modules
│   ├── blockchain.py    # Blockchain certification
│   ├── certificate.py   # Certificate generation
│   ├── ocr.py           # Text extraction from documents
│   ├── pipeline.py      # End-to-end processing pipeline
│   └── summarization.py # AI-powered text analysis
```

## Setup Instructions

1. **Clone the repository:**
   ```
   git clone <repository-url>
   cd DecenRep
   ```

2. **Create a virtual environment:**
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install the required packages:**
   ```
   pip install -r requirements.txt
   ```

4. **Install Tesseract OCR:**
   Follow the installation instructions for Tesseract based on your operating system. Ensure that Tesseract is added to your system's PATH.

5. **Set up environment variables:**
   Create a `.env` file in the root directory and add your Groq API key:
   ```
   GROQ_API_KEY=your_api_key_here
   ```

## Usage

1. **Run the application:**
   ```
   python app.py
   ```

2. **Access the application:**
   Open your web browser and go to `http://127.0.0.1:5000`.

3. **Upload a medical report:**
   Use the provided interface to upload a medical document (image or PDF). The application will:
   - Extract text using OCR
   - Generate an AI-powered analysis with medical term explanations
   - Create a blockchain certificate for verification
   - Display results in a user-friendly format

4. **Get a printable version:**
   Click the "Printable Version" button to generate a PDF certificate with the analysis results.

## Technologies Used

- **Flask**: Web application framework
- **PyMuPDF**: PDF processing and text extraction
- **Tesseract OCR**: Image text recognition
- **Groq API**: Advanced language model for medical text analysis
- **Web3.py**: Ethereum blockchain integration
- **ReportLab**: PDF certificate generation

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any enhancements or bug fixes.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.