#imports 
from pathlib import Path
import pandas as pd 
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

"""
cosine similarity is a method used to distinguish between two FTIR spectra

if its expected that they are going to be similar, need to introduce integration as metadata and compare

"""


#name the folder where the csv are
folder=Path("/home/")

#store the csv files in a empty dictionary 
store={}

#add them to the store 
for i in folder.glob("*.CSV"):


    #.stem gives the file name
    #print(i.stem)
    name=i.stem

    #reading in the FTIR data
    data=pd.read_csv(i)

    #name the cols in the data, this takes a list  
    cols=["wavenumber","absorbance"]
    data.columns=cols

    #store as a dictionary 
    store[name]=data


for l,m in store.items():
    print(l)

reference = store["key"]["absorbance"].values.reshape(1, -1)
unknown = store["key2"]["absorbance"].values.reshape(1, -1)

similarity = cosine_similarity(reference, unknown)[0, 0]
print(similarity * 100)
