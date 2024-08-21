import re
from unidecode import unidecode
from stanza.models.common.doc import Span

VOC_SAINT = f"sainte|saint|sant|san|st|s"
def is_saint(phrase):
    """
    Returns True if the phrase contains a token in the VOC_SAINT list
    """
    return bool(re.search(rf'\b({VOC_SAINT})\b', phrase))


def normalize_phrase(nps, pos=['NOUN', 'PROPN', 'ADJ'], stop_words=None):
    """
    Input :
    - nps : list of Stanza Span instances (stanza.models.common.doc.Span)
    
    Normalizes Proper Nouns Phrases or Common Nouns Phrases by applying the following rules:

    - Proper Nouns : remove tokens different from [NOUN, 'PROPN', 'ADJ']
    - Common Nouns : remove tokens diffrent [NOUN, 'PROPN']
        we also add 'PROPN' because some nouns ('Bourg', 'Isle', 'Ville') are tagged as 'PROPN'
        other issue : for 'isle' we suspect a out-of-vocabulary issue :
        {"text": "isle", "upos": "X",}

    - detect if the phrase is a saint name and prepend 'saint' in that case        
    - apply lower(), unidecode() to each token
    - remove tokens in a list of stopwords to double-check
    - remove symbols and digits

    Output :
    list of Stanza Span instances with attribute .norm_text
    """
    for np in nps:
        norm_nps = []

        # if pattern for VOC_SAINT is found, we delete it and prepend 'saint'
        if is_saint(unidecode(np.text.lower())):
            norm_nps = ['saint']
            continue
        
        norm_nps.extend(
            [
                unidecode(word.text.lower()) for word in np.words \
                    if word.upos in pos \
                        and not is_saint(unidecode(word.text.lower()))                            
            ]
        )
        norm_nps = [token for token in norm_nps if token not in stop_words]

        norm_nps = [re.sub(r'[^a-z\s]', '', token) for token in norm_nps]
        norm_nps = ' '.join(norm_nps)
        np.norm_text = norm_nps
        #norm_nps.append(np)
    return nps

# def normalize_NC(ncs, NC_pos=['NOUN', 'PROPN'], stop_words=None):
#     """
#     Input :
#     - ncs : list of Stanza Span instances (stanza.models.common.doc.Span)
    
#     Normalizes **Noms Communs** Phrases by applying the following rules:
#     - remove tokens not tagged as [NOUN, 'PROPN'] = NC_pos.
#         we also add 'PROPN' because some nouns ('Bourg', 'Isle', 'Ville') are tagged as 'PROPN'
#         other issue : for 'isle' we suspect a out-of-vocabulary issue :
#             # {"text": "isle", "upos": "X",}
#     - apply lower(), unidecode() to each token
#     - remove tokens in a list of stopwords to ensure
#     - remove symbols and digits

#     Output :
#     list of Stanza Span instances with attribute .norm_text
#     """
#     for np in ncs:
#         norm_nps = []

#         # if pattern for VOC_SAINT is found, we delete it and prepend 'saint'
#         if is_saint(unidecode(np.text.lower())):
#             norm_nps = ['saint']
#             continue
        
#         norm_nps.extend(
#             [
#                 unidecode(word.text.lower()) for word in np.words \
#                     if word.upos in NP_pos \
#                         and not is_saint(unidecode(word.text.lower()))                            
#             ]
#         )
#         norm_nps = [token for token in norm_nps if token not in stop_words]

#         norm_nps = [re.sub(r'[^a-z\s]', '', token) for token in norm_nps]
#         norm_nps = ' '.join(norm_nps)
#         np.norm_text = norm_nps
#         #norm_nps.append(np)
#     return nps


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

