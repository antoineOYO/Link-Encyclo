# Link Encyclo

Tools to link documents to Wikidata ressources.

The documents are represented by instances of `Article` class, grouped in a `Book` instance.

A Wikidata ressource is represented by `WikidataObject` instances.

 
**TODO**

- [X] add a description string to a book, append it to _repr__
- [ ] revoir la fonction is_saint : on ne veut remplacer que les abbréviations
- [ ] réordonner np1 et np2


# Sources

- stop-words and contractions (compiled into solr_stopwords.txt) : from svn.tartarus.org/snowball/trunk/website/algorithms/french/stop.txt, distributed under the BSD License.