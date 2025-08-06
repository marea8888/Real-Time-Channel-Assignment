import pandas as pd
import gdown

FILE_ID = "1wlZmgpW0SGpbqEyt_b5XYT8lXgQUTYmo"
OUTPUT_FILE = "frequenze.xlsx"

# Scarica il file
url = f"https://drive.google.com/uc?id={FILE_ID}"
gdown.download(url, OUTPUT_FILE, quiet=False)

# Leggi solo il foglio "ALL NP"
df = pd.read_excel(OUTPUT_FILE, sheet_name="ALL NP")

# Stampalo in console
print("\n--- Contenuto del foglio ALL NP ---")
print(df)


