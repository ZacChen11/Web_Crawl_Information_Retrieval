from nltk.stem import PorterStemmer


class SentimentDictionary:
    # it's like the lazy version of a singleton
    __instance = None

    #
    dictionary = None

    def __init__(self):
        if SentimentDictionary.__instance is None:
            SentimentDictionary.dictionary = self.load_sentiment_dictionary()

    @staticmethod
    def load_sentiment_dictionary():
        stemmer = PorterStemmer()
        f = open('sentiment_dictionary.txt', 'r')
        lines = f.readlines()
        f.close()

        pairs = map(lambda x: x.split('\t'), lines)
        pairs = map(lambda x: [stemmer.stem(x[0].decode('utf-8')), int(x[1].replace('\n', ''))], pairs)
        d = {pair[0]: pair[1] for pair in pairs}

        return d
