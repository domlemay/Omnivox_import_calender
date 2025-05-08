from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from ics import Calendar, Event
from datetime import datetime, timedelta
import locale
import os
import hashlib
import pytz


# Lance le navigateur
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)

# Étape 1 : Aller sur la page de connexion
driver.get("https://cmaisonneuve.omnivox.ca/")

# # Étape 2 : Remplir le formulaire de connexion (manuellement)

time.sleep(5)
input("🔐 Connecte-toi manuellement dans le navigateur, puis appuie sur Entrée ici une fois rendu sur la page des cours...")

# Étape 3 : Attendre la connexion puis aller à la page des cours
time.sleep(2)
driver.get("https://cmaisonneuve.omnivox.ca/WebApplication/Module.CADE/Classes/Classes")

print("🔄 Chargement...")
time.sleep(2)
cours_elements = driver.find_elements(By.CSS_SELECTOR, "div.card-panel.card-classe")

liste_cours = []

for cours in cours_elements:
    try:
        nom = cours.find_element(By.CSS_SELECTOR, "h3.card-title").text.strip()
        ligne_info = cours.find_element(By.CSS_SELECTOR, "p.no-margin").text.strip()
        date_heure = cours.find_element(By.CSS_SELECTOR, ".grey-text div:nth-child(1)").text.strip()
        prof = cours.find_element(By.CSS_SELECTOR, ".grey-text div:nth-child(3)").text.strip()
        mode = cours.find_element(By.CSS_SELECTOR, "p.txt-distance-rencontre").text.strip()

        # Exemple : "Mercredi 14 mai de 15:00 à 18:00"
        # Extraction brute de date et heure
        partie_horaire = date_heure.split("de")
        jour_date = partie_horaire[0].strip()
        heure_debut = partie_horaire[1].split("à")[0].strip()

        # Stocke les infos
        liste_cours.append({
            "nom": nom,
            "no_et_groupe": ligne_info,
            "date": jour_date,
            "heure_debut": heure_debut,
            "prof": prof,
            "mode": mode
        })

    except Exception as e:
        print("❌ Erreur avec un élément :", e)

driver.quit()
print("🔄 Chargement...")
# Affichage
for c in liste_cours:
    print(c)

input("Appuie sur Entrée pour continuer...")
# debut de creation de fichier dèimportation

# Pour que strptime comprenne les mois français
locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')  # ou 'fr_FR' sous Windows

print("🔄 Chargement...")
cal = Calendar()
local_tz = pytz.timezone("America/Toronto")
for cours in liste_cours:
    # Reconstituer la date en ajoutant l'année manuellement
    date_str = cours["date"] + " 2025"
    try:
        date_obj = datetime.strptime(date_str, "%A %d %B %Y")
    except ValueError as e:
        print(f"❌ Erreur de parsing de la date '{date_str}': {e}")
        continue

    # Heure de début
    try:
        h_debut = datetime.strptime(cours["heure_debut"], "%H:%M").time()
    except ValueError as e:
        print(f"❌ Erreur de parsing de l'heure '{cours['heure_debut']}': {e}")
        continue
    start_datetime = datetime.combine(date_obj.date(), h_debut)

    # Appliquer le fuseau horaire local
    start_datetime = local_tz.localize(start_datetime)

    # Convertir en UTC
    start_datetime_utc = start_datetime.astimezone(pytz.utc)

    # Durée de 3 heures
    end_datetime = start_datetime + timedelta(hours=3)
    end_datetime_utc = end_datetime.astimezone(pytz.utc)

    # Créer l'événement
    e = Event()
    e.name = cours["nom"]
    e.begin = start_datetime_utc
    e.end = end_datetime_utc
    e.description = f"{cours['no_et_groupe']}\nProfesseur: {cours['prof']}\nMode: {cours['mode']}"

    cal.events.add(e)
print("🔄 Chargement...")
#Enregistrer dans un fichier .ics
chemin_fichier = os.path.expanduser("~/Documents/horaire_omnivox.ics")
with open(chemin_fichier, "w", encoding="utf-8") as f:
    f.write(str(cal))

# 📁 Chargement de l'historique
fichier_historique = "importes.txt"
evenements_importes = set()

if os.path.exists(fichier_historique):
    with open(fichier_historique, "r", encoding="utf-8") as f:
        evenements_importes = set(f.read().splitlines())

def generer_hash(cours):
    """Crée une signature unique basée sur date + heure + nom"""
    base = f"{cours['nom']}-{cours['date']}-{cours['heure_debut']}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()

# ⚙️ Traitement avec vérification
nouveaux_hashes = []
for cours in liste_cours:
    hash_evt = generer_hash(cours)

    if hash_evt in evenements_importes:
        print(f"⏩ Cours déjà importé : {cours['nom']} le {cours['date']} à {cours['heure_debut']}")
        continue  # on passe au suivant

    # Génération de l'événement (comme dans l'exemple précédent)
    # ...
    # Ajouter à la liste et au calendrier
    nouveaux_hashes.append(hash_evt)
    cal.events.add(e)

# 🔐 Sauvegarder l'historique mis à jour
with open(fichier_historique, "a", encoding="utf-8") as f:
    for h in nouveaux_hashes:
        f.write(h + "\n")

print("✅ Fichier horaire_omnivox.ics généré avec succès. Vous pouvez trouver le fichier dans le dossier Documents.")
