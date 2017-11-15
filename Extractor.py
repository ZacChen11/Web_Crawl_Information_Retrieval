'''
Created on Nov 14, 2017

@author: Zac
'''

import re
import os
import requests
from readability import Document


class Extractor():
    
    def __init__(self):
        self.link_container = {}
    

    def html_to_text(self, data): 
        
        # remove all the tags
        r = re.compile(r'<[^<]*?>')
        data = r.sub('', data)
        
        r = re.compile('<.+?>')
        data = r.sub('', data)
         
        # remove the newlines
        data = data.replace("\n", " ")
        data = data.replace("\r", " ")
        
        # remove the newlines
        data = data.replace("\\n", " ")
        data = data.replace("\\r", " ")
        data = data.replace("\\t", " ")
        
        r = re.compile('&#[\d]+;')
        data = r.sub('', data)

        # replace consecutive spaces into a single one
        data = " ".join(data.split()) 
        
        return data  
         
    
    def generate_doc(self, m_list):
        
        # create a text directory if one does not exist
        if not os.path.isdir('text'):
            os.makedirs('text')
        
        i = 0
        for link in m_list:
            i += 1
            self.link_container[i] = link
            r = requests.get(link)
            doc = Document(r.text)
            doc = doc.title()+doc.content()+doc.summary()
         
            doc = Extractor.html_to_text(self, doc)
        
            filename = "text\\%d.txt"%(i)   
            f = open(filename, 'w', errors = 'ignore')
            f.write(doc)



if __name__ == '__main__':
    
    m = ["https://csu.qc.ca/content/student-groups-associations", "https://www.concordia.ca/artsci/students/associations.html", "http://www.cupfa.org", "http://cufa.net"]
    a = Extractor()
    a.generate_doc(m)
    print(a.link_container)
