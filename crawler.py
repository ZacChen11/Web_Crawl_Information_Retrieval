from bs4 import BeautifulSoup

# from urllib.error import HTTPError, URLError                 # python3
# from urllib.parse import urljoin, urlsplit, SplitResult      # python3
# from urllib.request import urlopen                           # python3
# from http.client import RemoteDisconnected                   # python3

from urllib2 import HTTPError, URLError                        # python2
from urlparse import urljoin, urlsplit, SplitResult            # python2
from urllib2 import urlopen                                    # python2

import Queue
from threading import Lock, Thread

import re
from boilerpipe.extract import Extractor


def validate_title(title):
    # Validate the title, remove those with title 'Page Not Found'

    if title and title.string:  # make sure title object and title.string obj are not None
        keywords = ['page', 'not', 'found']
        title_list = [keyword.lower() for keyword in title.string.split(' ')]
        if all(word in title_list for word in keywords):
            return False

    return True


class Crawler:
    # Web crawler to get URLs for a given depth

    facebook_url_re = re.compile('://\w*\.?facebook.com')

    def __init__(self, start_urls, max_links):
        self.url_queue = Queue.Queue()
        self.url_set = set()
        for url in start_urls:
            self.url_queue.put(url)
            self.url_set.add(url)

        self.max_links = max_links

        self.urls_file = open('webcrawl_docs/url_files.txt', 'w')
        self.i = -1

        self.lock = Lock()

    def preprocess_link(self, referrer, url):
        # Modify and filter URLs before crawling
        if not url:
            return None

        fields = urlsplit(urljoin(referrer, url))._asdict()  # convert to absolute URLs and split
        fields['path'] = re.sub(r'/$', '', fields['path'])  # remove trailing "/"
        fields['fragment'] = ''  # remove targets within a page
        fields = SplitResult(**fields)

        if fields.scheme == 'http':
            httpurl = newurl = fields.geturl()
            httpsurl = httpurl.replace('http:', 'https:', 1)
        elif fields.scheme == 'https':
            httpsurl = newurl = fields.geturl()
            httpurl = httpsurl.replace('https:', 'http:', 1)
        else:
            # Filter the URL without 'http' or 'https'
            return None

        if httpurl not in self.url_set and httpsurl not in self.url_set:
            # Filter URL that already exists in set
            return newurl
        else:
            return None

    def crawl(self):
        while self.url_queue.not_empty:
            if self.i >= self.max_links:
                return

            url = self.url_queue.get()

            if url is None:
                continue

            # skip facebook links
            if self.facebook_url_re.search(url) is not None:
                continue

            self.lock.acquire()
            print('processing:' + url)
            self.lock.release()

            # download resource
            try:
                html_page = urlopen(url)
            except HTTPError:
                continue
            except URLError:
                continue
            except: # I removed the specific exception detected here because I couldn't find a python2 import for it
                continue

            # ensure that resource is indexable
            try:
                content_type = html_page.headers['Content-Type'].split(';')[0]
            except:
                return
            if content_type not in ['text/html', 'text/plain']:
                continue

            # validate title
            soup = BeautifulSoup(html_page.read(), 'lxml')
            if content_type is 'text/html':
                if not validate_title(soup.title):
                    continue

            # extract text
            try:
                extractor = Extractor(extractor='KeepEverythingExtractor', url=url)
            except HTTPError:
                continue
            except URLError:
                continue
            except: # I removed the specific exception detected here because I couldn't find a python2 import for it
                continue

            # write text to file
            doc = extractor.getText()

            self.lock.acquire()

            self.i += 1
            filename = "webcrawl_docs/%d.txt" % self.i

            print 'writing doc %d' % self.i

            f = open(filename, 'w')
            f.write(doc.encode('utf-8'))
            f.close()

            # write url to file
            self.urls_file.write(url)
            self.urls_file.write('\n')

            self.lock.release()

            for link in soup.findAll('a'):
                filtered_link = self.preprocess_link(url, link.get('href'))
                self.lock.acquire()
                if filtered_link and filtered_link not in self.url_set:
                    self.url_set.add(filtered_link)
                    self.url_queue.put(filtered_link)
                self.lock.release()

    def multi_crawl(self, thread_count):
        threads = []
        for i in range(thread_count):
            t = Thread(target=self.crawl)
            t.start()
            threads.append(t)

        # for thread in threads:
        #     thread.join()

    def html_to_text(self, data):

        # define regexes
        head_remover = re.compile('<head>.*?</head>')
        comment_remover = re.compile('<!--.*?-->')
        script_remover = re.compile('<script.*?>.*?</script>')
        tag_remover = re.compile('</?.*?>')
        special_char_remover = re.compile('&#\d+;')

        # remove line breaks
        data = data.replace('\n', ' ')
        data = data.replace('\r', ' ')
        data = data.replace('\t', ' ')

        # remove tags for head, comments, and scripts also deleting all contents
        data = head_remover.sub(' ', data)
        data = comment_remover.sub(' ', data)
        data = script_remover.sub(' ', data)

        # remove arbitrary tags
        data = tag_remover.sub(' ', data)

        # remove tokens of the form &#ddd;
        data = special_char_remover.sub(' ', data)

        # delete extra whitespace
        data = ' '.join(data.split())

        return data


if __name__ == '__main__':
    import os, sys

    if not os.path.exists('webcrawl_docs'):
        os.makedirs('webcrawl_docs')

    urls = ["https://csu.qc.ca/content/student-groups-associations", "https://www.concordia.ca/artsci/students/associations.html", "http://www.cupfa.org", "http://cufa.net"]
    crawler = Crawler(urls, int(sys.argv[1]))
    crawler.multi_crawl(5)

