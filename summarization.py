# utils/summarization.py

import os
import re
from groq import Groq

# Set your Groq API key - better to use environment variables in production
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "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")
groq_client = Groq(api_key=GROQ_API_KEY)

# Simple duplicate removal function
def remove_duplicate_content(text):
    """Simple duplicate removal - splits by lines and removes exact duplicates"""
    if not text:
        return text
    
    print("🔍 Performing simple duplicate removal...")
    
    lines = text.split('\n')
    unique_lines = []
    seen_lines = set()
    
    for line in lines:
        clean_line = line.strip()
        if clean_line and clean_line not in seen_lines:
            seen_lines.add(clean_line)
            unique_lines.append(line)
        elif not clean_line:  # Keep empty lines for formatting
            unique_lines.append(line)
        else:
            print(f"🚫 Removed duplicate line: {clean_line[:60]}...")
    
    result = '\n'.join(unique_lines)
    print("✅ Simple duplicate removal completed")
    return result

# Fallback function - only used if LLM fails
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
            
            # Remove any duplicate content
            cleaned_summary = remove_duplicate_content(summary)
            return cleaned_summary
            
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
                
                # Remove any duplicate content
                cleaned_summary = remove_duplicate_content(summary)
                return cleaned_summary
                
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
                    
                    # Remove any duplicate content
                    cleaned_summary = remove_duplicate_content(summary)
                    return cleaned_summary
                except:
                    print("❌ All LLM models failed")
                    return None
    
    except Exception as e:
        print(f"❌ LLM summarization error: {str(e)}")
        return None

def explain_text(text):
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
        # No need for regex extraction since the LLM can understand the document structure
        if GROQ_API_KEY and GROQ_API_KEY != "your-api-key-here":
            try:
                print("🔍 Using LLM for analysis...")
                # Send the document directly to the LLM
                llm_summary = generate_llm_summary(cleaned_text[:8000])  # Limiting to 8000 chars for API limit
                
                if llm_summary and len(llm_summary) > 100:  # Ensure we got a real summary
                    return llm_summary
                    
                print("⚠️ LLM returned empty or very short summary, using fallback")
                # Only in case of LLM failure, fall back to the simple fallback
                return generate_simple_fallback(cleaned_text)
                
            except Exception as e:
                print(f"⚠️ LLM summarization failed: {str(e)}")
                # Fall back to our simple fallback in case of LLM failure
                return generate_simple_fallback(cleaned_text)
        else:
            # No API key, use our simple fallback
            print("⚠️ No valid GROQ_API_KEY found, using simple fallback")
            return generate_simple_fallback(cleaned_text)
                
    except Exception as e:
        print("❌ Error during summarization:", str(e))
        return "I encountered an issue while analyzing this medical report. Please make sure the image is clear and contains readable medical information."
