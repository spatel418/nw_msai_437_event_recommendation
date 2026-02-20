import numpy as np
import pandas as pd

venue_emb = np.load("venue_embeddings.npy")
event_emb = np.load("event_embeddings.npy")

venues = pd.read_csv("venues_with_text.csv")
events = pd.read_csv("events_with_text.csv")

print("Shapes:", venue_emb.shape, event_emb.shape)


scores = venue_emb[0] @ event_emb.T   

top = np.argsort(scores)[-5:][::-1]

print("\nVENUE:")
print(venues.loc[0, "venue_text"])

print("\nTop 5 matching events:")
for idx in top:
    print(f"{scores[idx]:.3f} | {events.loc[idx, 'name']}")