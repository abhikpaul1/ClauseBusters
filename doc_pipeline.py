import PyPDF2
import spacy
import requests
import json
import io
import sys
from requests.exceptions import Timeout, RequestException

# Pre-load the spaCy model once for efficiency
try:
    NLP_MODEL = spacy.load("en_core_web_sm")
except OSError:
    print("SpaCy model not found. Please run 'python -m spacy download en_core_web_sm' to install it.")
    sys.exit(1)

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
            with open(pdf_source, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() or ""
                return text
        else:
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
    Performs NLP analysis on the extracted text using the spaCy model.
    The model is loaded once at the start of the script for efficiency.
    
    Args:
        text: The string of text to analyze.

    Returns:
        A spaCy Doc object, or None if the text is empty.
    """
    print("--- Starting NLP analysis with spaCy ---")
    if not text:
        print("No text provided for analysis.")
        return None
    
    try:
        doc = NLP_MODEL(text)
        return doc
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

    entities = {}
    for ent in doc.ents:
        if ent.label_ not in entities:
            entities[ent.label_] = []
        entities[ent.label_].append(ent.text)
    
    for label in entities:
        entities[label] = list(set(entities[label]))

    keywords = [token.text for token in doc if token.pos_ in ["NOUN", "PROPN"]]
    
    return entities, list(set(keywords))

def summarize_text_with_gemini(text: str) -> str:
    """
    Calls the Gemini API to generate a summary of the provided text.
    """
    api_key = "AIzaSyCu1WqC4PE1uO2VhQ5ODK22JpAUDPgNuhg"
    if not api_key:
        print("API key is not set. Skipping summarization.")
        return "API key not configured."

    # Define a custom safety prompt for simplification
    safety_prompt = (
        "You are a helpful legal document assistant. Your task is to summarize the provided "
        "document. Explain the key clauses and agreements in a simple, jargon-free paragraph. "
        "Do not provide any legal advice, legal opinion, or take a legal position. "
        "Do not offer guidance on how to interpret or act on the document. "
    )

    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={api_key}"
    
    payload = {
        "contents": [{"parts": [{"text": safety_prompt + "Summarize the following legal document content:\n\n" + text}]}]
    }
    headers = {'Content-Type': 'application/json'}
    
    timeout_seconds = 30
    
    try:
        response = requests.post(api_url, headers=headers, data=json.dumps(payload), timeout=timeout_seconds)
        response.raise_for_status() 
        
        result = response.json()
        
        generated_text = result['candidates'][0]['content']['parts'][0]['text']
        
        # A more robust safety filter check
        harmful_phrases = [
            "legal advice", "legal opinion", "I advise you", "I suggest you", "recommend you",
            "take this position", "your rights are", "it is my opinion that", "consult with a lawyer"
        ]
        if any(phrase in generated_text.lower() for phrase in harmful_phrases):
            return "The AI's response was flagged for containing potentially harmful content. No summary will be provided."

        return generated_text
        
    except Timeout:
        print("API call timed out.")
        return "Summarization service timed out."
    except RequestException as e:
        print(f"API call failed due to a network error: {e}")
        return "Summarization service is unavailable due to a network error."
    except (KeyError, IndexError) as e:
        print(f"Error parsing API response: The response structure was unexpected. {e}")
        return "Failed to parse API response."

def main_pipeline(pdf_path: str):
    """
    Main function to orchestrate the document processing pipeline.
    """
    extracted_text = extract_text_from_pdf(pdf_path)
    if not extracted_text:
        return

    doc = analyze_text_with_spacy(extracted_text)
    
    entities, keywords = extract_entities_and_keywords(doc)

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

if __name__ == "__main__":
    pdf_path = input("Please enter the path to your PDF file: ")
    if not pdf_path:
        print("No file path provided. Exiting.")
        sys.exit(1)
    
    main_pipeline(pdf_path)

