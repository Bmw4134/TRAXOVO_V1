
import pandas as pd
import openpyxl
import re
from supabase import create_client
from sentence_transformers import SentenceTransformer, util

import os
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_ANON_KEY")
supabase = create_client(supabase_url, supabase_key)
model = SentenceTransformer('all-MiniLM-L6-v2')

def clean_headers(df):
    df = df.dropna(how="all")
    df.columns = df.iloc[0] if df.iloc[0].astype(str).str.contains("Date|Time|Asset", case=False).any() else df.columns
    df = df[1:] if df.columns.equals(df.iloc[0]) else df
    return df.reset_index(drop=True)

def deduplicate_and_insert(df, table):
    new_records = []
    base_vectors = []
    base_rows = supabase.table(table).select("*").execute().data
    for row in base_rows:
        row_text = " ".join([str(v) for v in row.values()])
        base_vectors.append(model.encode(row_text))

    for i, row in df.iterrows():
        row_text = " ".join([str(v) for v in row.values()])
        row_vector = model.encode(row_text)
        if base_vectors:
            similarities = util.cos_sim(row_vector, base_vectors)
            max_sim = float(similarities.max())
            if max_sim < 0.90:
                new_records.append(row.to_dict())
        else:
            new_records.append(row.to_dict())

    if new_records:
        supabase.table(table).insert(new_records).execute()
        return f"{len(new_records)} new records inserted."
    else:
        return "No new records — all deduplicated."

def handle_upload(file_path, table):
    df = pd.read_excel(file_path)
    df = clean_headers(df)
    return deduplicate_and_insert(df, table)
