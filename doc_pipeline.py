import PyPDF2
import spacy

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts all text from a PDF file.

    Args:
        pdf_path: The file path to the PDF document.

    Returns:
        A single string containing all the text from the PDF.
    """
    print(f"--- Starting extraction from '{pdf_path}' ---")
    try:
        # 'rb' mode is for reading binary files
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            # Iterate through each page and extract text
            for page in reader.pages:
                extracted_text = page.extract_text()
                # Use a safeguard in case a page has no extractable text
                if extracted_text:
                    text += extracted_text + "\n"
            return text
    except FileNotFoundError:
        print(f"Error: The file at '{pdf_path}' was not found. Please check the file path.")
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
    if not doc:
        return

    # Step 3: Extract and print key information
    entities, keywords = extract_entities_and_keywords(doc)
    
    print("\n--- Document Analysis Complete! ---")
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
