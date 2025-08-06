import pandas as pd
import gdown
import streamlit as st

st.write("✅ La tua app è viva!")

# 1️⃣ Inserisci qui l’ID del tuo file Google Drive
FILE_ID = "19YgqxihKo98iBvcqpzjcj8DQ3nmJh8BJ"  
OUTPUT_FILE = "frequenze.xlsx"

# 2️⃣ Costruisci l’URL “downloadabile” e scarica il file
url = f"https://drive.google.com/uc?id={FILE_ID}"
print(f"Scarico da: {url} …")
gdown.download(url, OUTPUT_FILE, quiet=False)

# 3️⃣ Leggi con pandas e mostrami le prime 10 righe
df = pd.read_excel(OUTPUT_FILE)
print("\n--- Contenuto del DataFrame ---")
print(df.head(10))   # usa df per vedere tutto o df.head(n) per n righe

