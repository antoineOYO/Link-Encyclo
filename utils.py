import re
from unidecode import unidecode
from stanza.models.common.doc import Span, Token

VOC_SAINT = f"sainte|saint|sant|san|st|s"
def is_saint(phrase):
    """
    Returns True if the phrase contains a token in the VOC_SAINT list
    """
    return bool(re.search(rf'\b({VOC_SAINT})\b', phrase))


def normalize_span(span, pos=['NOUN', 'PROPN', 'ADJ'], stop_words=None):
    """
    Input :
    - span : Stanza Span instances (stanza.models.common.doc.Span)
    
    Normalizes these Spans by applying the following rules:

    - if you want to normalize a Proper Noun Phrase, set `pos`=[NOUN, 'PROPN', 'ADJ'] to remove words tagged with other Part Of Speech
    - if you want to normalize a Common Noun Phrase, set `pos`=[NOUN, 'PROPN'] to remove words tagged with other Part Of Speech
        - 'PROPN' because some nouns ('Bourg', 'Isle', 'Ville') are times to times tagged as 'PROPN' (because they are capitalized ?)
        - other issue still unremedied : for "isle" is tagged as "X" (out of vocabulary ?)
    Then string normalization is applied :
    - .lower(), unidecode() to each token
    - stopwords are removed based on the list `stop_words` because the POS tagging is not perfect
    - symbols and digits are removed

    Output :
    list of Stanza Span instances with new attribute .norm_text

    """

    norm_text = []

    # # if pattern for VOC_SAINT is found, we prepend 'saint'
    # if is_saint(unidecode(span.text.lower())):
    #     norm_text = ['saint']
    
    # keeping only tokens with the right POS
    norm_text.extend(
        [
            unidecode(word.text.lower()) for word in span.words \
                if word.upos in pos \
                    #and not is_saint(unidecode(word.text.lower()))                            
        ]
    )

    # remove stopwords
    norm_text = [token for token in norm_text if token not in stop_words]

    # remove symbols like '-' 
    norm_text = [re.sub(r'[^a-z\s]', ' ', token) for token in norm_text]

    norm_text = ' '.join(norm_text)
    
    # adding the new attribute
    span.norm_text = norm_text
    
    # special case : norm_text is empty
    # in that case, after looking at these cases, we decide to keep the original text
    # with 1 condtions : must not be a stopword
    # this helped conserving ~700 NPs
    if norm_text=='':
        if unidecode(span.text.lower()) not in stop_words:
            span.norm_text = unidecode(span.text.lower())
    
    if norm_text=='':
        return None

    return span

VOC_DETERMINANTS = f"les|l'|l|le|la|los"
VOC_PREPOSITIONS = f"des|del|de|du|d'|d"
VOC_SEPARATEURS = f"ou plûtôt|ou|aussi|et|autrement|&|on pourroit dire en françois"

def normalize_head(headphrase) :
    """
    Normalizes a headphrase by :
    - deleting all non-alphabetic characters
    - lowercasing + unidecoding 
    - deletes tokens based on a list of specific stopwords
    - prepending 'saint' if sanctity
    """

    norm_head = unidecode(headphrase).lower()
    norm_head = re.sub(r'[^a-z\s]', ' ', norm_head)

    norm_head = re.sub(rf'\b({VOC_SEPARATEURS})\b', ' ', norm_head)
    norm_head = re.sub(rf'\b({VOC_PREPOSITIONS})\b', ' ', norm_head)
    norm_head = re.sub(rf'\b({VOC_DETERMINANTS})\b', ' ', norm_head)

    #replace consecutive spaces by one space
    norm_head = re.sub(r'\s+', ' ', norm_head)

    # ensure we don't output a blank string
    if norm_head=='' or norm_head==' ':
        return headphrase
    
    # if pattern for VOC_SAINT is found, we delete it and prepend 'saint'
    if is_saint(unidecode(headphrase).lower()):
        norm_head = 'saint ' + re.sub(rf'\b({VOC_SAINT})\b', ' ', norm_head)
        
    return norm_head


from difflib import SequenceMatcher
def string_similarity(
        s1:str,
        s2:str,
        threshold:float = 0.95,
        shorten:int = 50
        )-> tuple[str,str,bool]:
    """ 
    Because ENCRRE's OCR and ARTFL's one have slight differences, we need to tolarate some differences.

    Compares two input strings, shortened at the first 50 caracters (`shorten` setting)

    Returns a tuple with the cleaned strings and a boolean indicating if they are similar enough
    if short is True, inspects only the 100 first caracters of each string
    """
    # Cleaning the strings
    s1_cleaned = unidecode(s1).lower().replace('\u200b', '').replace('\n', '')#.replace('  ', ' ').strip()
    s2_cleaned = unidecode(s2).lower().replace('\u200b', '').replace('\n', '')#.replace('  ', ' ').strip()
    s1_cleaned = re.sub(r'[^a-z\s]', '',s1_cleaned).replace('  ', ' ').strip()
    s2_cleaned = re.sub(r'[^a-z\s]', '',s2_cleaned).replace('  ', ' ').strip()

    if shorten :
        s1_cleaned = s1_cleaned[: min(shorten,min(len(s1_cleaned), len(s2_cleaned)))]
        s2_cleaned = s2_cleaned[: min(shorten,min(len(s1_cleaned), len(s2_cleaned)))]


    similarity_ratio = SequenceMatcher(None, s1_cleaned, s2_cleaned).ratio()

    return s1_cleaned, s2_cleaned, similarity_ratio >= threshold

