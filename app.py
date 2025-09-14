from flask import Flask, render_template, request, send_file, jsonify, make_response
from markupsafe import Markup
from werkzeug.utils import secure_filename
import os
import hashlib
import io
import json
import uuid
import re
from datetime import datetime
from .blockchain import store_report_hash, verify_report_hash
from .certificate import MedicalCertificate
from .pipeline import MedicalReportPipeline

app = Flask(__name__, 
            template_folder='../frontend/templates',
            static_folder='../frontend/static')
UPLOAD_FOLDER = "../uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize the medical report pipeline
pipeline = MedicalReportPipeline()

def format_explanation(text):
    """Format the AI explanation for better HTML rendering"""
    if not text:
        return ""
    
    # Convert headers
    text = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    
    # Convert bold
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    
    # Convert lists
    text = re.sub(r'^\* (.*?)$', r'<li>\1</li>', text, flags=re.MULTILINE)
    text = re.sub(r'(<li>.*?</li>\n)+', r'<ul>\g<0></ul>', text, flags=re.DOTALL)
    
    # Convert paragraphs
    paragraphs = []
    for para in text.split("\n\n"):
        if not para.startswith('<h') and not para.startswith('<ul>'):
            para = f"<p>{para}</p>"
        paragraphs.append(para)
    
    return Markup("".join(paragraphs))

PRIVATE_KEY = "c169556a04e3d5a17a346e809bc3ff6ff8ecfc9a2f9c920733cdb49d639e4faa"

@app.route("/", methods=["GET", "POST"])
def index():
    extracted = explanation = file_hash = tx_hash = verification = None
    certificate = certificate_html = None
    processing_error = None

    if request.method == "POST":
        # Handle file upload
        if "report" in request.files:
            file = request.files["report"]
            if file.filename:
                try:
                    # Generate a unique ID for this processing session
                    session_id = str(uuid.uuid4())[:8]
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(UPLOAD_FOLDER, filename)
                    file.save(filepath)
                    
                    print(f"🚀 Starting medical report pipeline for {filename}")
                    
                    # Run the file through the pipeline
                    results = pipeline.process_report(filepath, session_id)
                    
                    # Extract results for the template
                    if results['status'] in ['completed', 'completed_with_errors']:
                        extracted = results.get('extracted_text', '')
                        raw_explanation = results.get('explanation', '')
                        explanation = format_explanation(raw_explanation)
                        file_hash = results.get('file_hash', '')
                        certificate = results.get('certificate', None)
                        certificate_html = results.get('certificate_html', None)
                        
                        if results['errors']:
                            processing_error = f"Completed with warnings: {', '.join(results['errors'])}"
                    else:
                        processing_error = f"Processing failed: {', '.join(results['errors'])}"
                
                except Exception as e:
                    processing_error = f"Error processing file: {str(e)}"
                    print(f"❌ Error in file upload handling: {str(e)}")

        # Store hash on blockchain
        if "store_hash" in request.form:
            file_hash = request.form.get("store_hash_value", "")
            if file_hash:
                try:
                    print("📝 Storing hash:", file_hash)
                    tx_hash = store_report_hash(file_hash, PRIVATE_KEY)
                    print("✅ TX Hash:", tx_hash)
                    
                    # Update certificate with blockchain address if we have one
                    if 'certificate' in request.form:
                        cert_data = json.loads(request.form['certificate'])
                        cert_data['verification_address'] = tx_hash
                        certificate = cert_data
                        certificate_html = MedicalCertificate.generate_certificate_html(cert_data)
                        
                except Exception as e:
                    tx_hash = f"Error: {str(e)}"
                    print("❌ Error storing hash:", e)

        # Verify hash from input
        if "verify_hash" in request.form:
            hash_to_verify = request.form.get("verify_input", "")
            print("🔍 Verifying hash:", hash_to_verify)
            verification = verify_report_hash(hash_to_verify)

            # Format timestamp
            if verification.get("exists"):
                ts = verification["timestamp"]
                if isinstance(ts, int) and ts > 0:
                    verification["timestamp"] = datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S UTC')
            print("✅ Result:", verification)

        # Download AI Summary
        if "download_summary" in request.form:
            try:
                summary_text = request.form["download_summary"]
                
                # Create a response with proper headers
                response = make_response(summary_text)
                response.headers["Content-Disposition"] = "attachment; filename=diagnosis_summary.txt"
                response.headers["Content-Type"] = "text/plain; charset=utf-8"
                
                print("📄 Downloading diagnosis summary text file")
                return response
            except Exception as e:
                print(f"❌ Error downloading summary: {str(e)}")
                processing_error = f"Error generating summary download: {str(e)}"
            
        # Download Medical Certificate
        if "download_certificate" in request.form:
            try:
                cert_data = json.loads(request.form["certificate_data"])
                cert_json = json.dumps(cert_data, indent=2)
                
                # Create a response with proper headers
                response = make_response(cert_json)
                response.headers["Content-Disposition"] = f"attachment; filename=medical_certificate_{cert_data['certificate_id']}.json"
                response.headers["Content-Type"] = "application/json"
                
                print(f"📄 Downloading certificate JSON: {cert_data['certificate_id']}")
                return response
            except Exception as e:
                print(f"❌ Error downloading certificate: {str(e)}")
                processing_error = f"Error generating certificate download: {str(e)}"

    return render_template("index.html",
                           extracted=extracted,
                           explanation=explanation,
                           file_hash=file_hash,
                           tx_hash=tx_hash,
                           verification=verification,
                           certificate=certificate,
                           certificate_html=certificate_html,
                           error=processing_error)

# API endpoint for certificate generation
@app.route("/api/generate-certificate", methods=["POST"])
def generate_certificate():
    try:
        # Get data from request
        data = request.get_json()
        
        if not data or not data.get('text') or not data.get('hash'):
            return jsonify({"error": "Missing required fields"}), 400
            
        # Generate certificate
        cert_data, cert_json = MedicalCertificate.generate_certificate(
            data['text'], 
            data['hash'],
            data.get('address')
        )
        
        # Return certificate JSON
        return jsonify(cert_data)
        
    except Exception as e:
        print(f"❌ Certificate generation error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# PDF Certificate download endpoint
@app.route('/download/certificate-pdf', methods=['POST'])
def download_certificate_pdf():
    """Generate a PDF certificate from certificate data"""
    try:
        # Get certificate data
        cert_data_raw = request.form.get("certificate_data", "{}")
        print(f"DEBUG - Raw certificate data: {cert_data_raw[:200]}...")
        
        # Parse certificate data
        try:
            cert_data = json.loads(cert_data_raw)
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {e}")
            return jsonify({"error": f"Invalid certificate data: {str(e)}"}), 400
        
        # Generate PDF using ReportLab
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from io import BytesIO
            
            # Extract certificate information
            cert_id = cert_data.get('certificate_id', 'UNKNOWN')
            hospital = cert_data.get('hospital', {})
            doctor = cert_data.get('doctor', {})
            patient = cert_data.get('patient_info', {})
            medical_info = cert_data.get('medical_info', {})
            timestamp = cert_data.get('timestamp', 'Unknown')
            
            # Get diagnosis from medical_info
            diagnosis = medical_info.get('diagnosis_summary', 'Medical report processed and analyzed')
            treating_physician = medical_info.get('treating_physician', 'Medical Professional')
            report_type = medical_info.get('report_type', 'Medical Report')
            
            # Create PDF buffer and document
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=1*inch)
            
            # Get styles and create custom ones
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                alignment=1,
                textColor=colors.HexColor('#2c3e50')
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=16,
                spaceAfter=12,
                textColor=colors.HexColor('#34495e')
            )
            
            # Build PDF content
            story = []
            
            # Title
            story.append(Paragraph("Medical Certificate", title_style))
            story.append(Paragraph(f"Certificate ID: {cert_id}", styles['Normal']))
            story.append(Paragraph(f"Generated: {timestamp}", styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
            
            # Patient Information
            story.append(Paragraph("Patient Information", heading_style))
            story.append(Paragraph(f"<b>Patient Initials:</b> {patient.get('initials', 'N/A')}", styles['Normal']))
            story.append(Spacer(1, 0.2*inch))
            
            # Medical Information
            story.append(Paragraph("Medical Summary", heading_style))
            story.append(Paragraph(f"<b>Report Type:</b> {report_type}", styles['Normal']))
            story.append(Paragraph(f"<b>Treating Physician:</b> {treating_physician}", styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph(f"<b>Diagnosis Summary:</b>", styles['Normal']))
            story.append(Paragraph(diagnosis, styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
            
            # Verification Information
            story.append(Paragraph("Verification", heading_style))
            story.append(Paragraph(f"<b>Document Hash:</b> {cert_data.get('document_hash', 'N/A')[:16]}...", styles['Normal']))
            story.append(Paragraph(f"<b>Certificate Status:</b> {cert_data.get('certificate_status', 'VALID')}", styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
            
            # Footer
            story.append(Paragraph("This certificate was digitally generated and verified using blockchain technology.", styles['Italic']))
            story.append(Paragraph("© DecenRep - Decentralized Medical Records Platform", styles['Italic']))
            
            # Build PDF
            doc.build(story)
            
            # Prepare response
            pdf_data = buffer.getvalue()
            buffer.close()
            
            response = make_response(pdf_data)
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'attachment; filename=Medical_Certificate_{cert_id}.pdf'
            
            return response
            
        except ImportError as e:
            print(f"❌ ReportLab import error: {e}")
            return jsonify({"error": "PDF generation library not available"}), 500
        
    except Exception as e:
        print(f"❌ Certificate PDF generation error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("🚀 Starting DecenRep server - Decentralized Medical Records Platform")
    app.run(debug=True, host="0.0.0.0", port=5000)
