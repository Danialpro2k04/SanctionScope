import pandas as pd
import requests
import json
import os
import argparse

def download_and_parse(url: str, output_path: str):
    print(f"Downloading data from {url}...")
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    raw_csv = "data/raw_targets.csv"
    with open(raw_csv, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            
    print("Reading and filtering CSV...")
    df = pd.read_csv(raw_csv, dtype=str).fillna("")
    print(f"Original shape: {df.shape}, Columns: {list(df.columns)}")
    
    # Filter to companies only
    target_types = {"Organization", "Company", "LegalEntity"}
    df = df[df["schema"].isin(target_types)]
    
    entities = []
    for _, row in df.iterrows():
        # OpenSanctions simplified CSV uses semicolons for array values
        aliases = [a.strip() for a in row["aliases"].split(";") if a.strip()]
        programs = [p.strip() for p in row["program_ids"].split(";") if p.strip()]
        
        entities.append({
            "entity_id": row["id"],
            "canonical_name": row["name"],
            "aliases": aliases,
            "entity_type": row["schema"],
            "country": row["countries"].split(";")[0] if row["countries"] else None,
            "sanctions_programs": programs,
            "source_dataset": "opensanctions_consolidated_sanctions"
        })
        
    print(f"Filtered to {len(entities)} company-type entities.")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(entities, f, ensure_ascii=False, indent=2)
    print(f"Saved to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True, help="URL to targets.simple.csv")
    args = parser.add_argument("--output", default="data/processed_entities.json")
    args = parser.parse_args()
    download_and_parse(args.url, args.output)