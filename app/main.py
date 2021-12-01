import re
import queue
from threading import Thread
import time
import traceback
from datetime import datetime
import os
import json

import nltk
import pysolr
import requests
import unidecode
import validators
from bs4 import BeautifulSoup
from nltk import word_tokenize
from nltk.corpus import stopwords
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.openapi.models import Response

class URL(BaseModel):
    url:str

run_interval = .5 #seconds
solr_host = os.getenv("SOLR_HOST", "host.docker.internal")
synonym_api = os.getenv("SOLR_HOST", "host.docker.internal")
synonym_updater = os.getenv("SOLR_HOST", "host.docker.internal")

solr = pysolr.Solr(f'http://{solr_host}:8983/solr/mycore/', always_commit=True)
crawler_queue = queue.Queue()
app = FastAPI(docs_url="/")

@app.post("/queue_document")
async def add_synonym_to_queue(url:URL):
    try:
        crawler_queue.put(url.url)
        return Response(status_code=201)
    except:
        return []
    
def crawler(url):
    print(f"crawling {url}")
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
 
def updateSynonyms(word):
    try:
        print("processing synonyms for "+ word)
        synonyms = requests.get(f"http://{synonym_api}:8091/spa?word={word}").json()
        synonyms.append(word) #in case the synonyms didn't return it 
        if len(synonyms) > 1:
            update_response = requests.post(f"http://{synonym_updater}:8092/update", data=json.dumps(synonyms))
            update_response.raise_for_status()
    except:
        print('error updating synonyms for ' + word)

def getDocument(soup,url):
    #Process text.
    #Remove tags, ccs,Javascript.
    text = soup.get_text()   
    #Get Tokens
    tokens = getTokenz(text)

    for token in tokens:
        updateSynonyms(token)

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

def consume_queue(crawler_queue):
    while True:
        try:
            if not crawler_queue.empty():
                crawler(crawler_queue.get())
        except:
            print(datetime.now().isoformat() + " " + traceback.format_exc())
        time.sleep(run_interval)

t1 = Thread(target = consume_queue, args=(crawler_queue,))
t1.setDaemon(True)
t1.start()


if __name__=="__main__":
    crawler_queue.put("https://www.it-swarm-es.com/es/python/como-obtener-sinonimos-de-nltk-wordnet-python/1041861904/")
    uvicorn.run("main:app",host='localhost', port=8094, reload=True, debug=True)