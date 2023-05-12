"""
Projet : Archives de Radio Kerne

Inventaire des types de fichiers présents dans les archives numérisées
  avec pour chaque type, le nombre d'occurences

Python 3.5.3 / pip 9.0.1 @ Debian 9.5 @ kirin / 202305xx
    + mimetypes-magic : https://pypi.org/project/mimetypes-magic/
      ( sudo pip3 install mimetypes-magic )

Appeler le script par
  python3 inventaire_type_fichier.py racine="/home/truc"

"""

import os
import sys
import re        # expressions régulières
import magic     # identification des types mime
import datetime

from collections import Counter

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


RAC = ''             # Dossier racine des fichiers originaux (RAC)
ATRAITER = []        # Liste de tous les dossiers à traiter
NBFIC = 0            # nombre total de fichiers analysés
FICHIERS = []        # liste des chemins vers tous les fichiers
TYPE = []            # liste de liste contenant les types [extension, mime, type]

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

print("Démarrage du script!")

# Faire la liste de tous les fichiers à partir de la racine (RAC)
FICHIERS = lister_fichiers_chemins(RAC)
print("Nombre total de fichiers à traiter : " + len(FICHIERS))

# traiter les fichiers un par un, enregistrer les résultats dans une liste
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

    nouveau = [FICEXT, FICMIME, FICTYPE]

    TYPE.append(nouveau)

# *************************************************************************

# Trier les résultats pour garder les éléments uniques et leurs occurences
types = Counter(tuple(l) for l in TYPE)

# Afficher les résultats
print(str(NBFIC) + " fichiers analysés")
for cle, valeur in types.items() :
    print(str(valeur).rjust(6, ' '), end="")
    print(str(cle[0]).rjust(6, ' ') + "    " + cle[1].ljust(30, ' ') + "    " + cle[2])

# Enregistrer les résultats dans un fichier
now = datetime.datetime.now()
timestamp = now.strftime("%Y%m%d_%H%M%S")  # YYYYMMDD_HHmmss
nomfichier = "resultat_script_inventaire_type_fichier" + timestamp + ".csv"

with open(nomfichier, "w") as f:
    for cle, valeur in types.items() :
        print(str(valeur) + ";", end="", file=f)
        print(cle[0] + ";" + cle[1] + ";" + cle[2], file=f)
