from __future__ import annotations
import re, hashlib

def clean_common_crawl_text(text):
    text=re.sub(r'<[^>]+>',' ',text); text=re.sub(r'https?://\S+',' ',text); text=re.sub(r'\s+',' ',text).strip(); return text

def quality_filter(text,min_words=5,max_symbol_fraction=0.25):
    words=text.split();
    if len(words)<min_words: return False
    sym=sum(not ch.isalnum() and not ch.isspace() for ch in text)/max(1,len(text))
    return sym <= max_symbol_fraction

def exact_deduplicate(texts):
    seen=set(); out=[]
    for t in texts:
        h=hashlib.sha1(t.encode()).hexdigest()
        if h not in seen: seen.add(h); out.append(t)
    return out

def redact_pii(text):
    text=re.sub(r'[\w.+-]+@[\w-]+\.[\w.-]+','<EMAIL>',text)
    text=re.sub(r'\b(?:\+?\d[\d\-\s]{7,}\d)\b','<PHONE>',text)
    return text
