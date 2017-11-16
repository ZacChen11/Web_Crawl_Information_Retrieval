import re
from nltk.tokenize import WordPunctTokenizer
from nltk.stem import PorterStemmer
import json
from sentiment_dictionary import SentimentDictionary
from math import log


class TokenStreamer:
    # regular expression patterns for pre-processing
    doc_start_re = re.compile('<REUTERS .*>')
    new_id_re = re.compile('NEWID="(\d+)"')
    xml_markup_re = re.compile('<.+?>')
    unknown_tag_start_re = re.compile('<UNKNOWN>')
    unknown_tag_end_re = re.compile('.*</UNKNOWN>$')
    empty_line_re = re.compile('^\s*$')
    special_characters_re = re.compile('&#[\d]+;')
    alpha_numeric_re = re.compile('[a-zA-Z0-9]')

    number_files = 22

    def __init__(self):
        # file information
        self.current_file_id = 0
        self.current_file = self.open_sgm()

        # stats
        self.current_doc_id = -1

        # working data
        self.tokens = []
        self.next_line_in_file = ''

        # utilities
        self.tokenizer = WordPunctTokenizer()
        self.stemmer = PorterStemmer()

    def get_token_counter(self):
        return self.token_counter

    def get_current_doc_id(self):
        return self.current_doc_id

    def open_sgm(self):
        return open('reuters21578/reut2-0'+format(self.current_file_id, '02d')+'.sgm', 'r')

    def next_line(self):
        # small hack to enable has_next() method in python
        if self.next_line_in_file != '':
            next_line = self.next_line_in_file
            self.next_line_in_file = ''
        else:
            next_line = self.current_file.readline()

        # check for end of file
        if next_line == '':
            self.current_file_id += 1
            if self.current_file_id < TokenStreamer.number_files:
                self.current_file = self.open_sgm()
                next_line = self.current_file.readline()

        # return line
        return next_line

    def has_next(self):
        if self.next_line_in_file == '':
            self.next_line_in_file = self.current_file.readline()

        return self.next_line_in_file != '' or self.tokens != []

    def next_preprocessed_line(self):
        in_unknown_tag = False
        while True:
            line = self.next_line()

            if line == '':
                return line

            # removes all contents between <UNKNOWN></UNKNOWN> tags between articles
            if in_unknown_tag:
                if TokenStreamer.unknown_tag_end_re.match(line):
                    in_unknown_tag = False
                continue
            if TokenStreamer.unknown_tag_start_re.match(line):
                in_unknown_tag = True
                continue

            # detects start of new document
            if TokenStreamer.doc_start_re.match(line):
                self.current_doc_id = int(TokenStreamer.new_id_re.findall(line)[0])
                continue

            # removes all xml tags from line
            line = re.sub(TokenStreamer.xml_markup_re, ' ', line)

            # removes all characters of the from &#ddd;
            line = re.sub(TokenStreamer.special_characters_re, ' ', line)

            # removes blank lines
            if TokenStreamer.empty_line_re.match(line):
                continue

            # remove lines that are exclusively punctuation
            if TokenStreamer.alpha_numeric_re.search(line) is None:
                continue

            # if line makes it this far then it's done pre processing
            return line

    def next(self):
        if not self.tokens: # if tokens list is empty
            next_line = self.next_preprocessed_line()

            # next_line == '' iff the end of last document has been reached
            if next_line == '':
                return []

            # fixes a specific bug where the non utf-8 character 0xFC in 'reut2-017.sgm' caused porter stemmer to crash
            next_line = next_line.decode('utf-8', 'ignore').encode("utf-8")

            # tokenize, and stem
            self.tokens = [self.stemmer.stem(word) for word in self.tokenizer.tokenize(next_line)]

            if not self.tokens: # if removing punctuation emptied the list then get next line
                    return self.next()

        # final token filtration
        if self.should_be_filtered(self.tokens[0]):
            self.tokens.pop(0)
            return self.next()

        # return tuple of final fully processed token and associated doc_id
        return self.tokens.pop(0), self.current_doc_id

    def should_be_filtered(self, token):
        # filters tokens with no numbers or letters
        if self.alpha_numeric_re.search(token) is None:
            return True
        return False


class CorpusStatsStreamer:
    def __init__(self, s):
        self.attached_stream = s

        self.doc_lengths_file = open('reuters.doclengths', 'w')

        self.current_doc_id = -1
        self.current_doc_length = 0
        self.token_counter = 0

    def write_doc_length_to_file(self):
        self.doc_lengths_file.seek((self.current_doc_id - 1) * 5)
        self.doc_lengths_file.write(format(self.current_doc_length, '05d'))
        self.current_doc_length = 0

    def has_next(self):
        return self.attached_stream.has_next()

    def next(self):
        next_token = self.attached_stream.next()

        # if nothing is then write final data and end early
        if not next_token:
            self.write_doc_length_to_file()
            self.write_meta_data()

            return next_token

        if next_token[1] != self.current_doc_id:
            if self.current_doc_id != -1:
                self.write_doc_length_to_file()

            self.current_doc_id = next_token[1]

        self.token_counter += 1
        self.current_doc_length += 1

        return next_token

    def write_meta_data(self):
        meta = {'number_docs': self.current_doc_id, 'number_tokens': self.token_counter}
        with open('reuters.meta', 'w') as f:
            f.write(json.dumps(meta, indent=4, separators=(',', ': ')))
            f.close()


class DocumentSentimentStreamer:
    integer_padding = 5

    def __init__(self, s):
        self.attached_stream = s
        self.sd = SentimentDictionary()

        self.doc_sentiments_file = open('reuters.sentiments', 'w')

        self.current_doc_id = -1
        self.current_doc_sentiment = 0

        self.max_sentiment = 0

    def write_doc_sentiment_to_file(self):
        self.doc_sentiments_file.seek((self.current_doc_id - 1) * DocumentSentimentStreamer.integer_padding)
        self.doc_sentiments_file.write(
            format(self.current_doc_sentiment, '0'+str(DocumentSentimentStreamer.integer_padding)+'d')
        )

    def has_next(self):
        return self.attached_stream.has_next()

    def next(self):
        next_token = self.attached_stream.next()

        # if nothing is then write final data and end early
        if not next_token:
            self.write_doc_sentiment_to_file()

            if log(self.max_sentiment, 10) > self.integer_padding - 1:
                print 'Sentiment integer padding not high enough'

            return next_token

        if next_token[1] != self.current_doc_id:
            if self.current_doc_id != -1:
                self.write_doc_sentiment_to_file()

                if self.current_doc_sentiment > self.max_sentiment:
                    self.max_sentiment = self.current_doc_sentiment
                self.current_doc_sentiment = 0

            self.current_doc_id = next_token[1]

        if next_token[0] in SentimentDictionary.dictionary:
            self.current_doc_sentiment += SentimentDictionary.dictionary[next_token[0]]

        return next_token
