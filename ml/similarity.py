import numpy as np
import pandas as pd

def find_similar_claims(input_vector: np.ndarray, top_k: int = 5) -> pd.DataFrame:
    history    = pd.read_pickle("data/claim_history.pkl")
    embeddings = np.load("data/embeddings.npy")

    norm_input   = input_vector / (np.linalg.norm(input_vector) + 1e-10)
    norms        = np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-10
    similarities = (embeddings / norms) @ norm_input

    history = history.copy()
    history["similarity"] = similarities
    top = history.nlargest(top_k, "similarity")

    return top[[
        "claim_amount", "injury_involved", "num_parties",
        "fraud_score", "severity_score", "litigation_score",
        "similarity"
    ]].round(3)
