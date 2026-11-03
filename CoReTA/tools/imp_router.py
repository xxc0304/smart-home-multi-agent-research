"""Paper-rule implementation, not official IMP code. No model/API access."""
import math
import re

VERSION='imp-source-unit-idf/1'

def words(text):
    return set(re.findall(r'[a-z0-9]+',text.casefold()))

def sentences(text):
    return [x for x in re.split(r'(?<=[.!?])\s+|\n+',text) if x.strip()]

def match(message,owned_refs,documents,question):
    """C.1 thresholds; whole source records are units, explicitly an adaptation."""
    vocabulary={ref:words(doc['content']) for ref,doc in documents.items()}
    df={w:sum(w in tokens for tokens in vocabulary.values()) for w in set().union(*vocabulary.values())}
    idf={w:math.log((len(documents)+1)/(n+0.5)) for w,n in df.items()}
    question_words=words(question);segments=[words(s) for s in sentences(message)]
    found=[];details=[]
    for ref in owned_refs:
        tokens=vocabulary[ref];weight=sum(idf[w] for w in tokens)
        if not tokens:continue
        for segment in segments:
            overlap=tokens&segment
            rare={w for w in overlap if df[w]<=2}
            fraction=sum(idf[w] for w in overlap)/weight
            if fraction>=0.5 or len(rare)>=2 and bool(rare-question_words):
                found.append(ref);details.append(dict(ref=ref,weighted_coverage=fraction,rare_words=sorted(rare)))
                break
    return found,details

def route(receiver_owned,sender_cumulative,documents):
    union=set().union(*(set(x) for x in sender_cumulative.values())) if sender_cumulative else set()
    refs=[ref for ref in documents if ref in union and ref not in receiver_owned]
    return [dict(documents[ref]) for ref in refs]
