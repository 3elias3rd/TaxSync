import os
from openai import OpenAI
from sqlalchemy.orm import Session
from sqlalchemy import select
from models import DocumentKnowledge, Category
from fastapi import HTTPException, Request
from pathlib import Path
from spacy.language import Language

MODEL_DIR = Path("model")/"tax_intent_cat"


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_nlp(request: Request):
    return request.app.state.nlp

def get_embedding(text: str):
    # Clean the text to ensure newlines don't confuse the model
    clean_text = text.replace("\n", " ")

    response = client.embeddings.create(
        input = clean_text,
        model = "text-embedding-3-small"
    )

    return response.data[0].embedding

def get_relevant_chunks(query_text: str, db: Session, limit: int = 10):

    # Convert user input into text
    query_vector = get_embedding(text=query_text)
    
    results = db.query(DocumentKnowledge).order_by(DocumentKnowledge.embedding.cosine_distance(query_vector)).limit(limit).all()

    return results

def generate_answer(question: str, context):
    system_prompt = "You are a helpful UAE Tax Advisor. Use the provided law snippets to answer the user's question. If the answer isn't in the context, say you don't know. Do not make up laws."

    user_prompt = f"Context:\n{context}\n\nQuestion: {question}"

    response = client.chat.completions.create(model="gpt-4o-mini", messages=[
        {"role": "system", "content": system_prompt}, 
        {"role": "user", "content": user_prompt}
        ])   
        
    return response.choices[0].message.content

def get_category_id(text, nlp: Language, db: Session) -> int:
    doc = nlp(text)
    cats = doc.cats
    top_tabel = max(cats, key=cats.get)
        
    category_obj = db.scalar(select(Category).where(Category.name==top_tabel))

    if not category_obj:
            raise HTTPException(status_code=400, detail=f"AI predicted {top_tabel}, this label is not in DB")

    category_id = category_obj.id

    return category_id
