import spacy
from sqlalchemy import create_engine

from scripts.tax_law import tax_law
from models import DocumentKnowledge, SessionLocal
from dotenv import load_dotenv
from services.ai_services import get_embedding
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

nlp = spacy.blank("en")

def get_overalpping_chunks(text: str, chunk_size, overlap):
    chunks = []
    step_size = chunk_size - overlap

    for i in range(0, len(text), step_size):
        chunk = text[i: i+chunk_size]
        chunks.append(chunk)
    
    return chunks

def set_law_to_db():
    chunks = get_overalpping_chunks(text=tax_law, chunk_size=1000, overlap=200) 
    db = SessionLocal()

    for i, piece in enumerate(chunks):
        

        # Check if embedding exists
        existing = db.query(DocumentKnowledge).filter(DocumentKnowledge.text == piece).first()

        if not existing:
            print(f"Now processing chunk {i + 1}")

            # Create vector for piece of text
            vector = get_embedding(text=piece)

            # Create a new row in document knowledge table
            new_entry = DocumentKnowledge(document_name="UAE_Tax_Law_2026", page_number=1, text=piece, embedding=vector)
            
            db.add(new_entry)
            db.commit()
            print(f"Saved chunk {i}")
        
        else:
            print(f"Skipping chunk {i}. Already exist.")

    db.close()

            
set_law_to_db()

