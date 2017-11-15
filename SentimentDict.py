'''
Created on Nov 11, 2017

@author: Zac
'''

class SentimentDict():

    def __init__(self):
        self.dict = {}
    
    def generate_dict(self):
      
#         i = 0
#         j = 0
#         k = 0  
        'read AFINN-111.txt file line by line'
        for a in open('AFINN\\AFINN-111.txt'):
#             i = i + 1
            a = a.split()
            
            'check if the key is more than one word'
            if len(a)>= 3:
                
                'when the key is more than two words'
                if a[2].isalpha():
#                     k += 1
                    e = a[0]+' '+a[1]+' '+a[2]
                    self.dict[e] = a[3]
#                     j += 1
                    
                    'when the key is two words'
                elif a[1].isalpha():
                    e = a[0]+' '+a[1]
#                     j+=1
                    self.dict[e] = a[2]
                    
                'when the key is one word'
            else:
                self.dict[a[0]]= a[1]
                
        print(self.dict)
    
    
#         'check if all the key-value pairs are properly stored in the dictionary'
#         i = 0
#         for items in self.dict:
#             if self.dict[items].isdigit():
#                 pass
#             elif self.dict[items].lstrip("-").isdigit():
#                 pass
#             else:
#                 i = i + 1
#                 print("%s : %s"%(items,self.dict[items]))
#         print('i is %s'%i)
#         print('k is %s'%k)

if __name__ == '__main__':
    a = SentimentDict()
    a.generate_dict()
    print(a.dict)
    print(a.dict['son-of-a-bitch'])
        