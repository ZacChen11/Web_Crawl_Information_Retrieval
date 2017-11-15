"""Web crawler to get URLs for a given depth"""
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin, urlsplit, SplitResult
import re


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
           If depth is 0, set it as initial depth
        """
        if url is None:
            url = self.starturl
        if currentdepth == 0:
            currentdepth = self.depth

        try:
            htmlpage = requests.get(url, timeout=10)
        except (requests.exceptions.ReadTimeout, ConnectionError, requests.exceptions.ConnectionError):
            print("Can't open the site: " + url)
            return

        soup = BeautifulSoup(htmlpage.content, 'lxml')
        self.urlset.add(url)
        print('processing:' + url)
        for link in soup.findAll('a'):
            filteredlink = self.preprocesslink(url, link.get('href'))
            if filteredlink and validatetitle(soup.title):
                if currentdepth > 1:
                    self.geturls(filteredlink, currentdepth-1)
                elif currentdepth == 1:
                    self.urlset.add(filteredlink)

    def getlist(self):
        """Crawl website and return URL list"""
        self.geturls()
        return list(self.urlset)


if __name__ == '__main__':
    mygetter = URLGetter("https://csu.qc.ca/content/student-groups-associations", 4)
    # mygetter = BreadthFirstURLGetter("http://hivecafe.ca", 5)
    urls = mygetter.getlist()
    print(urls)
    print(len(urls))
