# -*- coding: utf-8 -*-
"""
Created on Tue Aug 30 14:19:49 2022

@author: ASUS
"""

import os
import tempfile

from tkinter import Tk
from tkinter.filedialog import askopenfilename
from tqdm import tqdm
from pdf2image import convert_from_path

import os
import cv2
from paddleocr import PPStructure,draw_structure_result,save_structure_res

#transform pdf into image
def to_image():
    file_path = os.listdir('./pdfs/')
    print("Transforming pdfs into images...")
    for file_name in file_path:
        abs_pdf_path = ('./pdfs/'+file_name)
        base = os.path.splitext(file_name)[0]
        if not file_name:
            print("Error in opening the file")
            exit()
        else:
            print("Selected file:", file_name)
            print("Processing...")
    
        if not os.path.exists('./images/'+base):
            os.mkdir('./images/'+base)
            abs_output_path = os.path.abspath('./images/'+base)
        else:
            abs_output_path = os.path.abspath('./images/'+base)
        page_number =1
        try:
            pdf_images = convert_from_path(pdf_path=abs_pdf_path, output_folder=abs_output_path)
            print("\nTotal number of pages = ", len(pdf_images), "\n")
            for page in tqdm(pdf_images):
                pages_path = './images/'+base+'/page'
                if not os.path.exists('./images/'+base+'/page'):
                    os.mkdir('./images/'+base+'/page')
                image_name = pages_path + '/' + str(page_number) + '.jpg'
                page.save(image_name, 'JPEG')
                page_number += 1
        except:
            print("Error in performing the required action")

#extracting tables from articles in images format
def to_table():
    table_engine = PPStructure(show_log=False, use_gpu=False)
    file = os.listdir('./images')
    for f in file:
        article_name = f
        pages_path = './images/' + f + '/page'
        try:
            image = os.listdir(pages_path)
        except:
            continue
        for i in image:
            base = os.path.splitext(i)[0]
            image_path = pages_path + '/' + i
            print(image_path)
            img = cv2.imread(image_path)
        
        
            result = table_engine(img)
            for j in range(len(result)):
                if result[j]['type'] == 'Table':
                    save_path = './tables/'+ article_name
                    if not os.path.exists(save_path):
                        os.mkdir(save_path)
                    save_structure_res(result,save_path,base+'page')