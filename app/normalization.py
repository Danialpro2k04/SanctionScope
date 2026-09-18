import unicodedata
import re

LEGAL_SUFFIXES = {
    "ltd": "limited", "limited": "limited",
    "co": "company", "company": "company",
    "corp": "corporation", "corporation": "corporation",
    "inc": "incorporated", "incorporated": "incorporated",
    "llc": "llc", "gmbh": "gmbh", "jsc": "jsc"
}

def normalize(name: str) -> str:
    if not name:
        return ""
    # 1. Unicode NFKC
    name = unicodedata.normalize("NFKC", name)
    # 2. Casefold
    name = name.casefold()
    # 3. Strip punctuation
    name = re.sub(r'[\.,\-]', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()
    
    # 4. Map legal suffixes
    tokens = name.split()
    if tokens:
        if tokens[-1] in LEGAL_SUFFIXES:
            tokens[-1] = LEGAL_SUFFIXES[tokens[-1]]
        name = " ".join(tokens)
        
    return name