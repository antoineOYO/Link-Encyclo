from unidecode import unidecode
from stanza.models.common.doc import Span, Token
import random
import pandas as pd
import re

from utils import *


class Article:
    def __init__(self,
                 volume = None,
                 numero = None,
                 headphrase = None,
                 authors = None,
                 text = None, # concatenated text of the paragraphs
                 ):
        """
        :param volume: volume number
        :param numero: article number
        :param headphrase: headphrase of the article
        :param authors: list of authors
        :param text: concatenated text of the paragraphs

        :param hash: VOLUME/NUMERO/HEADPHRASE
        :param artfl: ARTFL id
        :param enccre: ENCCRE id
        """
        self.volume = volume
        self.numero = numero
        self.headphrase = headphrase
        self.authors = authors
        self.text = text

        self.hash = str(self.volume) + '/' + str(self.numero) + '/' + self.headphrase
        self.artfl  = 'https://artflsrv04.uchicago.edu/philologic4.7/encyclopedie0922/navigate/' + str(self.volume) + '/' + str(self.numero)
        self.enccre = None

        # the parsing should be done with stanza
        # https://stanfordnlp.github.io/stanza/data_objects.html#parsetree
        # self.parsed should be the output of this parser
        self.parsed = None

        # the NER should be done with custom NER method
        # https://huggingface.co/GEODE/bert-base-french-cased-edda-ner 
        # self.ner is the output of the model
        self.ner = None

        # refer to the method _enrich_stanzadoc
        self.nc1 = None
        self.nc1_ = None
        self.np1 = None
        self.np1_ = None
        self.np2 = None
        self.np2_ = None
        self.ncs = None
        self.nps = None

        # if any
        self.gold_qid = None
        self.gold_coords = None

        # annotations can be the outputs of your Entity Linking experiences
        self.annotations = None

    def __repr__(self):
        return self.hash
        # return f"Volume {self.volume} - Numero {self.numero} - Authors : {self.authors}\n{self.text}"
    
    def _apply_pipeline(self, pipeline, skip_headphrase=False):
        """
        Apply the provided pipeline to the Article.text
        Returns an instance of the pipeline's output
        """
        start_index = 0
        if skip_headphrase:
            start_index = len(self.headphrase)
        doc = pipeline(self.text[start_index:])
        return doc
    
    
    def _enrich_stanzadoc(self):
        """
        We add NER tags to a Stanza doc :
        - native `Token` instances of the Stanza doc receive the NER tags
        - native `Span` instances of the Stanza doc receive the contiguous merged NER tags

        Returns the tuple (ncs, nps): 
        - ncs, list[Span] --> list of all NC Geographic Entities
        - nps, list[Span] --> list of all NP Geographic Entities
        """
        if not self.parsed:
            print("parse the article first")
        if not self.ner:
            print("apply the NER pipeline first")

        # 1st. we add the related NER tag to each stanza.Token
        for token in self.ner:
            related_tokenpieces = [tp for tp in self.parsed.iter_tokens() \
                                if tp.start_char >= token['start'] \
                                    and tp.end_char <= token['end']]
            if related_tokenpieces:
                for tp in related_tokenpieces:
                    tp.ner = token['entity_group']
        #fulfil the gaps with 'O'
        for token in self.parsed.iter_tokens():
            if not token.ner: #i.e. token.ner == None
                token.ner = 'O'
        
        # 2nd. we merge the contiguous tokens with the same NER into spans

        stanza_spans = []
        list_tokens = [token for token in self.parsed.iter_tokens()]
        current_span = []
        for token in list_tokens:
            # either we extend current_span
            if not current_span or token.ner == current_span[-1].ner:
                current_span.append(token)
            # or we close it and start a new one
            else:
                whole_span = Span(
                    tokens = current_span,
                    type = current_span[-1].ner,
                    doc=self.parsed
                    )
                stanza_spans.append(whole_span)
                #print('span completed : ', whole_span.text, whole_span.type)    
                current_span = [token]

        # we finally add the spans to the Stanza doc
        self.parsed.entities = stanza_spans

    def _search_spatial_pattern(self, stopwords):
        """
        Extracts the spatial pattern (if any) from the article-body.
        by normalizing the Geographic Stanza Span 
        Currently, the following pattern in searched :
        ... NC_Spatial ... NP_Spatial ... NP_Spatial ...
        Strings are stored in the corresponding attributes : nc1, np1, np2

        Returns the tuple (ncs, nps):
        - ncs, list[Span] --> list of all Common Nouns Geographic Entities
        - nps, list[Span] --> list of all proper Nouns Geographic Entities
        """

        # we normalize the NP and NC entities using normalzing functions from utils.py
        nps = [entity_span for entity_span in self.parsed.entities if entity_span.type == 'NP_Spatial']
        nps = [normalize_span(span, pos=['NOUN', 'PROPN', 'ADJ'], stop_words=stopwords) for span in nps]
        nps = [np for np in nps if np] # removing the None values

        ncs = [entity_span for entity_span in self.parsed.entities if entity_span.type == 'NC_Spatial']
        ncs = [normalize_span(span, pos=['NOUN', 'PROPN'], stop_words=stopwords) for span in ncs]
        ncs = [nc for nc in ncs if nc] # removing the None values

        # PATTERN SEARCH
        nc1 = ncs[0] if ncs else None
        nc1_ = nc1.norm_text if nc1 else None
        
        consecutive_nps = [np for np in nps if (nc1 and np) and np.start_char > nc1.end_char] #if (nc1 and nps) else None# NP after the 1st NC
        
        np1 = consecutive_nps[0] if  len(consecutive_nps) > 0 else None
        np1_ = np1.norm_text if np1 else None
        np2 = consecutive_nps[1] if  len(consecutive_nps) > 1 else None
        np2_ = np2.norm_text if np2 else None

        # storing into the attributes
        self.nc1 = nc1
        self.nc1_ = nc1_
        self.np1 = np1
        self.np1_ = np1_
        self.np2 = np2
        self.np2_ = np2_
        self.ncs = ncs
        self.nps = nps

        return ncs, nps
    
from collections import Counter
class Book:
    def __init__(self, list_of_articles=None):
        self.articles = list_of_articles if list_of_articles is not None else []
        #self.description = None

    def __repr__(self):
        output = f"Book with {len(self.articles)} articles\n"
        if hasattr(self, 'description'):
            output += self.description
        output += f"\nAttributes :\n{self[0].__dict__.keys()}"
        return output
    
    def __iter__(self):
        return iter(self.articles)

    def __getitem__(self, index):
        return self.articles[index]
    
    
    def _sample(self, n):
        return random.sample(self.articles, n)

    
    def _reach_article(self, volume = None, numero  = None, headphrase=None):
        for art in self.articles:
            if headphrase:
                if art.headphrase.lower() == headphrase.lower():
                    return art
            elif art.volume == volume and art.numero == numero:
                return art
        return None
    
    def _make_counts(self):
        all_nps = [np.norm_text for article in self for np in article.nps]
        self.nps_counter = Counter(all_nps)
        all_ncs = [nc.norm_text for article in self for nc in article.ncs]
        self.ncs_counter = Counter(all_ncs)
    
    def _to_dataframe(self):
        return pd.DataFrame([article.__dict__ for article in self])