# -*- coding: utf-8 -*-
"""
Created on Tue Aug 30 14:05:00 2022

@author: Huahu Wen
"""

import WebCrawler
import Downloader
import setting
import Extractor
import TableProcessor

#getting keywords
keywords = setting.keywords
interested_parameters = setting.interested_parameters

#getting download links
WebCrawler.get_url(keywords,interested_parameters)
WebCrawler.check_relevance_advanced(keywords,interested_parameters)
WebCrawler.remove_unrelated_articles()
WebCrawler.get_download_link(keywords)

#downloading pdfs
Downloader.download_pdf()
#transforming pdfs into images
Extractor.to_image()
#extracting tables from images
Extractor.to_table()

#Table merging and TPOT
TableProcessor