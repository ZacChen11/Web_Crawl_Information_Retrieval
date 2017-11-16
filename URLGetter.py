"""Web crawler to get URLs for a given depth"""
from bs4 import BeautifulSoup
import requests
from urlparse import urljoin, urlsplit, SplitResult
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
        self.urls_file = open('url_files', 'w')

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
            htmlpage = requests.get(url, timeout=10)
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
            print("Can't open the site: " + url)
            return

        # ensure that resource is indexable 
        content_type = htmlpage.headers['Content-Type'].split(';')[0]
        if content_type not in ['text/html', 'text/plain']:
            return

        # validate title
        soup = BeautifulSoup(htmlpage.content, 'lxml')
        if content_type is 'text/html':
        	if not validatetitle(soup.title):
        		return

        # write url to file
        self.urlset.add(url)
        url_files.write(url)
        url_files.write('\n')

        # send html content to be filtered then written to file
        # TODO

        # get new links from page
        if currentdepth != 0:
            print('processing:' + url)
            for link in soup.findAll('a'):
            	filteredlink = self.preprocesslink(url, link)
                if filteredlink not in self.urlset:
                    filteredlink = self.preprocesslink(url, link.get('href'))
                            self.geturls(filteredlink, currentdepth-1)


    def getlist(self):
        """Crawl website and return URL list"""
        self.geturls()
        return list(self.urlset)


if __name__ == '__main__':
    mygetter = URLGetter("https://csu.qc.ca/content/student-groups-associations", 2)
    # mygetter = BreadthFirstURLGetter("http://hivecafe.ca", 5)
    urls = mygetter.getlist()
    print(urls)
    print(len(urls))
