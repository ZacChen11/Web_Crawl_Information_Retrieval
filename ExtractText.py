'''
Created on Nov 15, 2017

@author: Zac
'''

import os
from boilerpipe.extract import Extractor


class Extract_Text():
    
    def __init__(self):
        self.link_container = {}
    
    def generate_doc(self, m_list):
        
        if not os.path.isdir('text'):
            os.makedirs('text')
        
        i = 0
        for link in m_list:
            i += 1
            self.link_container[i] = link
            #DefaultExtractor ArticleExtractor ArticleSentencesExtractor KeepEverythingExtractor LargestContentExtractor
            extractor = Extractor(extractor='ArticleExtractor', url=link)
            doc = extractor.getText()
            print(doc.encode())
            filename = "text\\%d.txt"%(i)   
            f = open(filename, 'w', errors = 'ignore')
            f.write(doc)




if __name__ == '__main__':
    
    m = ["https://csu.qc.ca/content/student-groups-associations", "https://www.concordia.ca/artsci/students/associations.html", "http://www.cupfa.org", "http://cufa.net"]
    a = Extract_Text()
    a.generate_doc(m)
    print (a.link_container)