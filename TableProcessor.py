# -*- coding: utf-8 -*-
"""
Created on Wed Oct 26 10:15:08 2022

@author: ASUS
"""

import warnings
warnings.filterwarnings("ignore")
import pandas as pd
import os
import re
import openpyxl
from openpyxl import load_workbook
import numpy as np
import math
from IPython.display import clear_output as clear
from tpot import TPOTRegressor
from sklearn.metrics import r2_score
from sklearn.metrics import *
import sys
from setting import keywords
from setting import interested_parameters

word_dic = {"temperature":"temperature",
            "tin":"Inlet temperature",
            "temp": "temperature", 
            "°c": "temperature",
            "tout":"Outlet temperature",
            "yield":"yield",
            "moisture":"moisture",
            "flow rate": "feed flow rate"
        }

def get_Listfiles(path):
    Filelist = []
    for home, dirs, files in os.walk(path):
        for file in files:
            # include path
            Filelist.append(os.path.join(home, file))
            #Filelist.append(file)
    return Filelist

files = get_Listfiles("./tables")
tem = files.copy()
files = []
for i in tem:
    new = i.replace("\\","/")
    if new[-4:] == "xlsx":
        files.append(new)
        
def filter_out_string(self):
    count = 0
    self = self.replace(" ","")
    for l in self:
        if str(l).isdigit():
            count += 1
    if (count / len(self)) >= 0.5:
        return self
    else:
        return np.nan
    
def process_plus_or_negative(self):
    if type(self) == str:
        if "±" in self:
            digits_list = re.findall(r"[-]?(?:\d*\.\d+|\d+)±", self)
            return digits_list[0]
        else:
            return self
        
def find_longest_digits(self):
    if type(self) == str:
        digits_list = []
        digits_list = re.findall(r"[-]?(?:\d*\.\d+|\d+)",self)
        max_len = 0
        for i in digits_list:
            if len(i) > max_len:
                max_len = len(i)
        for i in digits_list:
            if len(i) == max_len:
                return i
    else:
        return self

entire_table = pd.DataFrame()
entire_tables_list = []
for table_path in files:
    try:
        table_excel=pd.read_excel(table_path, engine="openpyxl")
    except:
        continue
    table_excel = table_excel.astype(str)
    column_name = []
    column_name = table_excel.columns
    new_df = pd.DataFrame()
    for i in column_name:
        col_name_contain = False
        for key in word_dic.keys():
            if key in i.lower():
                new_df[word_dic[key]] = table_excel[i]
                col_name_contain = True
                break
        if col_name_contain == True:
            continue
        else:
            for key in word_dic.keys():
                original_column = table_excel[i].tolist()
                new_column = []
                length = len(original_column)
                for index in range(length):
                    new_column.append(np.nan)
                    if key in original_column[index].lower():
                        try:
                            new_column.extend(original_column[index + 1:])
                            new_df[word_dic[key]] = new_column
                        except:
                            break
    if not new_df.empty:
        entire_tables_list.append(new_df)
entire_table = pd.concat(entire_tables_list, axis=0)
entire_table.replace(to_replace = "nan", value = np.nan,inplace = True)
entire_table = entire_table.astype(str)
entire_table.to_csv("raw_tables.csv",index = False)
# Threshold 0.5 to filter out the element with less than 50% digits
# E.g "abc1234" -> 4/7 > 50%, will be regarded as valid data
entire_table = entire_table.applymap(filter_out_string)
entire_table = entire_table.applymap(process_plus_or_negative)
entire_table = entire_table.applymap(find_longest_digits)
entire_table = entire_table.astype(float)
entire_table = entire_table.reset_index(drop = True)
entire_table.to_csv("process_tables.csv",index = False)

print("Parameters found: ",list(entire_table.columns))
print("Total number of instances: ", len(entire_table))

while True:
    while True:
        type_1_error = False
        type_2_error = False
        user_in = input(f"Please type in the independent variables (no more than {len(entire_table.columns) - 1}): ").split(",")
        for i in user_in:
            if i in entire_table.columns:
                continue
            else:
                print("Invalid input, please type in again !")
                type_1_error = True
                break
        if type_1_error:
            continue
        else:
            if 0 < len(user_in) <= len(entire_table.columns) - 1:
                break
            else:
                print("Incorrect number of inputs, please type in again !")
                type_2_error = True
                continue
    while True:
        user_de = input("Please type in the dependent variables (must be 1): ").split(",")
        if len(user_de) != 1:
            print("Invalid input, please type in again !")
            continue
        if user_de[0] not in entire_table.columns:
            print("Invalid input, please type in again !")
            continue
        break
    if user_de[0] in user_in:
        print("Error: same varaible is simultaneously independent variable and dependent variable ! ")
        continue
    clear()
    break
print("The independent parameters are: ", user_in)
print("The dependent parameter is: ", user_de)
print("We will use",user_in,"to predict",user_de,".")

tem = entire_table.copy()
select = user_in.copy()
select.extend(user_de)
data = tem[select]
data = data.dropna(axis=0, how="all")
if data.empty: 
    output = tem[select]
    name = "+".join(i for i in select)
    output.to_csv(name + ".csv", index = False)
    sys.exit("Insufficient data, fail to predict the values.")
train = data.dropna(axis=0, how="any")
if train.empty:
    output = tem[select]
    name = "+".join(i for i in select)
    output.to_csv(name + ".csv", index = False)
    sys.exit("Insufficient data, fail to predict the values.")
train_x = train[user_in].reset_index(drop = True)
train_y = train.drop(user_in, axis=1).reset_index(drop = True)
test_x = data.dropna(axis=0, subset = user_in).drop(train.index)[user_in].reset_index(drop = True)
# Converting to array
train_x = np.array(train_x)
train_y = np.array(train_y)
test_x = np.array(test_x)

tpot = TPOTRegressor(generations=10, population_size = round(len(train_x) * 0.8) , verbosity = 2, scoring = "neg_mean_absolute_error")
tpot.fit(train_x, train_y)
test_y = tpot.predict(test_x)

# Evaluation
def score_print(results,testing_target):
    """
    evaluate model performance
    """
    print(f"model MSE is {round(mean_squared_error(results,testing_target), 2)}")
    print(f"model R2 is {round(r2_score(results,testing_target) * 100, 2)} %")
    
predict_train = tpot.predict(train_x)
score_print(predict_train, train_y)

output_train = pd.DataFrame()
output_train[user_in] = train_x
output_train[user_de] = train_y
output_test = pd.DataFrame()
output_test[user_in] = test_x
test_y = test_y.reshape((len(test_y), 1))
output_test[user_de] = test_y
output = pd.concat([output_train, output_test], axis = 0)
output = output.reset_index(drop = True)

name = "+".join(i for i in select)
output.to_csv(name + ".csv", index = False)