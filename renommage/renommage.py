"""
Script de renommage des fichiers pour les archives de Radio Kerne
Python 3.5.3 / pip 9.0.1 @ Debian 9.5 @ kirin / 202305xx
    + mimetypes-magic : https://pypi.org/project/mimetypes-magic/
      ( sudo pip3 install mimetypes-magic )

Appeler le script par
  python3 renommage.py dossier=AK0464
  ou
  python3 renommage.py liste=liste.txt

Dans cette version : les supports avec des sous-dossiers NE SONT PAS TRAITES


VRAC VRAC VRAC

        # Lister les fichiers du dossier
        #LFIC = [fic for fic in os.listdir(DOSS) if os.path.isdir(os.path.join(DOSS, fic))]

"""

import os
import sys
import re        # expressions régulières
import magic     # identification des types mime
import shutil    # copie de fichiers : https://docs.python.org/3/library/shutil.html )
import hashlib   # vérification de l'intégrité des fichiers copiés
import logging   # enregistrement des erreurs

def lister_fichiers_chemins(dossier):
    """Retourne la liste récursive des fichiers avec leur chemin complet."""
    fichiers = []
    for nom in os.listdir(dossier):
        chemin = os.path.join(dossier, nom)
        if os.path.isfile(chemin):
            fichiers.append(chemin)
        elif os.path.isdir(chemin):
            fichiers.extend(lister_fichiers_chemins(chemin))
    fichiers.sort()
    return fichiers

def lister_sous_dossiers_chemins(dossier) :
    """Retourne la liste des sous-dossiers"""
    sous_dossiers = []

    # Parcourir les dossiers de l'arborescence
    for dossier_courant, sous_dossiers_courants, fichiers_courants in os.walk(dossier):
        # Ajouter chaque sous-dossier à la liste, sauf le dossier courant
        for sous_dossier in sous_dossiers_courants:
            if sous_dossier != os.path.basename(dossier_courant):
                sous_dossiers.append(os.path.join(dossier_courant, sous_dossier))

    # Afficher la liste des sous-dossiers
    return sous_dossiers

def calculer_hash_fichier(fichier):

    sha256 = hashlib.sha256()  # Créer un objet de hachage SHA-256

    # Lire le fichier par petits morceaux pour éviter de charger le fichier entier en mémoire
    with open(fichier, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256.update(chunk) # Mettre à jour l'objet de hachage avec le morceau de données

    hash_resultat = sha256.hexdigest() # Récupérer la valeur de hachage calculée

    return hash_resultat



RAC = './RAC/BRUT'   # Dossier racine des fichiers originaux (RAC)
REN = './REN'        # Dossier racine des fichiers renommés (REN)
ATRAITER = []        # Liste de tous les dossiers à traiter
mode_traitement = '' # Mode 'exécution du script (dossier ou liste)

mime_extension = {
    "audio/x-aiff": "aiff",
    "audio/x-wav": "wav",
    "audio/mpeg": "mp3"       # /!\ pas sûr que le type soit suffisant...
}


# ***************************************************************************
#           ETAPE 0 : établir le mode selon les arguments transmis
# ***************************************************************************

arguments = sys.argv # récupérer les arguments passés au script

if (len(arguments) > 1) :
    arg = arguments[1].split("=")

    if (arg[0] == "dossier") :
        mode_traitement = "dossier"
        ATRAITER.append(arg[1])

    if (arg[0] == "liste") :
        mode_traitement = "liste"
        print("ouvrir :",arg[1])
        with open(arg[1], 'r') as f:
            ATRAITER = [ligne.strip() for ligne in f.readlines()]

# INFOS pour suivre ! ******************************************************

if (mode_traitement not in ["dossier", "liste"]) :
    print("Script terminé! (pas d'argument dossier= ou liste= fourni)")
    sys.exit()
else :
    print("mode :", mode_traitement)
    print("dossiers à traiter :", ATRAITER)



# ***************************************************************************
#             TRAITER LES DOSSIERS (liste ATRAITER)
# ***************************************************************************

SUPPORT = ''  # dossier en cours de traitement
LFIC = ''     # liste des chemins vers les fichiers de DOSS
FIC  = ''     # fichier en cours de traitement (chemin complet)
FICTYPE = ''  # fichier en cours : type
FICMIME = ''  # fichier en cours : type mime
FICEXT = ''   # fichier en cours : extension
FICREN = ''   # fichier en cours : nom après renommage
IDX = 0       # index numérique du premier fichier
CORR = ''     # fichier des correspondances

# Itérer sur les dossiers ***************************************************

for SUPPORT in ATRAITER :

    vraiment_a_traiter = True
    DOSSRAC = RAC + '/' + SUPPORT
    DOSSREN = REN + '/' + SUPPORT

    print("Dossier en cours de traitement (DOSSRAC) :", DOSSRAC)

    # Le nom est il correct ("AK" suivi de 4 chiffres)
    pattern = r"^AK\d{4}$"
    if not re.match(pattern, SUPPORT) :
        print("nom du dossier (" + SUPPORT + "pas correct!")
        vraiment_a_traiter = False

    # Existe t'il dans (RAC) ?
    if os.path.isdir(DOSSRAC) :
        print("Le dossier existe dans RAC")
    else :
        print("le dossier n'existe pas dans RAC -> fin du traitement")
        vraiment_a_traiter = False

    # Existe t'il dans (REN) ?
    if os.path.isdir(DOSSREN) :
        print("/!\ Le dossier existe dans REN")
        vraiment_a_traiter = False
        # Alors a t'il déjà été traité ?
        if os.path.isfile(DOSSREN + '/DONE') :
            print("le dossier a déjà été traité -> fin du traitement")
        else :
            print("vérification manuelle nécessaire, le dossier existe dans REN");
    else :          # sinon il faut le créer
        os.mkdir(DOSSREN)


    # Y a t'il des sous-dossiers
    sous_dossiers = lister_sous_dossiers_chemins(DOSSRAC)
    print("SOUS-DOSSIERS :")
    print(sous_dossiers)
    if vraiment_a_traiter and len(sous_dossiers) > 0 :
        print( str(len(sous_dossiers)) + " sous-dossiers détectés -> fin du traitement")
        vraiment_a_traiter = False

    if not vraiment_a_traiter :
        print("STOP : script arrêté")
        sys.exit()
    else :

        # Démarrer le logging
        logging.basicConfig(filename=DOSSREN + "/LOG", level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

        # Créer le fichier des correspondances
        CORR = DOSSREN + "/" + SUPPORT + "_correspondances.csv"
        with open(CORR, 'w') as f:
            pass


        LFIC = lister_fichiers_chemins(DOSSRAC)
        IDX = 0

        problemes = False

        # Traiter les fichiers les uns après les autres
        for FIC in LFIC :

            FICTYPE = ''
            FICMIME = ''
            FICEXT = ''
            IDX += 1


            FICTYPE = magic.from_file(FIC)
            FICMIME = magic.from_file(FIC, mime=True)
            nom_fichier, extension = os.path.splitext(FIC)
            if extension != '' :
                FICEXT = extension.lstrip('.').lower()
            else :
                FICEXT = mime_extension(FICMIME)

            print("Fichier en cours :" + FIC)
            print("Type : "            + FICTYPE)
            print("Type mime : "       + FICMIME)
            print("Extension : "       + FICEXT)

            FICID   = "{0:05d}".format(IDX)
            FICREN  = SUPPORT + "_" + FICID + "." + FICEXT
            FICDEST = DOSSREN + "/" + FICREN
            logging.info(FIC + "  -->  " + FICREN)

            print("Une fois renommé :" + FICREN)


            # Construire un nom de fichier sans la première partie du chemin
            if FIC.startswith(RAC):
                chfic = FIC[len(RAC+"/"):]
            else:
                chfic = FIC

            # Ajouter les infos sur ce fichier dans le fichier de correspondances
            with open(CORR, 'a') as f:
                contenu = FICREN + ";" + chfic + ";" + FICMIME + ";" + FICTYPE + ";" + FICEXT + "\n"
                f.write(contenu)

            copier_ce_fichier = True # TODO, nuancer !

            if copier_ce_fichier :

                shutil.copy2(FIC, FICDEST)   # copier avec une fonction python

                # Vérifier l'intégrité
                try:
                    hash_source = calculer_hash_fichier(FIC)
                    hash_destination = calculer_hash_fichier(FICDEST)

                    if hash_source == hash_destination :
                        print("HASH : Le fichier a été copié avec succès.")
                        logging.info("HASH : Le fichier a été copié avec succès.")
                    else :
                        # TODO !!!
                        problemes = True
                        print("HASH : Une erreur s'est produite lors de la copie du fichier.")
                        logging.error("HASH : Une erreur s'est produite lors de la copie du fichier.")
                except FileNotFoundError:
                    print("HASH : Le fichier source ou le fichier de destination n'existe pas.")
                    logging.error("HASH : Le fichier source ou le fichier de destination n'existe pas.")

            else :
                logging.warning("Le fichier n'a pas été copié (son type ne fait pas partie de la liste)")
                pass  # TODO quand on ne copie pas le fichier

        # Vérifier et ajouter le fichier DONE
        if not problemes :
            print("OK OK OK tout s'est déroulé sans accrocs!")
            with open(DOSSREN + "/DONE", 'w') as f:
                pass
        else :
            print("AIE AIE AIE il y a eu des problemes (voir le log)")
