
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
import re
import pickle
from datetime import datetime
from speech.training_data import *


def train():

    model = make_pipeline(CountVectorizer(), MultinomialNB())
    model.fit(sentences, labels)

    return model

def save(model, filepath):
    print(f"Saving model to {filepath}...")

    with open(filepath,'wb') as f:
        pickle.dump(model,f)

    print(f"Saved model to {filepath}.")

def load(filepath):
    print(f"Loading model from {filepath}...")
    with open(filepath, 'rb') as f:
        model = pickle.load(f)
    print(f"Done.")
    return model


if __name__ == "__main__":
    import sys

    filepath = sys.argv[1] if len(sys.argv) > 1 else "model.pkl"

    print("Training...", flush=True)
    start = datetime.now()

    model = train()
    save(model, filepath)

    end = datetime.now()
    print(f"Done. {end - start}")
