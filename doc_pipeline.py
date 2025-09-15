import os
import time
import json
import hashlib
from typing import Dict, Optional
import PyPDF2
import google.generativeai as genai
from collections import deque

class RateLimiter:
    def __init__(self, max_calls_per_minute=15):
        self.calls = deque()
        self.max_calls = max_calls_per_minute
    
    def can_call(self):
        now = time.time()
        # Remove calls older than 1 minute
        while self.calls and self.calls[0] < now - 60:
            self.calls.popleft()
        return len(self.calls) < self.max_calls
    
    def record_call(self):
        self.calls.append(time.time())
    
    def wait_if_needed(self):
        if not self.can_call():
            wait_time = 60 - (time.time() - self.calls[0])
            print(f"⏳ Rate limit reached. Waiting {wait_time:.1f} seconds...")
            time.sleep(wait_time)

class DocumentProcessor:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        self.rate_limiter = RateLimiter()
        
        # Legal keywords to detect legal queries
        self.legal_keywords = [
            'legal advice', 'sue', 'lawsuit', 'court', 'attorney', 'lawyer',
            'legal rights', 'liability', 'legal action', 'legal opinion'
        ]
        
        # Cache for processed documents
        self.doc_cache = {}
        
    def extract_pdf_text(self, pdf_path: str) -> str:
        """Extract text from PDF"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
        except Exception as e:
            raise Exception(f"Error reading PDF: {e}")
    
    def get_doc_hash(self, text: str) -> str:
        """Generate hash for caching"""
        return hashlib.md5(text.encode()).hexdigest()[:12]
    
    def is_legal_query(self, query: str) -> bool:
        """Check if query is asking for legal advice"""
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in self.legal_keywords)
    
    def process_document(self, pdf_path: str) -> Dict:
        """Process PDF with single API call"""
        print("📄 Extracting text from PDF...")
        text = self.extract_pdf_text(pdf_path)
        
        # Check cache
        doc_hash = self.get_doc_hash(text)
        if doc_hash in self.doc_cache:
            print("✅ Using cached results")
            return self.doc_cache[doc_hash]
        
        print("🤖 Processing with AI...")
        self.rate_limiter.wait_if_needed()
        
        prompt = f"""
        Analyze this document and provide:
        1. A brief summary (2-3 sentences)
        2. Key concepts with simple explanations
        3. Simplified version of complex content
        
        IMPORTANT: Do not provide legal advice. For legal documents, only explain structure and general concepts.
        
        Text: {text[:8000]}...
        
        Respond in JSON format:
        {{
            "summary": "brief summary here",
            "key_concepts": {{"term1": "simple explanation", "term2": "simple explanation"}},
            "simplified_content": "rewritten content in simple language",
            "is_legal_document": true/false
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            self.rate_limiter.record_call()
            
            # Parse JSON response
            content = response.text.strip()
            if content.startswith('```json'):
                content = content[7:-3]
            elif content.startswith('```'):
                content = content[3:-3]
            
            result = json.loads(content)
            result['doc_hash'] = doc_hash
            
            # Cache result
            self.doc_cache[doc_hash] = result
            
            return result
            
        except Exception as e:
            print(f"❌ AI processing error: {e}")
            return {
                "summary": "Error processing document",
                "key_concepts": {},
                "simplified_content": text[:1000] + "...",
                "is_legal_document": False,
                "doc_hash": doc_hash
            }
    
    def answer_query(self, processed_doc: Dict, query: str) -> str:
        """Answer query with minimal API usage"""
        
        # Block legal advice queries
        if self.is_legal_query(query):
            return "⚠️ I cannot provide legal advice. Please consult a qualified attorney for legal matters."
        
        # Add legal disclaimer for legal documents
        disclaimer = ""
        if processed_doc.get('is_legal_document'):
            disclaimer = "⚠️ Legal Disclaimer: This is for informational purposes only, not legal advice.\n\n"
        
        # Try to answer from cached data first
        query_lower = query.lower()
        
        # Check for summary requests
        if any(word in query_lower for word in ['summary', 'about', 'main', 'purpose']):
            return disclaimer + f"📝 Summary: {processed_doc['summary']}"
        
        # Check for key concepts
        if 'concept' in query_lower or 'term' in query_lower or 'definition' in query_lower:
            concepts = processed_doc['key_concepts']
            if concepts:
                result = "🔍 Key Concepts:\n"
                for term, explanation in concepts.items():
                    result += f"• {term}: {explanation}\n"
                return disclaimer + result
            
        # Check for simplified content request
        if any(word in query_lower for word in ['simple', 'explain', 'understand', 'clarify']):
            return disclaimer + f"💡 Simplified: {processed_doc['simplified_content'][:500]}..."
        
        # For specific/complex queries, use AI
        return self._ai_query(processed_doc, query, disclaimer)
    
    def _ai_query(self, processed_doc: Dict, query: str, disclaimer: str) -> str:
        """Use AI for complex queries"""
        self.rate_limiter.wait_if_needed()
        
        prompt = f"""
        Based on this document information, answer the user's question.
        Do NOT provide legal advice.
        
        Document Summary: {processed_doc['summary']}
        Key Concepts: {processed_doc['key_concepts']}
        
        User Question: {query}
        
        Provide a helpful, factual answer based only on the document information.
        """
        
        try:
            response = self.model.generate_content(prompt)
            self.rate_limiter.record_call()
            return disclaimer + f"💬 {response.text.strip()}"
        except Exception as e:
            return disclaimer + f"❌ Sorry, I couldn't process that query. Here's the summary: {processed_doc['summary']}"

def main():
    print("🚀 AI Document Processor")
    print("=" * 40)
    
    
    api_key = "AIzaSyCu1WqC4PE1uO2VhQ5ODK22JpAUDPgNuhg"  # Replace with your actual API key
    
    if api_key != "AIzaSyCu1WqC4PE1uO2VhQ5ODK22JpAUDPgNuhg":
        print("❌ Please set your Gemini API key in the code")
        return
    
    processor = DocumentProcessor(api_key)
    
    # Get PDF path from user
    pdf_path = input("📁 Enter PDF file path: ").strip().strip('"')
    
    if not os.path.exists(pdf_path):
        print("❌ File not found!")
        return
    
    try:
        # Process document
        result = processor.process_document(pdf_path)
        
        print("\n" + "=" * 50)
        print("✅ DOCUMENT PROCESSED")
        print("=" * 50)
        
        if result.get('is_legal_document'):
            print("⚠️  Legal document detected - no legal advice will be provided")
        
        print(f"\n📄 SUMMARY:")
        print(result['summary'])
        
        if result['key_concepts']:
            print(f"\n🔍 KEY CONCEPTS:")
            for term, explanation in result['key_concepts'].items():
                print(f"• {term}: {explanation}")
        
        # Q&A Loop
        print(f"\n❓ ASK QUESTIONS (type 'quit' to exit)")
        print("-" * 30)
        
        while True:
            question = input("\nYour question: ").strip()
            if question.lower() in ['quit', 'exit', 'q']:
                break
                
            if question:
                answer = processor.answer_query(result, question)
                print(f"\n{answer}")
        
        print("\n👋 Goodbye!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
