import spacy
from spacy.training.example import Example
from spacy.util import minibatch, compounding

import random
from pathlib import Path

from training_data import TRAIN_DATA

MODEL_DIR = Path("model")/"tax_intent_cat"


def create_nlp_pipeline():

    nlp = spacy.blank("en")

    if not "textcat" in nlp.pipe_names:
        textcat = nlp.add_pipe("textcat", last=True)
    
    labels = ["client_entertainment", "rent_and_utilities", "salaries_and_visas", "marketing_and_ads", "fines_and_penalties"]


    for label in labels:
        textcat.add_label(label)
    
    return nlp



def train(nlp, training_data, n_iter=20):

    examples = []

    # Create Example objects
    for text, ann in training_data:
        doc = nlp.make_doc(text)
        
        examples.append(Example.from_dict(doc, {"cats": ann["cats"]}))

    # Start training
    optimizer = nlp.initialize(lambda:examples)

    # Training loop
    for epoch in range(n_iter):
        random.shuffle(examples)
        losses = {}

        # Batching to compound
        batches = minibatch(examples, size=compounding(4.0, 32, 1.001))
        for batch in batches:
            nlp.update(batch, sgd=optimizer, losses=losses)
        
        print(f"Epoch: {epoch+1}, Losses: {losses.get('textcat', 0.0):.2f}")

    # Save and upload to disk
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    nlp.to_disk(MODEL_DIR)

    print(f"Model trainded and saved to {MODEL_DIR.resolve()}")


if __name__ == "__main__":
    nlp = create_nlp_pipeline()
    train(nlp=nlp, training_data=TRAIN_DATA, n_iter=20)
        