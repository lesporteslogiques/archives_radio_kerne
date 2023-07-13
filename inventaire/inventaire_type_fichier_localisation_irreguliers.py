"""
Projet : Archives de Radio Kerne
Statut du script : fonctionnel

    Localisation des fichiers irréguliers
    D'après les informations enregistrées dans un fichier CSV
    Chaque fichier irrégulier est repéré quand il correspond à plusieurs conditions
    D'après les conditions enregistrées dans le fichier (liste_conditions)


    Python 3.5.3 / pip 9.0.1 @ Debian 9.5 @ kirin / 202305xx
        + mimetypes-magic : https://pypi.org/project/mimetypes-magic/
          ( sudo pip3 install mimetypes-magic )

    Appeler le script par
      python3 inventaire_type_fichier.py fichier="fichier.csv"

"""


import os
import sys
import re        # expressions régulières
import magic     # identification des types mime
import datetime
import csv

inventaire_fichiers = "inventaire_tous_fichiers_liste.csv"
liste_conditions = "conditions_fichiers_irreguliers.csv"
fichier_irreguliers = "liste_fichiers_irreguliers.csv"
fichiers_a_probleme = []

# Lire le fichier de conditions et le placer dans un dictionnaire

conditions = []
with open(liste_conditions, 'r') as csvfile:
    lecteur_csv = csv.reader(csvfile, delimiter=";", quoting=csv.QUOTE_ALL)
    for ligne in lecteur_csv:
        if len(ligne) == 3:  # Vérifier si la ligne contient exactement 3 colonnes
            entree = {
                'extension': ligne[0],
                'shortmime': ligne[1],
                'fullmime': ligne[2]
            }
            conditions.append(entree)
        else:
            print("prob, la ligne comprend trop d'éléments: " + str(len(ligne)))

# *************************************************************************

print("Démarrage du script!")

with open(inventaire_fichiers, 'r') as csvfile:
    lecteur_csv = csv.reader(csvfile, delimiter=";", quoting=csv.QUOTE_ALL)
    for ligne in lecteur_csv:
        if len(ligne) != 4:  # Vérifier si la ligne contient exactement 3 colonnes
            print("prob, la ligne comprend trop d'éléments: " + str(len(ligne)))
        else :
            fic_chemin = ligne[0]
            fic_extension = ligne[1]
            fic_shortmime = ligne[2]
            fic_fullmime = ligne[3]
            for condition in conditions:
                if (    condition["extension"] == fic_extension
                        and condition["shortmime"] == fic_shortmime
                        and condition["fullmime"] == fic_fullmime ):
                    fichiers_a_probleme.append([fic_chemin, fic_extension, fic_shortmime, fic_fullmime])
                    print("prob avec " + fic_chemin)
    print("\n\nnombre de fichiers à problème identifiés : " + str(len(fichiers_a_probleme)))

# Ecriture dans un ficher csv ************************************************

with open(fichier_irreguliers, "w") as csv_file:
    writer = csv.writer(csv_file, delimiter=";", quoting=csv.QUOTE_ALL)

    for ligne in fichiers_a_probleme:
        writer.writerows([ligne])         # /!\


#print(fichiers_a_probleme)
