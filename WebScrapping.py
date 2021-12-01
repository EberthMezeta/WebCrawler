from bs4 import BeautifulSoup
import requests
import unidecode
import nltk
from nltk import  word_tokenize
from nltk.corpus import stopwords
import validators
import pysolr
import re

solr = pysolr.Solr('http://localhost:8983/solr/mycore/', always_commit=True)

    
def crawler(url):
    #Request HTML
    page = requests.get(url)
    #Get HTML content
    soup = BeautifulSoup(page.text, 'html.parser')
    #Get children links
    links = soup.find_all('a')
    childrenLinks = getLinks(links)
    #SaveDocument
    document = getDocument(soup,url)
    solr.add([document])
    
    
    for link in childrenLinks:
        page = requests.get(link)
        soup = BeautifulSoup(page.text, 'html.parser')
        linksLv1 = soup.find_all('a')
        
        childrenLinksLV1 = getLinks(linksLv1)
        document = getDocument(soup,link)
        solr.add([document])
        
        
        for sublink in childrenLinksLV1:
            page = requests.get(sublink)
            soup = BeautifulSoup(page.text, 'html.parser')
            document = getDocument(soup,sublink)
            solr.add([document])
         
def getTokenz(text):
    #Remove accents
    text = unidecode.unidecode(text)
    #text = text.translate(str.maketrans('','',string.punctuation))
    #To Lower Case
    text = text.lower()
    #Tokenizer
    tokens = word_tokenize(text)
    #Remove punctuations, other formalities of grammar
    tokens = [word for word in tokens if word.isalpha()]
    #Remove white spaces and StopWords
    tokens = [word for word in tokens if not word in stopwords.words("spanish")]
    
    return tokens

def getLinks(links = []):
    childrenLinks = []
    size = 0
    for link in links:
        path = link.get('href')
        if path is not None:
            if validators.url(path):
                 childrenLinks.append(path)
                 size = size + 1
        #Limit
        if size == 2:
            break;         
                
    print(childrenLinks)       
    return childrenLinks
 
def getDocument(soup,url):
    #Process text.
    #Remove tags, ccs,Javascript.
    text = soup.get_text()   
    #Get Tokens
    tokens = getTokenz(text)
    #Get text preprocess
    textUnWhiteSPace = " ".join(re.split(r"\s+", text))
    #Get size
    size = len(tokens)
    #Get Field Text
    textClean = " ".join(tokens)
    #Get URL
    link = url
    #Get Base_URL
    base_url = url.split('/')
    #Get Title
    soupTitle = soup.find('title')
    Snippet = textUnWhiteSPace[0:50]

    if soupTitle != None :
       title = soupTitle.text
    else:
        title = "Titulo no disponible"
                
    document = {
        "title": title,
        "_title_": title,
        "text": textClean,
        "_text_" : textClean,
        "_snippet_": Snippet,
        "size": size,
        "url" : link,
        "base_url":base_url[2]    
    }
    #summitInSolr(document)
    return document
    

crawler("https://www.it-swarm-es.com/es/python/como-obtener-sinonimos-de-nltk-wordnet-python/1041861904/")

