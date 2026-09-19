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


# Legal-form / boilerplate tokens to strip entirely before embedding. These add
# no distinguishing information for semantic similarity (many unrelated entities
# share "LLC", "Ltd", "JSC", etc.) and were causing short generic names to
# falsely cluster together in vector space based on shared corporate suffixes
# rather than actual name content. Includes tokens across the multiple
# languages/scripts present in the dataset (English, transliterated Ukrainian/
# Russian, Cyrillic).
SEMANTIC_STRIP_TOKENS = {
    # English / transliterated
    "ltd", "limited", "liability", "co", "company", "corp", "corporation",
    "inc", "incorporated", "llc", "gmbh", "jsc", "plc", "pjsc",
    "ojsc", "cjsc", "pte", "sa", "nv", "bv", "ag", "kg", "oao",
    "ooo", "zao", "pao", "tov", "tovarystvo", "obmezhenoiu",
    "vidpovidalnistiu", "aktsionerne", "tovarystvo", "pryvatne",
    "pidpryiemstvo",
    # Cyrillic equivalents (Ukrainian / Russian)
    "тов", "оао", "ооо", "зао", "пао", "товариство", "обмеженою",
    "відповідальністю", "акціонерне", "приватне", "підприємство",
    "общество", "ограниченной", "ответственностью",
}


def normalize_for_semantic(name: str) -> str:
    """
    Normalize text before embedding for semantic search. Unlike normalize()
    above (used for fuzzy matching, where legal suffixes are standardized but
    kept, since exact spelling distance still benefits from them), this strips
    legal-form boilerplate entirely so embeddings compare the substantive part
    of the name rather than shared corporate suffixes.

    Must be applied identically to both the stored entity texts (at embed/index
    time) and the incoming query text (at search time), otherwise the two sides
    are not comparable.
    """
    if not name:
        return ""
    text = unicodedata.normalize("NFKC", name)
    text = text.casefold()
    # Strip punctuation/quotes that wrap legal-form abbreviations
    text = re.sub(r'["\'""«»,\.\-]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()

    tokens = [t for t in text.split() if t not in SEMANTIC_STRIP_TOKENS]
    result = " ".join(tokens).strip()

    # Fallback: if stripping leaves nothing (name was ONLY boilerplate),
    # keep the original casefolded text rather than embedding an empty string.
    return result if result else text