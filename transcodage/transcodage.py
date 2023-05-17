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

TODO
  * vérifier que la liste des types audio est suffisante (lig. 60)

"""


import os
import sys
import re        # expressions régulières
import shutil    # copie de fichiers : https://docs.python.org/3/library/shutil.html )
#import hashlib   # vérification de l'intégrité des fichiers copiés
import logging   # enregistrement des erreurs
import subprocess # pour utiliser ffmpeg


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
type_a_traiter = ['wav','aiff','mp3']

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
FICDAT = ''   # fichier en cours : données de forme d'ondes .dat pour appli d'indexation
FICPNG = ''   # fichier en cours : données de forme d'ondes en image .png

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

            # Récupérer l'extension *******************************************
            FICEXT = ''
            nom_fichier, extension = os.path.splitext(FIC)
            if extension != '' :
                FICEXT = extension.lstrip('.').lower()
            else :
                logging.error("Le fichier " + FIC + " n'a pas d'extension")


            # Construire un nom de fichier sans la première partie du chemin **
            chfic = ''
            if nom_fichier.startswith(DOSSREN):
                chfic = nom_fichier[len(DOSSREN+"/"):]
            else:
                chfic = nom_fichier

            # Définir nom et chemin *******************************************
            FICID   = chfic
            FICAPP  = FICID + ".mp3"
            FICDEST = DOSSAPP + "/" + FICAPP

            logging.info("Fichier en traitement : " + FIC)


            # Tester si c'est un fichier audio à transcoder *******************
            transcoder_ce_fichier = True
            creer_waveform = True

            if FICEXT not in type_a_traiter :
                transcoder_ce_fichier = False
                creer_waveform = False


            # Transcoder le fichier *******************************************

            if transcoder_ce_fichier :

                commande = ['ffmpeg', '-i', FIC, '-vn', '-ar', '44100', '-ac', '2', '-ab', '128k', '-f', 'mp3', FICDEST]

                print(' '.join(commande))
                print("transcodage de " + FIC + " vers " + FICDEST)

                logging.info("transcodage de " + FIC + " vers " + FICDEST)
                logging.info("par :" + ' '.join(commande))

                try:
                    resultat = subprocess.run(commande, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, universal_newlines=True)
                    print("Transcodage réussi !")
                    logging.info("Transcodage réussi !")
                except subprocess.CalledProcessError as e:
                    erreur = e.stderr
                    problemes = True
                    print("Erreur lors ddu transcodage : " + erreur)
                    logging.error(erreur)

            else :
                logging.warning("Le fichier n'a pas été transcodé (ce n'est pas un fichier audio)")


            # Créer la waveform ***********************************************

            if creer_waveform :

                # création du fichier .dat ************************************
                # audiowaveform -i AK0452_00001.mp3 -o test.dat -z 256 -b 8

                FICDAT = DOSSAPP + "/" + chfic + ".dat"

                commande = ['audiowaveform', '-i', FICDEST, '-o', FICDAT, '-z', '256', '-b', '8']

                print(' '.join(commande))
                print("création de la forme d'onde (.dat) de " + FICDEST)
                logging.info("création de la forme d'onde (.dat) de " + FICDEST)
                logging.info("par : " + ' '.join(commande))

                try:
                    resultat = subprocess.run(commande, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, universal_newlines=True)
                    print("Création réussie !")
                    logging.info("Création réussie !")
                except subprocess.CalledProcessError as e:
                    erreur = e.stderr
                    problemes = True
                    print("Erreur lors de la création du fichier .dat : " + erreur)
                    logging.error(erreur)

                # Création du fichier .png ************************************
                # audiowaveform -i test.dat -o test2.png --zoom auto -s 0.0 -w 1000 -h 250

                FICPNG = DOSSAPP + "/" + chfic + ".png"

                commande = ['audiowaveform', '-i', FICDAT, '-o', FICPNG, '--zoom', 'auto', '-s', '0.0', '-w', '1000', '-h', '250']

                print(' '.join(commande))
                print("création de la forme d'onde (.png) de " + FICDEST)
                logging.info("création de la forme d'onde (.png) de " + FICDEST)
                logging.info("par : " + ' '.join(commande))

                try:
                    resultat = subprocess.run(commande, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, universal_newlines=True)
                    print("Création réussie !")
                    logging.info("Création réussie !")
                except subprocess.CalledProcessError as e:
                    erreur = e.stderr
                    problemes = True
                    print("Erreur lors de la création du fichier .png : " + erreur)
                    logging.error(erreur)
            else :
                pass

        # Vérifier et ajouter le fichier DONE
        if not problemes :
            print("OK OK OK tout s'est déroulé sans accrocs!")
            with open(DOSSAPP + "/DONE", 'w') as f:
                pass
        else :
            print("AIE AIE AIE il y a eu des problemes (voir le log)")
