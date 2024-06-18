from unidecode import unidecode
from stanza.models.common.doc import Span
import random
import pandas as pd


class Article:
    def __init__(self,
                 volume = None,
                 numero = None,
                 headword = None,
                 authors = None,
                 text = None, # concatenated text of the paragraphs
                 ):
        """
        :param volume: volume number
        :param numero: article number
        :param headword: headword of the article
        :param authors: list of authors
        :param text: concatenated text of the paragraphs

        """
        self.volume = volume
        self.numero = numero
        self.headword = headword
        self.authors = authors
        self.text = text

        self.hash = str(self.volume) + '/' + str(self.numero) + '/' + self.headword
        self.artfl  = 'https://artflsrv04.uchicago.edu/philologic4.7/encyclopedie0922/navigate/' + str(self.volume) + '/' + str(self.numero)

        # the parsing should be done with stanza
        # https://stanfordnlp.github.io/stanza/data_objects.html#parsetree
        # self.parsed should be the output of this parser
        self.parsed = None

        # the NER should be done with custom NER method
        # https://huggingface.co/GEODE/bert-base-french-cased-edda-ner 
        # self.ner is the output of the model
        self.ner = None

        self.nc1 = None
        self.nc1_ = None
        self.np1 = None
        self.np1_ = None
        self.np2 = None
        self.np2_ = None
        self.ncs = None
        self.nps = None

        self.gold_qid = None
        self.annotations = None

    def __repr__(self):
        return self.hash
        # return f"Volume {self.volume} - Numero {self.numero} - Authors : {self.authors}\n{self.text}"
    
    def _apply_pipeline(self, pipeline, skip_headword=False):
        """
        Apply the provided pipeline to the Article.text
        Returns an instance of the pipeline's output
        """
        start_index = 0
        if skip_headword:
            start_index = len(self.headword)
        doc = pipeline(self.text[start_index:])
        return doc
    
    
    def _enrich_stanzadoc(self):
        """
        We bring NER outputs into a Stanza doc :
        - we add the NER tag to each `Token` instance of the Stanza doc
        - we merge the contiguous tokens with the same NER into `Span` instances

        Returns the tuple (ncs, nps): 
        - ncs, list[Span] --> represents the NC_Spatial entities
        - nps, list[Span] --> represents the NP_Spatial entities
        """
        if not self.parsed:
            print("parse the article first")
        if not self.ner:
            print("apply the NER pipeline first")

        # 1st. we add the NER tag to each token
        for token in self.parsed.iter_tokens():
            related_token_pieces = [tp for tp in self.ner if tp['start'] >= token.start_char \
                                    and tp['end'] <= token.end_char]
            if related_token_pieces:
                token.ner = [token_piece['entity'] for token_piece in related_token_pieces][0]
            else:
                token.ner = 'O'  # Assign 'O' (Outside) if no NER tag is found
        
        # 2nd. we merge the contiguous tokens with the same NER into spans
        self.parsed.entities = []
        spans = []
        list_tokens = [token for token in self.parsed.iter_tokens()]
        current_span = []
        for i,token in enumerate(list_tokens):
            # either we extend current_span
            if not current_span or token.ner == current_span[-1].ner:
                current_span.append(token)
            # or we close it and start a new one
            else:
                whole_span = Span(tokens = current_span, type = current_span[-1].ner, doc=self.parsed)
                spans.append(whole_span)
                #print('span completed : ', whole_span.text, whole_span.type)    
                current_span = [token]
        ##############################################
        # we finally add the spans to the Stanza doc
        self.parsed.entities = spans
        ##############################################

        # 3rd. we keep only nouns in the first NC_Spatial entity
        NC_pos = ['NOUN']
        ##############################################
        # Finnaly we also add 'PROPN' because I noticed that some nouns are tagged as 'PROPN'
        # because they start with a capital letter 
        # in the sample, 'Bourg', 'Isle', 'Ville' and others were tagged 'PROPN'
        # for 'isle' we suspect a out-of-vocabulary issue :
        # {"text": "isle", "upos": "X",}
        NC_pos.append('PROPN')

        ncs = [entity for entity in self.parsed.entities if entity.type == 'NC_Spatial']
        nc1 = ncs[0] if ncs else None
        nc1_ = " ".join(word.text for word in nc1.words if word.upos in NC_pos) if nc1 else None
        if nc1_:
            nc1_ = unidecode(nc1_).lower()

        # Find NP_Spatial entities
        NP_pos = ['NOUN', 'PROPN', 'ADJ']
        nps = [entity for entity in self.parsed.entities if entity.type == 'NP_Spatial']
        fnp = [np for np in nps if nc1 and np.start_char > nc1.end_char] # NP after the 1st NC

        np1 = fnp[0] if len(fnp) > 0 else None
        np1_ = " ".join(word.text for word in np1.words if word.upos in NP_pos) if np1 else None
        if np1_:
            np1_ = unidecode(np1_).lower()

        np2 = fnp[1] if len(fnp) > 1 else None
        np2_ = " ".join(word.text for word in np2.words if word.upos in NP_pos) if np2 else None
        if np2_:
            np2_ = unidecode(np2_).lower()

        # Set attributes
        self.nc1 = nc1
        self.nc1_ = nc1_
        self.np1 = np1
        self.np1_ = np1_
        self.np2 = np2
        self.np2_ = np2_
        self.ncs = ncs
        self.nps = nps

        return ncs, nps
    

class Book:
    def __init__(self, list_of_articles=None):
        self.articles = list_of_articles if list_of_articles is not None else []

    def __repr__(self):
        return f"Book with {len(self.articles)} articles"
    
    def __iter__(self):
        return iter(self.articles)

    def __getitem__(self, index):
        return self.articles[index]
    
    
    def _sample(self, n):
        return random.sample(self.articles, n)

    
    def _reach_article(self, volume = None, numero  = None, headword=None):
        for art in self.articles:
            if headword:
                if art.headword.lower() == headword.lower():
                    return art
            elif art.volume == volume and art.numero == numero:
                return art
        return None
    
    
    def _to_dataframe(self):
        return pd.DataFrame([article.__dict__ for article in self])