import pymupdf
import streamlit as st
import pandas as pd


"""
ABOUT
__________________
this script uses takes data from the aquatic hazards in a MSDS and guidance from UK REACH CLP to determine the aquatic hazards of a mixture.

https://www.hse.gov.uk/pesticides/assets/docs/CLP-Hazard-Classification-and-Labelling-Guidance-Note-September-2014.pdf

using the summation method in 3.3.3 see table 3 as above.

assuming in this version that the M factor is always 1.

__________________

"""

#IMPORT THE DATA


#add msds pdf here 
doc = pymupdf.open("MSDS.pdf")

#or use a file uploader in streamlit
#doc=st.file_uploader("Upload MSDS PDF", type="pdf")


#DETERMINE THE PAGES WITH TABLES


#taking the page numbers of the ingredients in the MSDS
page_numbers = st.text_input("page numbers starting at 0 separated by commas", "2,3,4")

#to do. make this into list comprehension 

#split the input string into a list
page_number_list=page_numbers.split(",")


#find the min and max page numbers
for i in page_number_list:
    largest=page_number_list[0]
    for i in page_number_list:
        if int(i) > int(largest):
            largest = i

    smallest=page_number_list[0]
    for i in page_number_list:
        if int(i) < int(smallest):
            smallest = i

#make the list
page_number_list = range(int(smallest), int(largest)+1)


#to do. would be good to view the tables extracted from the MSDS pages



#LOOP THROUGH THE PAGES AND TABLES


#empty lists to fill the data
h400_values = []
h410_values = []
h411_values = []
h412_values = []
h413_values = []


#use the list to find the tables
for page_number in page_number_list:
    page = doc[page_number]
    tables = page.find_tables()

    #loop through the tables
    for table in tables:
        data = table.extract()



        #looping through the data in the tables 

        for row in data:
            # Check classification column
            if "(H400)" in row[6]:
                # Add concentration
                h400_values.append(float(row[5]))
    
            if "(H410)" in row[6]:
                h410_values.append(float(row[5]))

            if "(H411)" in row[6]:
                h411_values.append(float(row[5]))

            if "(H412)" in row[6]:
                h412_values.append(float(row[5]))

            if "(H413)" in row[6]:
                h413_values.append(float(row[5]))




print("this is H400", h400_values)
print("-----")
print("this is H410", h410_values)
print("-----")
print("this is H411", h411_values)
print("-----")
print("this is H412", h412_values)
print("-----")
print("this is H413", h413_values)



#make a pandas dataframe of the the H# values
#you cant make a pandas dataframe with lists of different lengths directly 
#so use pd.Series


df = pd.DataFrame({
    "H400": pd.Series(h400_values),
    "H410": pd.Series(h410_values),
    "H411": pd.Series(h411_values),
    "H412": pd.Series(h412_values),
    "H413": pd.Series(h413_values)
})

"""
COLLECTED H# VALUES FROM MSDS
_____________________________

"""

#print out the dataframe in streamlit
st.dataframe(df)


#to do. M factor input needs to be defined



#DETERMINATION OF H#


#the calculation as described in table 3 is. 
#H400 = % fragrance in mix(MSDS_conc) * (substance % H400 acute category 1/100) * M factor
#H410 = % fragrance in mix(MSDS_conc) * (substance % H410 chronic category1 1/100) * M factor
#H411 = % fragrance in mix(MSDS_conc) * (((substance % H410 chronic category1 1/100) * (M factor * 10))+(substance % H411)))
#H412 = % fragrance in mix(MSDS_conc) * ((substance % H410 chronic category1 1/100) * (M factor *100) + ((substance % H411 1/100) *(10) + (substance % H412 1/100 )
#H413 = % fragrance in mix(MSDS_conc) * (substance % H410 chronic category1 1/100) + (substance % H411 chronic category2 1/100 )+(substance % H412 chronic category3 1/100)+(substance %H413 chronic category 4 1/100 ) 

#calculate out the % of each first

#inputs required vary for each H# collection
#MSDS_conc is how much of MSDS material will be used in the mix
#M is the M factor update is needed to pull the M factor from the other columns of the MSDS

MSDS_conc=3.75
M = 1 

#acute category 1 h400
def calculate_h400(values):
    for i in values:
        total_h400=MSDS_conc*(i/100)
        h400_percentages.append(total_h400)

#chronic category 1 h410
def calculate_h410(values):
    for i in values:
        total_h410=MSDS_conc*(i/100)
        h410_percentages.append(total_h410)

#chronic category 2 h411
def calculate_h411(values):
    for i in values:
        total_h411=MSDS_conc*(i/100)
        h411_percentages.append(total_h411)

#chronic category 3 h412
def calculate_h412(values):
    for i in values:
        total_h412=MSDS_conc*(i/100)
        h412_percentages.append(total_h412)

#chronic category 4 h413
def calculate_h413(values):
    for i in values:
        total_h413=MSDS_conc*(i/100)
        h413_percentages.append(total_h413)



h400_percentages = []
h410_percentages = []
h411_percentages = []
h412_percentages = []
h413_percentages = []

calculate_h400(h400_values)
calculate_h410(h410_values)
calculate_h411(h411_values)
calculate_h412(h412_values)
calculate_h413(h413_values)

#sum the values in the percentages lists
#this is then the total w/w% of each h# in the MSDS 

h400_total_percentage = sum(h400_percentages)
h410_total_percentage = sum(h410_percentages)
h411_total_percentage = sum(h411_percentages)
h412_total_percentage = sum(h412_percentages)
h413_total_percentage = sum(h413_percentages)

#print the total percentages for each H# code to 3 significant figures
print("H400 total percentage:", round(h400_total_percentage, 3))
print("H410 total percentage:", round(h410_total_percentage, 3))
print("H411 total percentage:", round(h411_total_percentage, 3))
print("H412 total percentage:", round(h412_total_percentage, 3))
print("H413 total percentage:", round(h413_total_percentage, 3))


#then the calculation step taking into account M factor 

H400_actual=h400_total_percentage*M

H410_actual=h410_total_percentage*M

H411_actual=((h410_total_percentage*(10*M))+(h411_total_percentage))

H412_actual=((h410_total_percentage*(100*M)+(h411_total_percentage*10)+h412_total_percentage))

H413_actual=(h410_total_percentage+h411_total_percentage+h412_total_percentage+h413_total_percentage)


"""
LABELLING REQUIRED
__________________

"""


st.write("H400 actual:", H400_actual)
st.write("H410 actual:", H410_actual)
st.write("H411 actual:", H411_actual)
st.write("H412 actual:", H412_actual)
st.write("H413 actual:", H413_actual)



#if the total percentage is bigger than 25% than it needs labelling as that H#
if H400_actual >= 25:
    print("H400 needs labelling")
    st.write("H400 needs labelling")
    

if H410_actual >= 25:
    print("H410 needs labelling")
    st.write("H410 needs labelling")
    

elif H411_actual >= 25:
    print("H411 needs labelling")
    st.write("H411 needs labelling")
    

elif H412_actual >= 25:
    print("H412 needs labelling")
    st.write("H412 needs labelling")
    

elif H413_actual >= 25:
    print("H413 needs labelling")
    st.write("H413 needs labelling")
