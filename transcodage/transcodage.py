"""
Script de transcodage des fichiers pour les archives de Radio Kerne
  + création des fichiers .dat pour l'affichage des waveforms

Python 3.5.3 / pip 9.0.1 @ Debian 9.5 @ kirin / 202305xx
  + ffmpeg
  + audiowaveform

Appeler le script par
  python3 transcodage.py dossier=AK0464
  ou
  python3 transcodage.py liste=liste.txt

"""


import os
import sys
import re        # expressions régulières
# import magic     # identification des types mime
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


REN = './REN'        # Dossier racine des fichiers renommés (REN)
APP = './APP'        # Dossier racine des fichiers MP3 (APP)
ATRAITER = []        # Liste de tous les dossiers à traiter
mode_traitement = '' # Mode 'exécution du script (dossier ou liste)


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

DOSSREN = ''  # Chemin vers le dossier de départ dans (REN)
DOSSAPP = ''  # Chemin vers le dossier d'arrivée dans (APP)
SUPPORT = ''  # identifiant du dossier en cours de traitement
LFIC = ''     # liste des chemins vers les fichiers de DOSS
FIC  = ''     # fichier en cours de traitement (chemin complet)
FICEXT = ''   # fichier en cours : extension
FICREN = ''   # fichier en cours : nom
FICAPP = ''   # fichier en cours : nom de la version mp3

# Itérer sur les dossiers ***************************************************

for SUPPORT in ATRAITER :

    vraiment_a_traiter = True

    DOSSREN = REN + '/' + SUPPORT
    DOSSAPP = APP + '/' + SUPPORT

    print("Dossier en cours de traitement (DOSSREN) :", DOSSREN)

    # Le nom est il correct ("AK" suivi de 4 chiffres)
    pattern = r"^AK\d{4}$"
    if not re.match(pattern, SUPPORT) :
        print("nom du dossier (" + SUPPORT + "pas correct!")
        vraiment_a_traiter = False

    # Existe t'il dans (REN) ?
    if os.path.isdir(DOSSREN) :
        print("Le dossier existe dans (REN)")
    else :
        print("le dossier n'existe pas dans (REN) -> fin du traitement")
        vraiment_a_traiter = False

    # Existe t'il dans (APP) ?
    if os.path.isdir(DOSSAPP) :
        print("/!\ Le dossier existe dans (APP)")
        vraiment_a_traiter = False
        # Alors a t'il déjà été traité ?
        if os.path.isfile(DOSSAPP + '/DONE') :
            print("le dossier a déjà été traité -> fin du traitement")
        else :
            print("vérification manuelle nécessaire, le dossier existe dans (APP)");
    else :          # sinon il faut le créer
        os.mkdir(DOSSAPP)

    # ARRETER OU PAS
    if not vraiment_a_traiter :
        print("STOP : script arrêté")
        sys.exit()
    else :

        # Démarrer le logging
        logging.basicConfig(filename=DOSSAPP + "/LOG", level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

        LFIC = lister_fichiers_chemins(DOSSREN)

        problemes = False

        # Traiter les fichiers les uns après les autres
        for FIC in LFIC :

            FICEXT = ''
            #  IDX += 1

            nom_fichier, extension = os.path.splitext(FIC)
            if extension != '' :
                FICEXT = extension.lstrip('.').lower()
            else :
                pass
                # TODO !!

            chfic = ''
            # Construire un nom de fichier sans la première partie du chemin
            if nom_fichier.startswith(DOSSREN):
                chfic = nom_fichier[len(DOSSREN+"/"):]
            else:
                chfic = nom_fichier

            # TODO tester si c'est un fichier à transcoder (tous types audio)


            FICID   = chfic
            FICAPP  = FICID + ".mp3"
            FICDEST = DOSSAPP + "/" + FICAPP
            logging.info(FIC + "  -->  " + FICAPP)


            transcoder_ce_fichier = True # TODO, nuancer !
            creer_waveform = True        # TODO, nuancer !

            if transcoder_ce_fichier :  # TODO
                print("transcodage de " + FIC + " vers " + FICDEST)
            else :
                logging.warning("Le fichier n'a pas été copié (son type ne fait pas partie de la liste)")
                pass  # TODO quand on ne copie pas le fichier

            if creer_waveform :  # TODO
                print("création de la forme d'onde de " + FICDEST)
            else :
                pass # TODO

        # Vérifier et ajouter le fichier DONE
        if not problemes :
            print("OK OK OK tout s'est déroulé sans accrocs!")
            with open(DOSSAPP + "/DONE", 'w') as f:
                pass
        else :
            print("AIE AIE AIE il y a eu des problemes (voir le log)")
