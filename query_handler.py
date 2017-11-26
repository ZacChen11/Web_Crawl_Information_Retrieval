import re
from nltk import stem
from nltk.tokenize import WordPunctTokenizer
import math
import json


class QueryHandler:

    alpha_numeric_re = re.compile('[a-zA-Z0-9]')

    def __init__(self):
        # read dictionary file into memory
        f = open('webcrawl.dict', 'r')
        d = f.readlines()
        f.close()
        splitter = re.compile('(.*),(\d+),(-?\d+)$')
        self.dictionary = dict((s[0][0], [int(s[0][1]), int(s[0][2])]) for s in [splitter.findall(line) for line in d])

        # open postings file for searching
        self.postings_file = open('webcrawl.postings', 'r')

        # open doc sizes file
        self.doc_sizes = open('webcrawl.doclengths', 'r')

        # get urls list
        urls_file = open('webcrawl.urls', 'r')
        self.urls = map(lambda x: x[:-1], urls_file.readlines())



        # read in metadata
        f = open('webcrawl.meta', 'r')
        meta = json.loads(f.read())
        f.close()

        self.number_docs = int(meta['number_docs'])
        self.number_tokens = int(meta['number_tokens'])

        # initialize stemmer
        self.stemmer = stem.PorterStemmer()
        self.tokenizer = WordPunctTokenizer()

    def get_postings(self, terms):
        # if given an empty set of terms
        if not terms:
            return [[]], [[]]

        postings = []
        for term in terms:
            if term in self.dictionary:
                # get postings list
                postings_location = self.dictionary[term][0]
                self.postings_file.seek(postings_location)
                postings_list = self.postings_file.readline()[:-1].split(';')

                # decompress postings list
                postings_list = self.decompress_postings_list(postings_list)

                postings.append(postings_list)
            else:
                # empty list has meaning for intersection algorithm and helps calculate term frequencies for ranking
                postings.append([])

        # sort postings list ascending by length
        postings.sort(key=lambda x: len(x))

        return postings, sorted(map(len, postings))

    @staticmethod
    def decompress_postings_list(postings_list):
        # convert from string to tuple of int and list of single int
        postings_list = map(lambda x: map(int, x), map(lambda y: y.split(','), postings_list))

        # re-add term frequencies of 1 and convert to int
        for i, posting in enumerate(postings_list):
            if len(posting) == 1:
                postings_list[i] = [posting[0], 1]

        # restore to full doc_id
        last_amount = 0
        for posting in postings_list:
            last_amount = posting[0] + last_amount
            posting[0] = last_amount

        # convert from string to tuple of int and list of single int
        postings_list = map(lambda x: [x[0], [x[1]]], postings_list)

        return postings_list

    # !Important!: this function is NOT pure. It will alter the postings lists
    @staticmethod
    def intersect_postings(postings):
        postings.sort(key=len)

        intersected_postings = postings.pop(0)

        while len(postings) > 0:
            intersected_postings = QueryHandler.intersect_pair_postings(intersected_postings, postings.pop(0))

        return intersected_postings

    # !Important!: this function is NOT pure. It will alter the postings lists
    @staticmethod
    def intersect_pair_postings(list1, list2):
        # end early if possible
        if not list1 or not list2:
            return []

        p1 = list1.pop(0)
        p2 = list2.pop(0)

        # basic intersection algorithm + term frequency padding
        new_list = []
        while p1 and p2:
            if p1[0] == p2[0]:
                new_list.append([p1[0], p1[1] + (p2[1])])
                if not list1 or not list2:
                    break
                p1 = list1.pop(0)
                p2 = list2.pop(0)
            elif p1[0] < p2[0]:
                if not list1 or not list2:
                    break
                p1 = list1.pop(0)
            else:
                if not list1 or not list2:
                    break
                p2 = list2.pop(0)

        return new_list

    # !Important!: this function is NOT pure. It will alter the postings lists
    @staticmethod
    def union_postings(postings):
        postings = list(postings)
        postings.sort(key=len)

        unioned_postings = postings.pop(0)

        i = 1
        while len(postings) > 0:
            unioned_postings = QueryHandler.union_pair_postings(unioned_postings, postings.pop(0), i)
            i += 1

        return unioned_postings

    # !Important!: this function is NOT pure. It will alter the postings lists
    @staticmethod
    def union_pair_postings(list1, list2, i):
        # end early if possible
        if not list1 and not list2:
            return []

        # prevent popping empty list
        if not list1:
            p1 = [float('inf')]
        else:
            p1 = list1.pop(0)
        if not list2:
            p2 = [float('inf')]
        else:
            p2 = list2.pop(0)

        # the amount of 0s to add for empty terms depends on number of empty terms
        blanks = [0 for x in range(i)]

        # basic union algorithm + terms frequency concatenation
        new_list = []
        while True:
            if p1[0] == p2[0]:
                new_list.append([p1[0], p1[1] + p2[1]])
                if not list1 or not list2:
                    break
                p1 = list1.pop(0)
                p2 = list2.pop(0)
            elif p1[0] < p2[0]:
                new_list.append([p1[0], p1[1] + [0]])
                if not list1:
                    break
                p1 = list1.pop(0)
            else:
                new_list.append([p2[0], blanks + p2[1]])
                if not list2:
                    break
                p2 = list2.pop(0)

        # once first list has been exhausted, add remaining postings in other list to results
        # make sure to pad term frequencies with 0s first
        if not list1:
            new_list.extend(map(lambda x: [x[0], blanks + x[1]], list2))
        if not list2:
            new_list.extend(map(lambda x: [x[0], x[1] + [0]], list1))

        return new_list

    def parse_query(self, input):
        # tokenize
        tokens = self.tokenizer.tokenize(input)

        # stem
        terms = [self.stemmer.stem(term) for term in tokens]

        # reduce to lower case
        terms = map(lambda x: x.lower(), terms)

        # filters tokens with no numbers or letters
        terms = [term for term in terms if self.alpha_numeric_re.search(term) is not None]

        return terms

    def bm25_scorer(self, postings, term_freqs, b, k1):
        for doc in postings:
            # get document length
            self.doc_sizes.seek(doc[0] * 5)
            doc_length = self.doc_sizes.read(5)
            doc_length = int(doc_length)

            # calculate score with bm25 from 11.32
            score = 0
            for i, tf in enumerate(term_freqs):
                # idf padded to prevent division by 0
                idf = math.log(float(self.number_docs) / float(tf + 0.1))
                numerator = doc[1][i] * (k1 + 1)
                denominator = k1 * ((1-b) + b * (doc_length / (self.number_tokens/float(self.number_docs)))) + doc[1][i]
                score += idf * numerator / denominator
            doc[1] = score
        return postings

    def get_terms_sentiment(self, terms):
        total = 0
        for term in terms:
            if term in self.dictionary:
                total += self.dictionary[term][1]

        return total

    def sentiment_scorer(self, scored_postings, query_sentiment):

        query_is_negative = query_sentiment < 0

        for doc in scored_postings:
            # get doc sentiment
            doc_sentiment = self.compute_document_sentiment(doc[0])

            # get document length
            self.doc_sizes.seek(doc[0] * 5)
            doc_length = self.doc_sizes.read(5)
            doc_length = int(doc_length)

            scale_amount = math.e ** (abs(doc_sentiment / float(doc_length)))

            document_is_negative = doc_sentiment < 0

            if (query_is_negative and document_is_negative) or (not query_is_negative and not document_is_negative):
                doc[1] *= scale_amount

        return scored_postings

    def compute_document_sentiment(self, doc_id):
        doc_file = open('processed_docs/%d' % doc_id,'r')

        doc_terms = doc_file.readlines()
        doc_terms = map(lambda x: x[:-1].split(), doc_terms)
        doc_terms = {term[0]:int(term[1]) for term in doc_terms}

        doc_term_sentiments = []

        for term in doc_terms:
            if term in self.dictionary:
                doc_term_sentiments.append(self.dictionary[term][1])
            else:
                doc_term_sentiments.append(0)

        return sum(doc_term_sentiments)


if __name__ == '__main__':
    q = QueryHandler()

    print("----Concordia Web Crawl Index----")
    while True:
        raw_query = raw_input('\n\nEnter your query: ')
        print '\n'

        query = q.parse_query(raw_query)
        posts, term_freqs = q.get_postings(query)

        query_sentiment = q.get_terms_sentiment(query)

        # intersection results no longer given because ranking is more important
        results = q.union_postings(posts)

        # score results
        results = q.bm25_scorer(results, term_freqs, 0.75, 1.6)

        # modify score with sentiment score
        results = q.sentiment_scorer(results, query_sentiment)

        # sort results
        results = sorted(results, key=lambda x: x[1], reverse=True)

        # keep only the doc_id
        results = map(lambda x : x[0], results)

        # map doc_id to url
        results = map(lambda doc_id: q.urls[doc_id], results)

        print 'Results: '
        for url in results:
            print url
