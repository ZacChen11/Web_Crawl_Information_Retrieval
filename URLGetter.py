"""Web crawler to get URLs for a given depth"""
from bs4 import BeautifulSoup
<<<<<<< HEAD
import requests
from urllib.parse import urljoin, urlsplit, SplitResult
=======
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit, SplitResult
from urllib.request import urlopen
>>>>>>> b9cf413f4154ecd776fb1d66623661218be20b15
import re
from boilerpipe.extract import Extractor
import os


def validatetitle(title):
    """Validate the title, remove those with title 'Page Not Found'"""

    if title and title.string:  # make sure title object and title.string obj are not None
        keywords = ['page', 'not', 'found']
        titlelist = [keyword.lower() for keyword in title.string.split(' ')]
        if all(word in titlelist for word in keywords):
            return False

    return True


class URLGetter:
    """Web crawler to get URLs for a given depth"""

    def __init__(self, starturl, depth):
        """Initialize the start URL and crawling depth"""
        self.starturl = starturl
        self.depth = depth
        self.urlset = set()
        self.urls_file = open('url_files', 'w')
        self.i = 0
        self.link_container = {}
        self.count = 0


    def preprocesslink(self, referrer, url):
        """ Modify and filter URLs before crawling"""
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

        if httpurl not in self.urlset and httpsurl not in self.urlset:
            # Filter URL that already exists in set
            return newurl
        else:
            return None

    def geturls(self, url=None, currentdepth=0):
        """Get URLs from a given link and depth. Default page is start page.
        """
        if url is None:
            url = self.starturl

        # download resource
        try:
            htmlpage = urlopen(url)
            # print(htmlpage.read())
        except (HTTPError, URLError):
            print("Can't open the site: " + url)
            return

        # ensure that resource is indexable
        content_type = htmlpage.headers['Content-Type'].split(';')[0]
        if content_type not in ['text/html', 'text/plain']:
            return

        # validate title
        soup = BeautifulSoup(htmlpage.read(), 'lxml')
        if content_type is 'text/html':
            if not validatetitle(soup.title):
                return

        # write url to file
        self.urlset.add(url)
        self.urls_file.write(url)
        self.urls_file.write('\n')
        
        #extract content from the link and write into file
        extractor = Extractor(extractor='KeepEverythingExtractor', url = url)
            
        doc = extractor.getText()
        self.i += 1
        self.link_container[self.i] = url
        print("id: %d  %s"%(self.i,url))
        filename = "text\\%d.txt"%(self.i)   
        f = open(filename, 'w', errors = 'ignore')
        f.write(doc)
        
        if currentdepth != 0:
            print('processing:' + url)
            for link in soup.findAll('a'):
                filteredlink = self.preprocesslink(url, link.get('href'))
                if filteredlink and filteredlink not in self.urlset:
                    self.geturls(filteredlink, currentdepth-1)


    def getlist(self):
        """Crawl website and return URL list"""
        self.geturls(self.starturl, self.depth)
        return list(self.urlset)


if __name__ == '__main__':

    if not os.path.isdir('text'):
        os.makedirs('text')
        
    mygetter = URLGetter("https://csu.qc.ca/content/student-groups-associations", 2)

    urls = mygetter.getlist()
    print(urls)
    print(len(urls))
