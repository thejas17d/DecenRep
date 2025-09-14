"""
Medical Report Pipeline Module
-----------------------------------
This module implements a sequential pipeline for processing medical reports:
1. OCR: Extract text from images or PDFs
2. Analysis: Process the extracted text with LLM or rule-based methods
3. Certificate Generation: Create medical certificates with key information
"""

import os
import hashlib
import tempfile
from datetime import datetime
from utils.ocr import extract_text
from utils.summarization import explain_text
from utils.certificate import MedicalCertificate

class MedicalReportPipeline:
    """Processes medical reports through a series of steps and collects results"""
    
    def __init__(self):
        self.processed_files = {}
        
    def process_report(self, file_path, file_id=None):
        """
        Process a medical report through the complete pipeline
        
        Args:
            file_path: Path to the medical report file
            file_id: Optional identifier for the report
            
        Returns:
            Dictionary containing all processing results
        """
        if not file_id:
            file_id = os.path.basename(file_path)
            
        # Initialize results dictionary
        results = {
            'file_path': file_path,
            'file_id': file_id,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'processing',
            'steps_completed': [],
            'errors': []
        }
        
        try:
            # STEP 1: Generate file hash
            print(f"🔒 Step 1: Generating file hash for {file_id}")
            with open(file_path, "rb") as f:
                file_hash = hashlib.sha3_256(f.read()).hexdigest()
                
            results['file_hash'] = file_hash
            results['steps_completed'].append('hash_generation')
            print(f"✅ Hash generated: {file_hash[:10]}...{file_hash[-6:]}")
            
            # STEP 2: OCR - Extract text from document
            print(f"📄 Step 2: Extracting text with OCR from {file_id}")
            extracted_text = extract_text(file_path)
            
            if not extracted_text or len(extracted_text.strip()) < 20:
                results['errors'].append('OCR_EXTRACTION_FAILED')
                print("❌ OCR extraction failed: insufficient text extracted")
            else:
                results['extracted_text'] = extracted_text
                results['steps_completed'].append('ocr')
                text_preview = extracted_text[:100].replace('\n', ' ') + '...'
                print(f"✅ Text extracted ({len(extracted_text)} chars): {text_preview}")
            
            # STEP 3: AI Analysis - Generate explanation
            if 'ocr' in results['steps_completed']:
                print(f"🧠 Step 3: Analyzing text with AI for {file_id}")
                explanation = explain_text(extracted_text)
                
                if explanation:
                    results['explanation'] = explanation
                    results['steps_completed'].append('analysis')
                    explanation_preview = explanation[:100].replace('\n', ' ') + '...'
                    print(f"✅ AI analysis complete: {explanation_preview}")
                else:
                    results['errors'].append('AI_ANALYSIS_FAILED')
                    print("❌ AI analysis failed")
            
            # STEP 4: Certificate Generation
            if 'analysis' in results['steps_completed']:
                print(f"📜 Step 4: Generating medical certificate for {file_id}")
                certificate_data, certificate_json = MedicalCertificate.generate_certificate(
                    extracted_text, file_hash, explanation=explanation
                )
                
                if certificate_data:
                    results['certificate'] = certificate_data
                    results['certificate_html'] = MedicalCertificate.generate_certificate_html(certificate_data)
                    results['steps_completed'].append('certificate')
                    print(f"✅ Certificate generated: {certificate_data['certificate_id']}")
                else:
                    results['errors'].append('CERTIFICATE_GENERATION_FAILED')
                    print("❌ Certificate generation failed")
            
            # Final status
            if results['errors']:
                results['status'] = 'completed_with_errors'
                print(f"⚠️ Pipeline completed with errors: {', '.join(results['errors'])}")
            else:
                results['status'] = 'completed'
                print(f"✅ Pipeline completed successfully for {file_id}")
                
            # Store results
            self.processed_files[file_id] = results
            return results
            
        except Exception as e:
            print(f"❌ Pipeline error: {str(e)}")
            results['status'] = 'failed'
            results['errors'].append(f'PIPELINE_ERROR: {str(e)}')
            self.processed_files[file_id] = results
            return results
    
    def get_results(self, file_id):
        """Retrieve results for a previously processed file"""
        return self.processed_files.get(file_id, None)
        
    def clear_results(self, file_id=None):
        """Clear results for a specific file or all files"""
        if file_id:
            if file_id in self.processed_files:
                del self.processed_files[file_id]
        else:
            self.processed_files = {}
