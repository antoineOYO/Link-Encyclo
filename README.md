# Linking the Encyclopédie

The documents are represented by instances of `Article` class, grouped in a `Book` instance.

A Wikidata ressource is represented by `WikidataObject` instances.

- `table2plainbook.ipynb` builds a `Book` instance and adds the Wikidata QIDs from P. Nugues annotation campaign
- `plainbook2geobook.ipynb` trims the raw articles down to triples (headĥrase, Proper Noun 1, Proper Noun 2)

 
**TODO**

- [X] add a description string to a book, append it to _repr__
- [ ] revoir la fonction is_saint : on ne veut remplacer que les abbréviations
- [X] réordonner np1 et np2


# Sources
- gold QIDs from [Linking Named Entities in Diderot’s Encyclopédie to Wikidata](https://aclanthology.org/2024.lrec-main.928) (Nugues, LREC-COLING 2024)
- stop-words and contractions (compiled into solr_stopwords.txt) : from [http://snowball.tartarus.org/algorithms/french/stop.txt](http://snowball.tartarus.org/algorithms/french/stop.txt), distributed under the BSD License.