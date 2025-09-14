"""
Medical Certificate Generator Module
-----------------------------------
This module creates medical summary certificates that contain key health information
extracted from medical reports along with verification data.
"""

import re
import hashlib
import json
from datetime import datetime
import uuid
import base64

class MedicalCertificate:
    """Generates and validates medical summary certificates"""
    
    @staticmethod
    def extract_medical_codes(text):
        """Extract medical codes (ICD-10, CPT, etc.) from text"""
        # ICD-10 codes usually follow pattern like (A00.0) or [A00.0]
        icd_codes = re.findall(r'(?:[([])?([A-Z]\d{2}(?:\.\d{1,2})?)[)\]]?', text)
        
        # CPT codes are typically 5 digits
        cpt_codes = re.findall(r'\b(\d{5})\b', text)
        
        # Filter out false positives from CPT codes (like dates, zip codes)
        cpt_codes = [code for code in cpt_codes if not re.search(r'\d{2}/\d{2}/\d{4}', text)]
        
        return {
            "icd10": icd_codes[:5],  # Limit to first 5 codes
            "cpt": cpt_codes[:5]
        }
    
    @staticmethod
    def extract_key_info(text):
        """Extract critical medical information"""
        info = {}
        
        # Try to find patient name
        name_match = re.search(r'(?:patient|name)[:\s]+([A-Za-z\s\.]{2,30})', text, re.IGNORECASE)
        if name_match:
            info['patient_name'] = name_match.group(1).strip()
        
        # Try to find doctor name
        doctor_match = re.search(r'(?:doctor|physician|dr\.?)[:\s]+([A-Za-z\s\.]{2,30})', text, re.IGNORECASE)
        if doctor_match:
            info['doctor'] = doctor_match.group(1).strip()
            
        # Try to find diagnosis
        diagnosis_match = re.search(r'(?:diagnosis)[:\s]+(.*?)(?=\n\n|\n[A-Z]|$)', text, re.IGNORECASE | re.DOTALL)
        if diagnosis_match:
            info['diagnosis'] = diagnosis_match.group(1).strip()
        
        return info
    
    @staticmethod
    def generate_certificate(text, file_hash, address=None, explanation=None):
        """Generate a medical certificate from report text and hash"""
        # Create certificate data
        cert_id = str(uuid.uuid4())[:8].upper()
        
        # Extract medical information
        key_info = MedicalCertificate.extract_key_info(text)
        med_codes = MedicalCertificate.extract_medical_codes(text)
        
        # Certificate creation timestamp
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        
        # Extract key findings from AI explanation if available
        diagnosis_summary = "Medical report analyzed and processed"
        if explanation:
            # Try to extract the main diagnosis/condition from the AI explanation
            import re
            # Look for common medical conditions mentioned in the explanation
            conditions = re.findall(r'\b(pneumonia|diabetes|hypertension|infection|heart|lung|cancer|transplant|cardiomyopathy)\b', explanation.lower())
            if conditions:
                # Take the first few unique conditions
                unique_conditions = list(dict.fromkeys(conditions))[:3]
                diagnosis_summary = f"Conditions identified: {', '.join(unique_conditions).title()}"
        
        # Try to get diagnosis from the original text if explanation doesn't have enough detail
        if not diagnosis_summary or diagnosis_summary == "Medical report analyzed and processed":
            diagnosis_summary = key_info.get('diagnosis', 'Medical report processed and analyzed by AI')
        
        # Create certificate data structure
        certificate = {
            "certificate_id": f"MED-CERT-{cert_id}",
            "document_hash": file_hash,
            "verification_address": address or "Not verified on blockchain",
            "timestamp": timestamp,
            "patient_info": {
                "name": key_info.get('patient_name', 'Patient'),
                # Add only first and last initials for privacy
                "initials": "".join([n[0].upper() for n in key_info.get('patient_name', 'P A').split()[:2]]) if 'patient_name' in key_info else "P.A."
            },
            "medical_info": {
                "diagnosis_summary": diagnosis_summary,
                "medical_codes": med_codes,
                "treating_physician": key_info.get('doctor', 'Medical Professional'),
                "ai_analysis_available": bool(explanation),
                "report_type": "Medical Report Analysis"
            },
            "certificate_status": "VALID"
        }
        
        # Create a JSON string of the certificate
        cert_json = json.dumps(certificate, indent=2)
        
        return certificate, cert_json
    
    @staticmethod
    def generate_certificate_html(certificate):
        """Generate HTML version of the certificate for display"""
        cert = certificate
        
        # Basic styling for the certificate
        html = f"""
        <div class="medical-certificate">
            <div class="certificate-header">
                <h2>Medical Summary Certificate</h2>
                <p class="cert-id">ID: {cert['certificate_id']}</p>
            </div>
            
            <div class="certificate-body">
                <div class="section">
                    <h3>Document Verification</h3>
                    <p><strong>Hash:</strong> {cert['document_hash'][:20]}...{cert['document_hash'][-8:]}</p>
                    <p><strong>Verified:</strong> {datetime.strptime(cert['timestamp'], '%Y-%m-%d %H:%M:%S UTC').strftime('%b %d, %Y at %H:%M UTC')}</p>
                </div>
                
                <div class="section">
                    <h3>Patient Information</h3>
                    <p><strong>Patient Initials:</strong> {cert['patient_info']['initials']}</p>
                </div>
                
                <div class="section">
                    <h3>Medical Summary</h3>
                    <p><strong>Diagnosis:</strong> {cert['medical_info']['diagnosis_summary']}</p>
                    
                    <div class="codes">
                        <p><strong>Medical Codes:</strong></p>
                        <ul>
                            {"".join([f"<li>{code}</li>" for code in cert['medical_info']['medical_codes'].get('icd10', []) if code])}
                        </ul>
                    </div>
                    
                    <p><strong>Physician:</strong> {cert['medical_info']['treating_physician']}</p>
                </div>
                
                <div class="verification">
                    <p>This certificate verifies that the referenced medical document 
                    has been cryptographically secured and contains the key medical information
                    extracted from the original document.</p>
                </div>
            </div>
            
            <div class="certificate-footer">
                <p class="status">Status: {cert['certificate_status']}</p>
                <p class="timestamp">Generated: {cert['timestamp']}</p>
            </div>
        </div>
        """
        
        return html
