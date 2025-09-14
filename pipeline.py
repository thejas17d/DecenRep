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
import re
from datetime import datetime
from groq import Groq
from .ocr import extract_text
from .certificate import MedicalCertificate

# Set your Groq API key - better to use environment variables in production
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "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")
groq_client = Groq(api_key=GROQ_API_KEY)

# Enhanced duplicate removal function
def remove_duplicate_content(text):
    """Enhanced duplicate removal - removes exact and semantic duplicates"""
    if not text:
        return text
    
    print("🔍 Performing enhanced duplicate removal...")
    
    # Step 1: Split into sentences for better duplicate detection
    sentences = []
    current_sentence = ""
    
    for char in text:
        current_sentence += char
        if char in '.!?' and len(current_sentence.strip()) > 10:
            sentences.append(current_sentence.strip())
            current_sentence = ""
    
    if current_sentence.strip():
        sentences.append(current_sentence.strip())
    
    # Step 2: Remove duplicate sentences (exact and similar)
    unique_sentences = []
    seen_content = set()
    
    for sentence in sentences:
        # Clean sentence for comparison (remove HTML and normalize)
        clean_sentence = re.sub(r'<[^>]+>', '', sentence).strip().lower()
        clean_sentence = re.sub(r'\s+', ' ', clean_sentence)
        
        # Skip very short sentences
        if len(clean_sentence) < 15:
            unique_sentences.append(sentence)
            continue
        
        # Check for semantic similarity (word overlap)
        is_duplicate = False
        sentence_words = set(clean_sentence.split())
        
        for seen in seen_content:
            seen_words = set(seen.split())
            if len(sentence_words) > 0 and len(seen_words) > 0:
                overlap = len(sentence_words.intersection(seen_words)) / min(len(sentence_words), len(seen_words))
                if overlap > 0.8:  # 80% overlap = duplicate
                    print(f"🚫 Removed similar sentence: {clean_sentence[:60]}...")
                    is_duplicate = True
                    break
        
        if not is_duplicate:
            seen_content.add(clean_sentence)
            unique_sentences.append(sentence)
    
    # Step 3: Reconstruct text
    result = ' '.join(unique_sentences)
    
    # Step 4: Clean up any HTML issues
    result = re.sub(r'\s+', ' ', result)  # Normalize whitespace
    result = re.sub(r'(<h2[^>]*>[^<]*</h2>)\s*(<h2[^>]*>[^<]*</h2>)', r'\1\n\n\2', result)  # Space headers
    
    print("✅ Enhanced duplicate removal completed")
    return result

def ensure_proper_ending(text):
    """Ensure the text ends properly after the third section"""
    if not text:
        return text
    
    # Find the last occurrence of "Recommended next steps" section
    last_section_match = re.search(r'(<h2>Recommended next steps[^<]*</h2>.*?)(?=<h2>|$)', text, re.DOTALL | re.IGNORECASE)
    
    if last_section_match:
        # Keep everything up to and including the last section
        before_last = text[:last_section_match.start()]
        last_section = last_section_match.group(1)
        
        # Remove any content that might appear after the third section
        clean_text = before_last + last_section
        print("🔧 Ensured proper ending after third section")
        return clean_text.strip()
    
    return text

def generate_simple_fallback(text):
    """Simple fallback explanation if LLM is not available"""
    return f"""
    <h2>Medical Report Analysis</h2>
    <p>I've analyzed your medical report. Unfortunately, the advanced AI analysis is currently unavailable, 
    but I can confirm that your document has been processed and contains {len(text)} characters of medical text.</p>
    
    <p>For a detailed explanation of your medical report, please:</p>
    <ul>
        <li>Consult with your healthcare provider</li>
        <li>Ask your doctor to explain any medical terms you don't understand</li>
        <li>Request a follow-up appointment if you have concerns</li>
    </ul>
    
    <p><em>Note: This is a basic fallback response. For comprehensive medical analysis, 
    please ensure the AI service is properly configured.</em></p>
    """

def generate_llm_summary(text):
    """Use Groq's LLM to generate a better summary of medical text"""
    try:
        # Create a prompt that instructs the model exactly what we want
        messages = [
            {
                "role": "system", 
                "content": """You are an advanced medical assistant helping patients understand their medical reports.
                Your task is to explain medical reports in clear, accessible language while providing valuable context and education.
                
                STRICT OUTPUT FORMAT - EXACTLY 3 SECTIONS:
                
                1. <h2>What the report is telling you – in plain language</h2>
                   [Write your explanation here - NO repetition allowed]
                
                2. <h2>What this means for your health</h2>
                   [Write health implications here - must be completely different from section 1]
                
                3. <h2>Recommended next steps</h2>
                   [Write recommendations here - must be unique content]
                
                ABSOLUTELY CRITICAL RULES - VIOLATION WILL CAUSE ERRORS:
                - Write EXACTLY 3 sections with the exact headings above
                - Each section must contain COMPLETELY UNIQUE content
                - NEVER repeat any sentence, phrase, or medical information between sections
                - STOP WRITING immediately after section 3 is complete
                - Do NOT add any additional text, summaries, or conclusions
                - Each paragraph within a section must be unique
                - If you find yourself repeating content, DELETE the repetition
                - Use HTML formatting: <p>, <h2>, <strong>, <em>
                - Highlight medical terms: <strong style="color: #00b3b3;">term</strong>
                
                DUPLICATION CHECK: Before finishing, scan your entire response:
                - Are any sentences repeated? DELETE them.
                - Are any medical facts mentioned twice? DELETE the duplication.
                - Does any section repeat information from another? REWRITE to be unique.
                
                Remember: Quality over quantity. Better to have shorter, unique content than longer, repetitive content.
                """
            },
            {
                "role": "user",
                "content": f"""Please analyze this medical report and provide a comprehensive explanation following the exact format specified:

MEDICAL REPORT TEXT:
{text}

Remember to:
- Use the exact section headings I specified
- Explain ALL medical terminology found in the report
- Provide practical health guidance
- Use proper HTML formatting for web display
"""
            }
        ]
        
        print("📤 Sending request to Groq API using new client...")
        try:
            # Using the new Groq client with the GPT-OSS-120B model
            completion = groq_client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=messages,
                temperature=0.1,  # Very low temperature for more deterministic output
                max_completion_tokens=800,  # Reduced to prevent overly long responses
                top_p=0.8,  # More focused responses
                reasoning_effort="medium",
                stream=False
            )
            
            # Extract the response
            summary = completion.choices[0].message.content
            print("✅ Successfully received AI explanation")
            
            # Remove any duplicate content and ensure proper truncation
            cleaned_summary = remove_duplicate_content(summary)
            
            # Ensure content stops after the third section
            final_summary = ensure_proper_ending(cleaned_summary)
            return final_summary
            
        except Exception as api_error:
            print(f"❌ Groq API error with GPT-OSS-120B: {str(api_error)}")
            # Fall back to another model if GPT-OSS-120B isn't available
            try:
                print("⚠️ Falling back to llama3-8b-8192 model...")
                completion = groq_client.chat.completions.create(
                    model="llama3-8b-8192",
                    messages=messages,
                    temperature=0.1,  # Low temperature for consistency
                    max_tokens=800,  # Reduced token limit
                    top_p=0.8
                )
                summary = completion.choices[0].message.content
                print("✅ Successfully received AI explanation from fallback model")
                
                # Remove any duplicate content and ensure proper truncation
                cleaned_summary = remove_duplicate_content(summary)
                final_summary = ensure_proper_ending(cleaned_summary)
                return final_summary
                
            except Exception as fallback_error:
                print(f"❌ Fallback model error: {str(fallback_error)}")
                # Try one more fallback
                try:
                    print("⚠️ Trying final fallback: gemma2-9b-it...")
                    completion = groq_client.chat.completions.create(
                        model="gemma2-9b-it",
                        messages=messages,
                        temperature=0.1,  # Low temperature for consistency
                        max_tokens=800,  # Reduced token limit
                        top_p=0.8
                    )
                    summary = completion.choices[0].message.content
                    print("✅ Successfully received AI explanation from final fallback model")
                    
                    # Remove any duplicate content and ensure proper truncation
                    cleaned_summary = remove_duplicate_content(summary)
                    final_summary = ensure_proper_ending(cleaned_summary)
                    return final_summary
                except:
                    print("❌ All LLM models failed")
                    return None
    
    except Exception as e:
        print(f"❌ LLM summarization error: {str(e)}")
        return None

def explain_text(text):
    """Main function to explain medical text using LLM"""
    try:
        # Check if text exists
        if not text or len(text.strip()) < 20:
            return "I couldn't find any legible text in this document. Please check if the file is clear and contains actual text content."

        # Clean OCR junk
        cleaned_text = re.sub(r"[^\x00-\x7F]+", " ", text)
        cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()

        # Check if text is empty after cleaning
        if not cleaned_text:
            return "I couldn't find any legible text in this document. Please check if the image is clear and try again."
        
        print(f"📄 Document text length: {len(cleaned_text)} characters")
        
        # Directly use the LLM for all medical report analysis
        if GROQ_API_KEY and GROQ_API_KEY != "your-api-key-here":
            try:
                print("🔍 Using LLM for analysis...")
                # Send the document directly to the LLM
                llm_summary = generate_llm_summary(cleaned_text[:8000])  # Limiting to 8000 chars for API limit
                
                if llm_summary and len(llm_summary) > 100:  # Ensure we got a real summary
                    return llm_summary
                    
                print("⚠️ LLM returned empty or very short summary, using fallback")
                return generate_simple_fallback(cleaned_text)
                
            except Exception as e:
                print(f"⚠️ LLM summarization failed: {str(e)}")
                return generate_simple_fallback(cleaned_text)
        else:
            # No API key, use our simple fallback
            print("⚠️ No valid GROQ_API_KEY found, using simple fallback")
            return generate_simple_fallback(cleaned_text)
                
    except Exception as e:
        print("❌ Error during summarization:", str(e))
        return "I encountered an issue while analyzing this medical report. Please make sure the image is clear and contains readable medical information."

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
