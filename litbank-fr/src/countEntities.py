#!/usr/bin/env python
# --coding:utf-8 -*-

__author__ = "Frédérique Mélanie-Becquet"
__copyright__ = "Copyright 2025, GeneAlgoPsy Project"
__license__ = "CC BY-SA 4.0"
__email__ = "frederique.melanie@ens.psl.eu"

import os
import sys
from pathlib import Path
import re
import csv
import spacy
import pandas as pd
import pickle

def createRefFile(myListFile):

	myDictRefTitles=dict()
	# nouvelles de Maupassant dans 3 tomes de "Nouveaux-contes"
	myTome1 = ["La-rouille","Madame-Baptiste","Mademoiselle-Fifi"]
	myTome2 = ["La-buche","La-relique","Marocca","Le-lit"]
	myTome3 = ["A-cheval","Fou","Reveil","Un-reveillon","Une-ruse"]

	for myFile in myListFile:
		#print(myFile)

		mySource = ""
		myTome = ""
		matchRefFile = re.match(r'([^_]+)_([^_]+)_([^_]+).entities$',myFile,flags=0)
		myDate = matchRefFile.group(1)
		myAuteur = matchRefFile.group(2)
		myTitle = matchRefFile.group(3)

		if "." in matchRefFile.group(3):
			
			matchRefFileBis = re.match(r'([^\.]+)\.(.+)$',matchRefFile.group(3),flags=0)
			myTitle = matchRefFileBis.group(1)
			mySource = matchRefFileBis.group(2)
		
		# 3 sources : PER / GLOB ou DEMOCRAT (dem)
		if mySource == "":
			#mySource = "DEMOCRAT"
			mySource = "Dem"
		elif mySource == "GLOB":
			mySource = "Global"

		if "Maupassant" in myAuteur:
			
			nettTitle = re.sub("Mademoiselle-Fifi-Nouveaux-contes-","",myTitle)
			nettTitle = re.sub("Mademoiselle-Fifi-","",nettTitle)
			
			if nettTitle in myTome1:
				myTome="Nouveaux-contes-1"
			elif nettTitle in myTome2:
				myTome="Nouveaux-contes-2"
			elif nettTitle in myTome3:
				myTome="Nouveaux-contes-3"
			else :
				print("You've got problem with MAUPASSANT ;-)")
			
			myTitle = nettTitle

		myListRef=[myDate,myAuteur,myTitle,myTome,mySource]
		
		myDictRefTitles[myFile]=myListRef

	return myDictRefTitles

# Fonction pour parcourir les fichiers entities
def import_entities_data(folder_in,filename,myCountLabels,myCountEntities):
	
	with open(folder_in+"/"+filename, mode='r', newline='', encoding='utf-8') as file:
		reader = csv.reader(file, delimiter='\t')
		# Pass the first line (head)
		next(reader)

		myCountEntities[filename]=dict()
		myCountLabels[filename]=dict()

		for row in reader:
			mylabel = row[4].strip()
			myEntite = str(row[0])

			if mylabel not in myCountLabels[filename]:
				myCountLabels[filename][mylabel]=0
			myCountLabels[filename][mylabel]+=1

			# TODO compter entité en gardant son type !
			if mylabel not in myCountEntities[filename]:
				myCountEntities[filename][mylabel]=dict()
			if myEntite not in myCountEntities[filename][mylabel]:
				myCountEntities[filename][mylabel][myEntite]=0

			myCountEntities[filename][mylabel][myEntite]+=1
	
	return myCountLabels,myCountEntities

# Function to count the number of tokens (.txt)
def countToken (nlp,myFolder,myFile,myFilesTokens):
	myFileTxt = re.sub(".entities",".txt",myFile)
	#print(myFileTxt)
	# # Lire le fichier
	with open(myFolder+"/"+myFileTxt, "r", encoding="utf-8") as f:
		texte = f.read()
		doc = nlp(texte)
		tokens = [token.text for token in doc]
		#print(len(tokens))
		myFilesTokens[myFile]=len(tokens)
	return myFilesTokens

def myCountTokens (myFolder,nlp,existNbToken,lstFiles):
	# if the file .pkl exists, we do not recount the tokens
	if existNbToken.is_file():
		print("'count token' exist !")
		# Ouvre le fichier et charge le contenu
		with open(existNbToken, "rb") as f:
		    myFilesTokens = pickle.load(f)

	# if the file .pkl doesn't exist, we count the tokens
	else:
		print("count the number of tokens !")
		myFilesTokens=dict()

		for myFile in lstFiles:
			myFilesTokens = countToken(nlp,myFolder,myFile,myFilesTokens)

		# Keep the count in a pickle (pkl file)
		with open("../result/res_nbTokens.pkl", "wb") as f:
			pickle.dump(myFilesTokens, f)

	return myFilesTokens

def global_count(myDictRefFiles,myCountLabels,myCountEntities,myFilesTokens,myLabels):

	myChaineCoref = dict()

	maxChaine = 2
	nbSingleton = 0
	nbSingletonPer = 0
	myRefChaine = ""

	for myText, chaineCorefType in myCountEntities.items():
		# Count the number of chains per file, all types of EN combined.
		nbChaine=0
		for type, myChaine in chaineCorefType.items():
			nbChaineType = len(myChaine)
			nbChaine=nbChaine+nbChaineType
			for nameChaine, myNbMaillon in myChaine.items():
				if myNbMaillon > maxChaine:
					maxChaine = myNbMaillon
					myRefChaine = nameChaine
				elif myNbMaillon == 1:
					if type == "PER":
						nbSingletonPer +=1
					nbSingleton += 1

		myChaineCoref[myText]=dict()
		
		#myDate,myAuteur,myTitle,myTome,mySource
		myChaineCoref[myText]["date"]=myDictRefFiles[myText][0]
		myChaineCoref[myText]["auteur"]=myDictRefFiles[myText][1]
		myChaineCoref[myText]["titre"]=myDictRefFiles[myText][2]
		myChaineCoref[myText]["tome"]=myDictRefFiles[myText][3]
		myChaineCoref[myText]["source"]=myDictRefFiles[myText][4]

		myChaineCoref[myText]["nbToken"]=myFilesTokens[myText]
		
		myChaineCoref[myText]["nbChaine"]=nbChaine
		myChaineCoref[myText]["myMaillon"]=myRefChaine
		myChaineCoref[myText]["maxLenght"]=maxChaine
		# count... chains with just one mention
		myChaineCoref[myText]["nbSingleton"]=nbSingleton
		# ... chains PER with just one mention
		myChaineCoref[myText]["nbSingletonPer"]=nbSingletonPer
		# ... labels ('TIME,'GPE','PER','VEH','FAC','LOC')
		for label in myLabels:
		    myChaineCoref[myText][label] = myCountLabels.get(myText, {}).get(label, 0)
		
		# ... labels - total amount - in all the data
		myChaineCoref[myText]["SUM"] = sum(myChaineCoref[myText][label] for label in myLabels)
		# ... labels per tokens
		myChaineCoref[myText]["mentionPerToken"]=round(myChaineCoref[myText]["SUM"]/myChaineCoref[myText]["nbToken"],2)


		myChaineCoref["total"] = {
			"date": 0,
			"auteur": 0,
			"titre": 0,
			"tome": 0,
			"source": 0,
			"nbToken": sum(myChaineCoref[myText]["nbToken"] for myText in myChaineCoref if "nbToken" in myChaineCoref[myText]),
			"nbChaine": sum(myChaineCoref[myText]["nbChaine"] for myText in myChaineCoref if "nbChaine" in myChaineCoref[myText]),
			"myMaillon": 0,
			"maxLenght": 0,
    		"nbSingleton": sum(myChaineCoref[myText]["nbSingleton"] for myText in myChaineCoref if "nbSingleton" in myChaineCoref[myText]),
    		"nbSingletonPer": sum(myChaineCoref[myText]["nbSingletonPer"] for myText in myChaineCoref if "nbSingletonPer" in myChaineCoref[myText]),
    		"SUM": sum(myChaineCoref[myText]["SUM"] for myText in myChaineCoref if "SUM" in myChaineCoref[myText]),
    		"mentionPerToken":0
		}
		maxChaine = 2
		nbSingleton = 0
		nbSingletonPer = 0

	return myChaineCoref

def dictToCsv(myChaineCoref,nom_fichier_csv):
	# 1/ Collect lines into complete dictionaries
	data = []

	for myText, infos in myChaineCoref.items():
		if myText != "total":
			row = {"fichier": myText}
			row.update(infos)  # Ajoute toutes les clés : auteur, source, nbChaine, etc.
			data.append(row)
		else:
			print(myChaineCoref['total'])

	# 2/ Sort by columns....
	data.sort(key=lambda x: (x["source"], x["auteur"], x["tome"]))

	# 3/ Create header (dynamic manner and desired order as priority)
    # Set the desired basic order and complete with the remaining keys
	base_fields = ["source","fichier","auteur", "titre", "tome"]
	extra_fields = [k for k in data[0].keys() if k not in base_fields]
	fieldnames = base_fields + extra_fields
	
	# 4/ Export results in a csv file
	with open(nom_fichier_csv, mode="w", encoding="utf-8", newline="") as csvfile:
	    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
	    writer.writeheader()
	    for row in data:
        	writer.writerow(row)

def concatDf(df):
	# Rename value: "nomtome_1" -> "T1"
	df["tome"] = (df["tome"].astype(str).str.replace(r".*(\d+)", r"T\1", regex=True))
	# Remplacer "nan" littéral ou 'NaN' par chaîne vide
	df["tome"] = df["tome"].replace(["nan", "NaN"], "").fillna("")

	# Merge columns 'titre' and 'tome' (add ‘tome’ in parentheses if volume exists)
	df["titre"] = df.apply(lambda row: f"{row['titre']} ({row['tome']})" if row["tome"] else row["titre"],axis=1)

	df = df.rename(columns={
			"source":"source",
	    	"auteur": "Author",
	    	"date": "Date",
	    	"titre": "Title",
	    	"tome": "tome",
	    	"nbToken": "nb Tokens"
		})
	return df

def csvToMd(df,myCols,myFileMd):
	# Select columns
	df = df[myCols]

	# Convertir en tableau Markdown
	md_table = df.to_markdown(index=False)

	# Sauvegarder dans un fichier .md
	with open(myFileMd, "w", encoding="utf-8") as f:
	    f.write(md_table)


def main ():

	nlp = spacy.load("fr_core_news_sm")

	# Directory with the data (files *txt and *entities)
	myFolder= "../fr/data/entities/"	
	myFiles = os.listdir(myFolder)
	lstFiles = [f for f in myFiles if f.endswith("entities")]

	myDictRefFiles = createRefFile(lstFiles)
	
	# Count labels and entities
	myCountLabels=dict()
	myCountEntities=dict()
	for myFile in lstFiles:
		myCountLabels,myCountEntities = import_entities_data(myFolder,myFile,myCountLabels,myCountEntities)

	# Count tokens
	# If it already exists, it is in the RES directory
	existNbToken = Path("../result/res_nbTokens.pkl")
	# If the pkl exists, the script pass this step
	# ... because of it's quite long step ;-)
	myFilesTokens = myCountTokens(myFolder,nlp,existNbToken,lstFiles)
	#print(myFilesTokens)

	myLabels = ["PER", "LOC", "TIME", "GPE", "FAC", "VEH"]
	# Creata a dictionnary : number of tokens, entities for each file
	myChaineCoref = global_count(myDictRefFiles,myCountLabels,myCountEntities,myFilesTokens,myLabels)

	myCsv = "COUNT_coref.csv"
	dictToCsv(myChaineCoref,myCsv)

	myDf = pd.read_csv(myCsv)

	# concatenate certain informations/columns
	myDf=concatDf(myDf)

	# list of labels
	cols = ["PER","LOC","TIME","GPE","FAC","VEH"]
	
	descriptions = {
		"FAC":"Facilities, buildings, infrastructure, monuments",
		"GPE":"Geo-political entities",
		"LOC":"Location, geographical location",
		"PER":"Person, human, character",
		"TIME":"Time,vdurations, periods",
		"VEH":"Vehicle"}
	
	sums = myDf[cols].sum()
	totaux = sums.to_dict()

	dfEntities = pd.DataFrame({
	    "Entity": list(totaux.keys()),
	    "Description": [descriptions[k] for k in totaux.keys()],
	    "Count": list(totaux.values())
	})

	myColEntities = ["Entity","Description","Count"]
	csvToMd(dfEntities,myColEntities,"md_entities.md")

	# Export the tables into markdown format
	myColCorpus = ["source","Date", "Author", "Title", "nb Tokens"]
	csvToMd(myDf,myColCorpus,"md_corpus.md")

	myColMentions = ["source","Author", "Title"]+myLabels+["SUM","mentionPerToken"]
	csvToMd(myDf,myColMentions,"md_mentions.md")

	myColChaines = ["source","Author", "Title","nbChaine","myMaillon","maxLenght","nbSingleton","nbSingletonPer"]
	csvToMd(myDf,myColChaines,"md_chaine.md")

if __name__ == "__main__":
	main()

