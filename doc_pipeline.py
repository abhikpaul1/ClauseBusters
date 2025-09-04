import PyPDF2
import spacy
import requests
import json
import io

def extract_text_from_pdf(pdf_source) -> str:
    """
    Extracts all text from a PDF file from a given source.
    The source can be a file path (str) or a file-like object (e.g., BytesIO).

    Args:
        pdf_source: The path to the PDF file or a file-like object.

    Returns:
        A single string containing all the text from the PDF.
    """
    print(f"--- Starting extraction ---")
    try:
        if isinstance(pdf_source, str):
            # If the source is a string, open the file
            with open(pdf_source, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() or ""
                return text
        else:
            # If the source is a BytesIO object, read from it directly
            reader = PyPDF2.PdfReader(pdf_source)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text
            
    except FileNotFoundError:
        print(f"Error: The file at '{pdf_source}' was not found.")
        return ""
    except Exception as e:
        print(f"An unexpected error occurred during PDF extraction: {e}")
        return ""

def analyze_text_with_spacy(text: str):
    """
    Performs NLP analysis on the extracted text using the spaCy library.

    Args:
        text: The string of text to analyze.

    Returns:
        A spaCy Doc object, or None if the text is empty.
    """
    print("--- Starting NLP analysis with spaCy ---")
    if not text:
        print("No text provided for analysis.")
        return None
    
    # Load the small English model
    try:
        nlp = spacy.load("en_core_web_sm")
        doc = nlp(text)
        return doc
    except OSError:
        print("SpaCy model not found. Please run 'python -m spacy download en_core_web_sm' to install it.")
        return None
    except Exception as e:
        print(f"An error occurred during spaCy analysis: {e}")
        return None

def extract_entities_and_keywords(doc) -> tuple:
    """
    Extracts named entities and common keywords from a spaCy Doc object.

    Args:
        doc: A spaCy Doc object.

    Returns:
        A tuple containing a dictionary of unique entities and a list of unique keywords.
    """
    print("--- Extracting entities and keywords ---")
    if not doc:
        return {}, []

    # Use a dictionary to store unique entities by their label
    entities = {}
    for ent in doc.ents:
        if ent.label_ not in entities:
            entities[ent.label_] = []
        entities[ent.label_].append(ent.text)
    
    # Remove duplicates from the entity lists
    for label in entities:
        entities[label] = list(set(entities[label]))

    # Extract keywords, filtering for nouns and proper nouns to find key concepts
    keywords = [token.text for token in doc if token.pos_ in ["NOUN", "PROPN"]]
    
    return entities, list(set(keywords))

def summarize_text_with_gemini(text: str) -> str:
    """
    Calls the Gemini API to generate a summary of the provided text.
    """
    api_key = "" # Replace with your actual Gemini API key
    if not api_key:
        print("API key is not set. Skipping summarization.")
        return "API key not configured."

    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={api_key}"
    
    # Construct the payload for the API request
    payload = {
        "contents": [{"parts": [{"text": f"Summarize the following legal document content in a single paragraph, focusing on key clauses and agreements:\n\n{text}"}]}]
    }

    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(api_url, headers=headers, data=json.dumps(payload))
        response.raise_for_status() # Raise an error for bad status codes
        
        result = response.json()
        
        # Extract the generated text from the response
        generated_text = result['candidates'][0]['content']['parts'][0]['text']
        return generated_text
        
    except requests.exceptions.RequestException as e:
        print(f"API call failed: {e}")
        return "Summarization service is unavailable."
    except (KeyError, IndexError) as e:
        print(f"Error parsing API response: {e}")
        return "Failed to parse API response."

def main_pipeline(pdf_path: str):
    """
    Main function to orchestrate the document processing pipeline.
    """
    # Step 1: Extract text
    extracted_text = extract_text_from_pdf(pdf_path)
    if not extracted_text:
        return

    # Step 2: Analyze text with spaCy
    doc = analyze_text_with_spacy(extracted_text)
    
    # Step 3: Extract key information (entities and keywords)
    entities, keywords = extract_entities_and_keywords(doc)

    # Step 4: Summarize with Gemini API
    summary = summarize_text_with_gemini(extracted_text)
    
    # Display all results
    print("\n--- Document Analysis Complete! ---")
    print(f"\nDocument Summary:\n{summary}")
    print("\nExtracted Named Entities:")
    for label, entity_list in entities.items():
        print(f"  {label}:")
        for entity in entity_list:
            print(f"    - {entity}")

    print("\nExtracted Keywords:")
    print("  " + ", ".join(sorted(keywords)))

# Example usage of the pipeline:
if __name__ == "__main__":
    # Replace 'your_document.pdf' with the actual path to your PDF file.
    # Make sure the file exists in the same directory as this script.
    main_pipeline('your_document.pdf')
