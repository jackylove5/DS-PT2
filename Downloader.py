# -*- coding: utf-8 -*-
"""
Created on Tue Aug 30 14:18:50 2022

@author: ASUS
"""

import os
from urllib.request import urlretrieve
import wget
from selenium import webdriver
import pandas as pd
import time

#getting download links using webdriver
def download_pdf():
    link_df = pd.read_csv("download_link.csv")
    option = webdriver.ChromeOptions()
    option.add_experimental_option('prefs', {
        "download.default_directory": "E:\\Test\\pdfs", #Change default directory for downloads
        "download.prompt_for_download": False, #To auto download the file
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True,#It will not show PDF directly in chrome
    })    
    option.add_experimental_option("excludeSwitches", ['enable-automation', 'enable-logging'])
    driver = webdriver.Chrome(options=option)
    for i in range(len(link_df)):
        downloaded = False
        d_link = link_df.iloc[i,1]
        driver.get(d_link)
        while downloaded == False:
            try:
                time.sleep(1)
                os.chdir("E:\\Test\\pdfs")
                files = filter(os.path.isfile, os.listdir("E:\\Test\\pdfs"))
                files = [os.path.join("E:\\Test\\pdfs", f) for f in files] # add path to each file
                files.sort(key=lambda x: os.path.getmtime(x))
                if len(files) != 0:
                    newest_file = files[-1]
                    new_name = link_df.iloc[i,0].replace(".","").replace("/","").replace("\\","").replace(":","").replace(">","").replace("?","").replace("<","").replace("*","")[:200]
                    os.rename(newest_file, new_name +".pdf")
                    downloaded = True
            except:
                continue
