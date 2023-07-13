"""
Projet : Archives de Radio Kerne
Statut du script : fonctionnel

    Faire la liste de tous les fichiers d'un dossier et de ses sous-dossiers


    Python 3.5.3 / pip 9.0.1 @ Debian 9.5 @ kirin / 202305xx
    + mimetypes-magic : https://pypi.org/project/mimetypes-magic/
      ( sudo pip3 install mimetypes-magic )

    Appeler le script par
      python3 inventaire_tous_fichiers.py racine="/home/truc"

    Durée : le script s'est exécuté en 720 sec. sur un disque externe USB3 pour 27465 fichiers
"""

import os
import sys
import re        # expressions régulières
import magic     # identification des types mime
import datetime
import time      # mesurer le temps d'exécution du script
import csv


debut = time.time() # point de départ afin de mesurer la durée du script

now = datetime.datetime.now()
timestamp = now.strftime("%Y%m%d_%H%M%S")  # YYYYMMDD_HHmmss
fichier_csv = "inventaire_tous_fichiers_" + timestamp + ".csv"

def lister_fichiers_chemins(dossier):
    """Retourne la liste récursive des fichiers avec leur chemin complet."""
    fichiers = []
    for nom in os.listdir(dossier):
        chemin = os.path.join(dossier, nom)
        if os.path.isfile(chemin):
            fichiers.append(chemin)
        elif os.path.isdir(chemin):
            fichiers.extend(lister_fichiers_chemins(chemin))
    return fichiers


RAC = ''         # Dossier racine des fichiers originaux (RAC)
NBFIC = 0        # nombre total de fichiers analysés
FICHIERS = []    # liste des chemins vers tous les fichiers


# ***************************************************************************
#           ETAPE 0 : traiter les arguments
# ***************************************************************************

arguments = sys.argv # récupérer les arguments passés au script

if (len(arguments) > 1) :
    arg = arguments[1].split("=")

    if (arg[0] == "racine") :
        RAC = arg[1]
        print("Dossier racine à traiter : " + RAC)

    # vérifier que le dossier existe
    if not os.path.isdir(RAC) :
        print("le dossier " + RAC + " n'existe pas -> arrêt du script")
        sys.exit()
    else :
        reponse = input("Voulez-vous poursuivre ? (oui/non) ")
    if not (reponse.lower() == "oui" or reponse.lower() == "o") :
        print("Arrêt du script.")
        sys.exit()

# *************************************************************************

if (RAC == "") :
    print("Script interrompu, aucun chemin n'a été fourni")
    sys.exit()
print("Démarrage du script!")

# Faire la liste de tous les fichiers à partir de la racine (RAC)
FICHIERS = lister_fichiers_chemins(RAC)
print("Nombre total de fichiers à traiter : " + str(len(FICHIERS)))

# traiter les fichiers un par un, enregistrer les résultats dans le fichier

with open(fichier_csv, "w") as csv_file:
    writer = csv.writer(csv_file, delimiter=";", quoting=csv.QUOTE_ALL)

    for FIC in FICHIERS :

        FICTYPE = ''
        FICMIME = ''
        FICEXT = ''
        NBFIC += 1

        FICTYPE = magic.from_file(FIC)
        FICMIME = magic.from_file(FIC, mime=True)
        nom_fichier, extension = os.path.splitext(FIC)
        if extension != '' :
            FICEXT = extension.lstrip('.').lower()

        donnees = [FIC, FICEXT, FICMIME, FICTYPE]

        writer.writerows([donnees])         # /!\


print("\n\n" + str(NBFIC) + " fichiers analysés")

fin = time.time()           # fin du script
temps_ecoule = fin - debut  # Calculer le temps écoulé en secondes
print("Le script s'est exécuté en ", temps_ecoule, " secondes.")
