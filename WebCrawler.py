# -*- coding: utf-8 -*-
"""
Created on Tue Aug 30 14:18:25 2022

@author: ASUS
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import warnings 
from bs4 import BeautifulSoup
from urllib import parse
import urllib
import os
from fuzzywuzzy import fuzz
import warnings
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
# nltk.download("stopwords")
# nltk.download("punkt")

LIMIT = 80
ZERO = 0
TWO = 2
warnings.filterwarnings('ignore')

#getting title, url link, doi number of articles, storing the information in a csv file.
def get_info(word, base, filt, num_page):
    next_page = base + word + filt
    url = base + word + filt
    new_url = []
    doi = []        
    title = []
    for num in range(num_page):
        r = requests.get(next_page)
        r.encoding = "utf-8"
        soup = BeautifulSoup(r.text, "html.parser")
        names = soup.findAll("a", class_="docsum-title")
        dios = soup.findAll("span", class_="docsum-journal-citation full-journal-citation")
        href = []
        for name in names:
            title.append(name.text.strip().replace(".","").replace("/","").replace("\\","").replace(":","").replace(">","").replace("?","").replace("<","").replace("*",""))
        for search_result in names:
            href.append(search_result["href"])
        for result in dios:
            code = re.findall(r'doi: \d+.\d+', result.text)
            doi.append(code)
        for i in href:
            new_url.append(base+i)
        next_page = url + "&page=" + str(num + 2)
    result = pd.DataFrame({"URL":new_url, "doi": doi, "title":title})
    result.to_csv(word + ".csv", index = False)

    
def get_url (keywords, interested_parameters):
    print("start searching for articles...")
    base = "https://pubmed.ncbi.nlm.nih.gov/?term="
    filt = "&filter=simsearch2.ffrft&filter=simsearch3.fft"
    for word in keywords:
        url = base + word + filt
        r = requests.get(url)
        r.encoding = "utf-8"
        soup = BeautifulSoup(r.text, "html.parser")
        pages = soup.find("label", class_="of-total-pages").text
        num_page = int(re.findall(r'\d+', pages)[0])
        get_info(word, base, filt, num_page)
        check_relevance(keywords, interested_parameters)
        
def check_relevance(keywords, interested_parameters):
    print("start checking relevance between articles and parameters...")
    for word in keywords:
        articles = pd.read_csv(word+'.csv')
        articles.reset_index(drop=True, inplace=True)
        titles = []
        abstracts = []
        scores = []
        for i in range(len(articles)):
            rev = 0
            r = requests.get(articles.iloc[i, ZERO])
            r.encoding = "utf-8"
            soup = BeautifulSoup(r.text, "html.parser")
            try:
                title = soup.find("h1", class_="heading-title").text.lower()
                abstract = soup.find("div", class_="abstract-content selected").find("p").text.lower()
                titles.append(title)
                abstracts.append(abstract)
                for iword in interested_parameters:
                    if fuzz.partial_token_set_ratio(iword, title) >= LIMIT:
                        rev += 1
                    if fuzz.partial_token_set_ratio(iword, abstract) >= LIMIT:
                        rev += 1
                score = rev / (TWO * len(interested_parameters))
                scores.append(score)
            except (AttributeError):
                titles.append("Not found")
                abstracts.append("Not found")
                scores.append(ZERO)
        articles["title"] = titles
        articles["abstract"] = abstracts
        articles["relevance"] = scores
        articles = articles[articles["title"] != "Not found"]
        articles.reset_index(drop=True, inplace=True)
        articles.to_csv(word+'.csv', index=None)

def check_relevance_advanced(keywords,interested_parameters):
    nltk.download('punkt')
    nltk.download('stopwords')
    print("Applying advanced relevance checking...")
    relevanced = []
    for word in keywords:
        articles = pd.read_csv(word+".csv")
        articles["token_title"] = articles.iloc[:, 2].apply(lambda x: word_tokenize(x))
        articles["abstract"] = articles.iloc[:, 3].apply(lambda x: word_tokenize(x))
        articles["sum"] = articles.iloc[:, 5] + articles.iloc[:, 3]
        stop_word = set(stopwords.words("english"))
        articles["token_title"] = articles.iloc[:, 5].apply(lambda x: [w for w in x if not w in stop_word])
        articles["abstract"] = articles.iloc[:, 3].apply(lambda x: [w for w in x if not w in stop_word])
        articles["sum"] = articles.iloc[:, 5] + articles.iloc[:, 3]
        query = ["spray", "drying"]
        articles["term number"] = 0 #6
        articles["tf"] = 0 # 7
        for word in interested_parameters:
            articles["term number"] += articles.iloc[:, 6].apply(lambda x: x.count(word))
            articles["tf"] += articles.iloc[:, 6].apply(lambda x: x.count(word) / len(x))
        scores = []
        for i in range(len(articles)):
            rev = 0
            lt = len(articles.iloc[i, 5])
            la = len(articles.iloc[i, 3])
            weight = lt / (lt + la)
            for word in query:
                for w in articles.iloc[i, 5]:
                    if fuzz.partial_token_set_ratio(word, w) >= 80:
                        rev += 1 - weight
                        break
                for w in articles.iloc[i, 3]:
                    if fuzz.partial_token_set_ratio(word, w) >= 80:
                        rev += weight
                        break
            score = rev / len(query)
            scores.append(score)
        articles["r2"] = scores
        articles = articles.loc[articles["relevance"] != 0]
        relevanced.append(articles)
    relevanced = pd.concat([i for i in relevanced], axis = 0)
    relevanced.to_csv("relevanced.csv", index=None)
def remove_unrelated_articles():
    relevanced = pd.read_csv("relevanced.csv")
    relevanced = relevanced.loc[relevanced["tf"] != 0].reset_index(drop = True)
    relevanced.drop_duplicates(subset=["URL"], inplace=True, keep = "first")
    relevanced.to_csv("relevanced_tf.csv", index=None)
    return None
def get_download_link(keywords):
    download_link = pd.DataFrame()
    f1 = pd.read_csv('relevanced_tf.csv')
    #1155
    f1_1155 = f1[f1['doi']=="['doi: 10.1155']"]
    link_1155 = doi_1155(f1_1155)
    if link_1155.empty != True:
        download_link = link_1155
    #2147
    f1_2147 = f1[f1['doi']=="['doi: 10.2147']"]
    link_2147 = doi_2147(f1_2147)
    if link_2147.empty != True:
        download_link = pd.concat([download_link,link_2147],ignore_index=True)
    #3389
    f1_3389 = f1[f1['doi']=="['doi: 10.3389']"]
    link_3389 = doi_3389(f1_3389)
    if link_3389.empty != True:
        download_link = pd.concat([download_link,link_3389],ignore_index=True)
    #1002
    f1_1002 = f1[f1['doi']=="['doi: 10.1002']"]
    link_1002 = doi_1002(f1_1002)
    if link_1002.empty != True:
        download_link = pd.concat([download_link,link_1002],ignore_index=True)
    #1007
    f1_1007 = f1[f1['doi']=="['doi: 10.1007']"]
    link_1007 = doi_1007(f1_1007)
    if link_1007.empty != True:
        download_link = pd.concat([download_link,link_1007],ignore_index=True)
    #1248
    f1_1248 = f1[f1['doi']=="['doi: 10.1248']"]
    link_1248 = doi_1248(f1_1248)
    if link_1248.empty != True:
        download_link = pd.concat([download_link,link_1248],ignore_index=True)
    #1021
    f1_1021 = f1[f1['doi']=="['doi: 10.1021']"]
    link_1021 = doi_1021(f1_1021)
    if link_1021.empty != True:
        download_link = pd.concat([download_link,link_1021],ignore_index=True)
    #1371
    f1_1371 = f1[f1['doi']=="['doi: 10.1371']"]
    link_1371 = doi_1371(f1_1371)
    if link_1371.empty != True:
        download_link = pd.concat([download_link,link_1371],ignore_index=True)
    #1038
    f1_1038 = f1[f1['doi']=="['doi: 10.1038']"]
    link_1038 = doi_1038(f1_1038)
    if link_1038.empty != True:
        download_link = pd.concat([download_link,link_1038],ignore_index=True)
    #3390
    f1_3390 = f1[f1['doi']=="['doi: 10.3390']"]
    link_3390 = doi_3390(f1_3390)
    if link_3390.empty != True:
        download_link = pd.concat([download_link,link_3390],ignore_index=True)
    download_link.title = download_link.title.apply(lambda x: x.replace("\n",""))
    download_link.title = download_link.title.apply(lambda x: x.lstrip(" "))
    download_link.title = download_link.title.apply(lambda x: x.rstrip(" "))
    download_link.title.replace(".","").replace("/","").replace("\\","").replace(":","").replace(">","").replace("?","").replace("<","").replace("*","")
    download_link.to_csv("download_link.csv",index = False)
    return None

def doi_1155(f1):
    print("getting download link for doi 1155...")
    dlinklist = []
    title = []
    if len(f1) != 0:
        for i in range(len(f1)):
            r = requests.get(f1.iloc[i, 0])
            r.encoding = "utf-8"
            soup = BeautifulSoup(r.text, "html.parser")
            try:
                new_url = soup.find("span", class_="identifier doi").find("a", class_="id-link")['href']
            except:
                continue
            r = requests.get(new_url)
            r.encoding = "utf-8"
            soup = BeautifulSoup(r.text, "html.parser")
            try:
                download_link = soup.find('div', class_='threeColumn__RightWrapper-sc-1crxfky-2 imlryA rightWrapper').find('a')['href']
            except:
                continue
            dlinklist.append(download_link)
            title.append(f1.iloc[i, 2])
    dlinkdf = pd.DataFrame({"title":title, "URL":dlinklist})
    return dlinkdf
    
def doi_2147(f1):
    print("getting download link for doi 2147...")
    dlinklist = []
    title = []
    if len(f1) != 0:
        for i in range(len(f1)):
            r = requests.get(f1.iloc[i, 0])
            r.encoding = "utf-8"
            soup = BeautifulSoup(r.text, "html.parser")
            try:
                new_url = soup.find("span", class_="identifier doi").find("a", class_="id-link")['href']
                r = requests.get(new_url)
                r.encoding = "utf-8"
                soup = BeautifulSoup(r.text, 'html.parser')
                link = soup.find('a', class_='download-btn print-hide')['href']
                download_link = 'https://www.dovepress.com/' + link + '?download=true'
                dlinklist.append(download_link)
                title.append(f1.iloc[i, 2])  
            except:
                continue
    dlinkdf = pd.DataFrame({ "title":title, "URL":dlinklist})
    return dlinkdf
    
def doi_3389(f1):
    print("getting download link for doi 3389...")
    dlinklist = []
    title = []
    if len(f1) != 0:
        for i in range(len(f1)):
            r = requests.get(f1.iloc[i, 0])
            r.encoding = "utf-8"
            soup = BeautifulSoup(r.text, "html.parser")
            try:
                new_url = soup.find("span", class_="identifier doi").find("a", class_="id-link")['href']
                r = requests.get(new_url)
                r.encoding = "utf-8"
                soup = BeautifulSoup(r.text, 'html.parser')
                link = soup.find('ul',class_='dropdown-menu').find('a')['href']
                download_link = 'https://www.frontiersin.org' + link
                dlinklist.append(download_link)
                title.append(f1.iloc[i, 2])
            except:
                continue
    dlinkdf = pd.DataFrame({ "title":title, "URL":dlinklist})
    return dlinkdf
    
def doi_1002(f1):
    print("getting download link for doi 1002...")
    websites_1002 = []
    title = []
    if len(f1) != 0:
        for i in range(len(f1)):
            newurl=f1.iloc[i, 0]
            r = requests.get(newurl)
            r.encoding = "utf-8"
            soup = BeautifulSoup(r.text, "html.parser")
            if soup.find("span", class_="identifier doi") is None:
                continue
            else:
                new_url_raw = soup.find("span", class_="identifier doi").find("a", class_="id-link")['href']
                new_url="https://onlinelibrary.wiley.com/doi/pdfdirect/10.1002"+new_url_raw[23:]+"?download=true"
                websites_1002.append(new_url)
                title.append(f1.iloc[i, 2])
    dlinkdf = pd.DataFrame({ "title":title, "URL":websites_1002})
    return dlinkdf
    
def doi_1007(f1):
    print("getting download link for doi 1007...")
    download_links_1007 = []
    title = []
    search_base = "https://www.ncbi.nlm.nih.gov/pmc/?term="
    download_base = "https://www.ncbi.nlm.nih.gov"
    if len(f1) != 0:
        for i in range(len(f1)):
            url = f1.iloc[i,0]
            r = requests.get(url)
            r.encoding = "utf-8"
            soup = BeautifulSoup(r.text, "html.parser")
            try:
                full_id = soup.find("a",class_ = "id-link").text
                fullid = re.findall(r'PMC\d+', full_id)[0]
                full_text_link = search_base + fullid
                r = requests.get(full_text_link)
                r.encoding = "utf-8"
                soup = BeautifulSoup(r.text, "html.parser")
                download_link = soup.find("div",class_ = "links").findAll("a")[2]["href"]
                download_link = download_base + download_link
                download_links_1007.append(download_link)
                title.append(f1.iloc[i, 2])
            except:
                continue
    dlinkdf = pd.DataFrame({ "title":title, "URL":download_links_1007})
    return dlinkdf    

def doi_1248(f1):
    print("getting download link for doi 1248...")
    dlinklist_1248 = []
    title = []
    if len(f1) != 0:
        for i in range(len(f1)):
            r = requests.get(f1.iloc[i, 0])
            r.encoding = "utf-8"
            soup = BeautifulSoup(r.text, "html.parser")
            try:
                new_url = soup.find("span", class_="identifier doi").find("a", class_="id-link")['href']
                r = requests.get(new_url)
                r.encoding = "utf-8"
                soup = BeautifulSoup(r.text, "html.parser")
                pdf_link = soup.find('div', class_='col-md-6 print-non-disp').find('a', class_="thirdlevel-pdf-btn")['href']
                dlinklist_1248.append(pdf_link)
                title.append(f1.iloc[i, 2])
            except:
                continue
    dlinkdf = pd.DataFrame({ "title":title, "URL":dlinklist_1248})
    return dlinkdf

def doi_1021(f1):
    print("getting download link for doi 1021...")
    websites_1021 = []
    title = []
    if len(f1) != 0:
        for i in range(len(f1)):
            newurl=f1.iloc[i, 0]
            r = requests.get(newurl)
            r.encoding = "utf-8"
            soup = BeautifulSoup(r.text, "html.parser")
            try:
                new_url_raw = soup.find("span", class_="identifier doi").find("a", class_="id-link")['href']
                new_url="https://pubs.acs.org/doi/pdf"+new_url_raw[15:]+"?download=true"
                websites_1021.append(new_url)
                title.append(f1.iloc[i, 2])
            except:
                continue
    dlinkdf = pd.DataFrame({ "title":title, "URL":websites_1021})
    return dlinkdf

def doi_1371(f1):
    websites_1371 = []
    title = []
    print("getting download link for doi 1371...")
    if len(f1) != 0:
        for i in range(len(f1)):
            r = requests.get(f1.iloc[i, 0])
            r.encoding = "utf-8"
            soup = BeautifulSoup(r.text, "html.parser")
            try:
                new_url_raw = soup.find("span", class_="identifier doi").find("a", class_="id-link")['href']
                new_url="https://journals.plos.org/plosone/article/file?id=10.1371/"+new_url_raw[24:]+"&type=printable"
                websites_1371.append(new_url)
                title.append(f1.iloc[i, 2])
            except:
                continue
    dlinkdf = pd.DataFrame({ "title":title, "URL":websites_1371})
    return dlinkdf

def doi_1038(f1):
    print("getting download link for doi 1038...")
    websites_1038 = []
    title = []
    if len(f1) != 0:
        for i in range(len(f1)):
            r = requests.get(f1.iloc[i, 0])
            r.encoding = "utf-8"
            soup = BeautifulSoup(r.text, "html.parser")
            try:
                new_url = soup.find("span", class_="identifier doi").find("a", class_="id-link")['href']
                r = requests.get(new_url)
                r.encoding = "utf-8"
                soup = BeautifulSoup(r.text, "html.parser")
                current = soup.find("head").find(attrs={"name":"prism.url"})['content'] #meta
                download = current+".pdf"
                websites_1038.append(download)
                title.append(f1.iloc[i, 2])
            except:
                continue
    dlinkdf = pd.DataFrame({ "title":title, "URL":websites_1038})
    return dlinkdf

def doi_3390(f1):
    search_base = "https://www.ncbi.nlm.nih.gov/pmc/?term="
    download_base = "https://www.ncbi.nlm.nih.gov"
    print("getting download link for doi 3390...")
    download_links_3390 = []
    title = []
    if len(f1) != 0:
        for i in range(len(f1)):
            r = requests.get(f1.iloc[i, 0])
            r.encoding = "utf-8"
            soup = BeautifulSoup(r.text, "html.parser")
            try:
                full_id = soup.find("a",class_ = "id-link").text
                fullid = re.findall(r'PMC\d+', full_id)[0]
                full_text_link = search_base + fullid
                r = requests.get(full_text_link)
                r.encoding = "utf-8"
                soup = BeautifulSoup(r.text, "html.parser")
                download_link = soup.find("div",class_ = "links").findAll("a")[2]["href"]
                download_link = download_base + download_link
                download_links_3390.append(download_link)
                title.append(f1.iloc[i, 2])
            except:
                continue
    dlinkdf = pd.DataFrame({ "title":title, "URL":download_links_3390})
    return dlinkdf
#def get_doi_count(keywords):
#    df1 = pd.read_csv("./keywords/"+keywords[0]+'.csv', index_col=0)
#    for word in keywords[1:]:
#        df2 = pd.read_csv("./keywords/"+word+'.csv', index_col=0)
#        df1 = df1.append(df2, ignore_index=True)
#        count = df1.groupby(['doi']).size().sort_values(ascending=False)
#        count.to_csv("./keywords/"+word+"_doi_count.csv")
#    return count

#get download links