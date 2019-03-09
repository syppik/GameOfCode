#!/usr/bin/env python
# coding: utf-8

# # NLP for historical newspapers
The goal of this Notebook is to first create a parser that extracts all of the data contained in the Dublin Core XML files. Then we will perform Named Entity Recognition to extract relevant keywords about people, location and events from the text. To finish, we then create a content-based recommendation system for a sample of 47.850 articles. We do so by using the tf-idf method to map the content to a vector space and then compute the cosine similarity between articles. The top 3 articles, with at least 70% of likeness are recommended to the reader.
# In[4]:


# Load needed libraries
import pandas as pd
import os
import xml.etree.ElementTree
from xml.dom import minidom
import glob
from bs4 import BeautifulSoup


# # I. Load all xml files

# In[37]:


folder_path = 'data/export01-newspapers1841-1878/export01-newspapers1841-1878/' # PATH OF ALL DATA 

# This function reads in all the XML files in a directory (and sub-directories recursively) and returns a list of all the XML files
def search_files(directory='.', extension='',show = False):
    extension = extension.lower()
    list_files = []
    for dirpath, dirnames, files in os.walk(directory):
        for name in files:
            if extension and name.lower().endswith(extension):
                list_files.append(os.path.join(dirpath, name))
                if show:
                    print(os.path.join(dirpath, name))
            elif not extension:
                list_files.append(os.path.join(dirpath, name))
                if show:
                    print(os.path.join(dirpath, name))
    return list_files
                
list_files = search_files(folder_path)
print("Nombre de fichier xml:",len(list_files))


# In[38]:


filename = list_files[0]

# This function parses the xml files and converts them json
def xml_file_to_json(filename):
    page = open(filename)
    soup = BeautifulSoup(page.read())
    # dc:relation: ID du journal
    # identifier: ID de l'article
    # filename: nom du fichier xml
    # dc:date: date publication
    # dc:description: contenu
    # dc:type: type (pub, article ...)
    # dc:language: langue detectée
    # dcterms:isPartOf: nom du journal (company)
    # dcterms:hasVersion: lien url vers l'article
    try:
        relation = soup.find('dc:relation').text
    except:
        relation = ""
        
    try:
        identifier = soup.find('identifier').text.split('-')[-1]
    except:
        identifier = ""
        
    try:
        file_name = filename
    except:
        file_name = ""
        
    try:
        dc_date = soup.find('dc:date').text
    except:
        dc_date =  ""
        
    try:
        titre = soup.find('dc:title').text
    except:
        titre = ""
        
    try:
        description = soup.find('dc:description').text
    except:
        description = ""
        
    try:
        dc_type = soup.find('dc:type').text
    except:
        dc_type = ""
        
    try:
        language = soup.find('dc:language').text
    except:
        language = ""
        
    try:
        dctermispartof = soup.find('dcterms:ispartof').text
    except:
        dctermispartof = ""
        
    try:
        dctermhasversion = soup.find('dcterms:hasversion').text
    except:
        dctermhasversion = ""
    page.close()
    
    return {"dc_relation":relation,"identifier":identifier,"filename":file_name,           "dc_date":dc_date,"dc_title":titre,"dc_description":description,"dc_type":dc_type,           "dc_language":language,"dcterms_ispartof":dctermispartof,"dcterms_hasversion":dctermhasversion}

xml_file_to_json(filename)


# In[39]:


# This function returns one dictionary made of all the XML files. The function from before is used in the body of this function
def all_file_to_dict(list_files):
    result = []
    i=0
    for file in list_files:
        i+=1
        result.append(xml_file_to_json(file))
        if i % 1000==0:
            print(i,"/",len(list_files))
        if i>1000:
            break
    return result

result = all_file_to_dict(list_files)


# In[40]:


result


# In[20]:


# We now export the object from above to a csv file
file = open("export_json.csv","w")
i=0
json_data = []
for line in result:
    json_data.append(line)
import json
json_to_export = json.dumps(json_data)
file.write(json_to_export)
file.close()


# In[9]:


# We now reload the file as a Data Frame and create a new column called ID made up of the relation and identifier nodes of the XML files
df = pd.DataFrame(result)
df['ID']=df['dc_relation']+"_"+df['identifier']


# In[11]:


df


# In[12]:


# We export the data frame to a pipe separated values files. We already import this to ELK. This is the MVP.
df.to_csv("_export01-newspapers1841-1878.csv", sep='|', encoding='utf-8',index = False)


# # II. Named entity recognition
Here, we perform Named Entity Recognition which allows to extract much more information from the text of the articles. This will make searching much faster, but also allows reader to glance at the entities that were extracted from the articles and thus have a good clue of the content of the artiles without needing to read it.
# In[2]:


import pandas as pd
import os
import xml.etree.ElementTree
from xml.dom import minidom
import glob
from bs4 import BeautifulSoup


# In[ ]:


# Read in the data from before
df = pd.read_csv("_export01-newspapers1841-1878.csv", sep='|', encoding='utf-8')
df = df[df['dc_type']=='ARTICLE'][df['dcterms_ispartof'] in ["L'indépendence Luxembourgeoise","L'UNION."]]


# In[ ]:


import spacy
from spacy import displacy
from collections import Counter


# In[ ]:


# To load the model for french we first need to dowload it using "python -m spacy download fr_core_news_md"
nlp = spacy.load('fr_core_news_md')


# In[ ]:


# Perform NER
df['Entities'] = df['dc_description'].apply(lambda x: [(X.text, X.label_) for X in nlp(x).ents])


# In[4]:


entities = df['Entities'].values.tolist()


# In[5]:


entities


# In[6]:


from ast import literal_eval

def tuple_to_tags(input_tuple):
    l = literal_eval(input_tuple)
    #print(l)
    LOC = []
    PER = []
    MISC = []
    ORG = []


    for t in l:
        if t[1]=='LOC':
            LOC.append(t[0])
        if t[1]=='PER':
            PER.append(t[0])
        if t[1]=='MISC':
            MISC.append(t[0])
        if t[1]=='ORG':
            ORG.append(t[0])  
    return ["#["+'] #['.join(LOC)+"]","#["+'] #['.join(PER)+"]","#["+'] #['.join(MISC)+"]","#["+'] #['.join(ORG)+"]",' '.join(LOC+PER+MISC+ORG)]


tuple_to_tags(entities[0])


# In[7]:


list_tags = []
for i in range(len(entities)):
    if i%100 == 0:
        print(i,"/",len(entities))
    list_tags.append(tuple_to_tags(entities[i]))


# In[8]:


list_LOC = list(zip(*list_tags))[0]
list_LOC

list_PER = list(zip(*list_tags))[1]
list_PER

list_MISC = list(zip(*list_tags))[2]
list_MISC

list_ORG = list(zip(*list_tags))[3]
list_ORG

list_all = list(zip(*list_tags))[4]


# In[9]:


df['Tags_localisation']=list_LOC
df['Tags_personne']=list_PER
df['Tags_autres']=list_MISC
df['Tags_organisation']=list_ORG
df['All_key_word']=list_all


# In[10]:


df.loc[df['Tags_localisation'] == "#[]", 'Tags_localisation'] = ""
df.loc[df['Tags_personne'] == "#[]", 'Tags_personne'] = ""
df.loc[df['Tags_autres'] == "#[]", 'Tags_autres'] = ""
df.loc[df['Tags_organisation'] == "#[]", 'Tags_organisation'] = ""


# In[11]:


df = df.drop(['clean_description'],axis = 1)
df = df.drop(['Entities'],axis = 1)


# In[12]:


df


# In[13]:


df.to_csv("TAGS_export01-newspapers1841-1878.csv", sep='|', encoding='utf-8',index = False)


# # III. Content-based Recommender system (on article content) #AI #ML #predict
The Content-based recommender system is based on the article content. The idea is to identify the article which talk about the sames topics. To do that we need to vectorize the unstructured article text content. After that we will be able to calculate distance between vectors themself, which also mean : a "distance" or "similarity" between the differents articles. At the end we will be able to determine the most reliable articles for each article
# In[1]:


import pandas as pd
import os
import xml.etree.ElementTree
from xml.dom import minidom
import glob
from bs4 import BeautifulSoup
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer


# In[2]:


df = pd.read_csv("TAGS_V2_export01-newspapers1841-1878.csv", sep='|', encoding='utf-8')
df['Reco 1 - ID']=""
df['Reco 1 - score']=""
df['Reco 1 - Link']=""

df['Reco 2 - ID']=""
df['Reco 2 - score']=""
df['Reco 2 - Link']=""

df['Reco 3 - ID']=""
df['Reco 3 - score']=""
df['Reco 3 - Link']=""
df


# In[21]:


N = 0
STEP = 10000
article_desc = df['dc_description'].values.tolist()[N:N+STEP]
liste_id = df['ID'].values.tolist()
url = df['dcterms_hasversion'].values.tolist()


# In[22]:


# Text vectorization
tfidf = TfidfVectorizer().fit_transform(article_desc)


# In[23]:


# Matrix of similarity generation
# no need to normalize, since Vectorizer will return normalized tf-idf
pairwise_similarity = tfidf * tfidf.T
matrix_similarity = (tfidf * tfidf.T).A
matrix_similarity


# In[24]:


import json
import heapq

# Select 3 most reliable article for all of them
for i in range(len(matrix_similarity)):
    liste_recommandations = []
    #print(liste_id[i])
    for recommandations in heapq.nlargest(4, range(len(matrix_similarity[i])), matrix_similarity[i].__getitem__)[1:]:
        if matrix_similarity[i][recommandations] > 0.7:
            liste_recommandations.append({'ID':liste_id[recommandations],'dcterms_hasversion':url[recommandations],'Recommandation_score':matrix_similarity[i][recommandations]})
    #print(liste_recommandations)
    k=1
    for e in liste_recommandations:
        df.loc[df['ID']==liste_id[i+N],'Reco '+str(k)+' - ID'] = e['ID']
        df.loc[df['ID']==liste_id[i+N],'Reco '+str(k)+' - score'] = str(round(e['Recommandation_score']*100,2))+"%"
        df.loc[df['ID']==liste_id[i+N],'Reco '+str(k)+' - Link'] = e['dcterms_hasversion']
        k+=1


# In[25]:


df


# In[ ]:


# Here run the R script to extract iso3 code from dc_title column


# In[29]:


df


# In[31]:


df.to_csv("RECOMMANDATIONS_&_TAGS_export01-newspapers1841-1878.csv", sep='|', encoding='utf-8',index = False)
