import io
import PyPDF2
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from doc_pipeline import extract_text_from_pdf, analyze_text_with_spacy, extract_entities_and_keywords, summarize_text_with_gemini

# --- Dummy PDF Creation Function ---
# This function creates a test PDF in memory to pass to your pipeline.
def create_dummy_pdf() -> io.BytesIO:
    """
    Creates a simple PDF file in memory with legal-like text for testing.
    """
    print("--- Creating a dummy PDF for testing ---")
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    legal_text = (
        "This Agreement is made as of this 4th day of September, 2025, by and between "
        "the Plaintiff, John Doe, and the Defendant, Acme Corporation, Inc. "
        "The Parties hereby agree to the following terms and conditions: "
        "1. CONFIDENTIALITY. Both Parties agree to maintain strict confidentiality. "
        "2. JURISDICTION. This contract shall be governed by the laws of New York. "
        "3. PAYMENT. A sum of $50,000 shall be paid to the Plaintiff."
        "The purpose of this agreement is for the settlement of all claims."
    )
    
    c.drawString(100, 750, "CONFIDENTIAL AGREEMENT")
    c.setFont("Helvetica", 12)
    textobject = c.beginText(100, 720)
    textobject.textLines(legal_text.splitlines())
    c.drawText(textobject)
    c.save()
    
    buffer.seek(0)
    return buffer

# --- Main Test Script ---
if __name__ == "__main__":
    # The API key must be set in the original document_pipeline.py file
    
    # Create the in-memory PDF
    dummy_pdf_stream = create_dummy_pdf()
    
    # Use the pipeline functions from your main script
    extracted_text = extract_text_from_pdf(dummy_pdf_stream)
    if not extracted_text:
        print("Test failed: No text extracted.")
    else:
        # Step 2: Analyze text with spaCy
        doc = analyze_text_with_spacy(extracted_text)
        
        # Step 3: Extract key information (entities and keywords)
        entities, keywords = extract_entities_and_keywords(doc)

        # Step 4: Summarize with Gemini API
        summary = summarize_text_with_gemini(extracted_text)
        
        print("\n--- Document Analysis Complete! ---")
        print(f"\nDocument Summary:\n{summary}")
        print("\nExtracted Named Entities:")
        for label, entity_list in entities.items():
            print(f"  {label}:")
            for entity in entity_list:
                print(f"    - {entity}")

        print("\nExtracted Keywords:")
        print("  " + ", ".join(sorted(keywords)))

    
