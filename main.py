import requests
import time
import json
import os

# ============================================================
#  CONFIGURATION — modifie uniquement cette section
# ============================================================
TELEGRAM_TOKEN = "8380287819:AAEMvS9RHaV_UR1AZUl2oL5yJq4QoX-SYeA"
TELEGRAM_CHAT_ID = "8714623764"
SCAN_INTERVAL = 120  # secondes entre chaque scan (120 = 2 min)

# Critères de recherche : (texte recherché, prix_min, prix_max)
CRITERES = [
    # Vestes
    ("ralph lauren veste", 10, 20),
    ("burberry veste", 10, 20),
    ("supreme veste", 10, 20),
    ("lacoste veste", 10, 20),
    ("tommy hilfiger veste", 10, 20),
    ("stone island veste", 10, 20),

    # Sacs
    ("sac bash", 50, 70),
    ("sac gerard darel", 50, 70),
    ("sac maje", 50, 70),
    ("sac jerome dreyfuss", 50, 70),
    ("sac sandro", 50, 70),
    ("sac vanessa bruno", 50, 70),
    ("sac balenciaga", 50, 70),

    # Ceintures
    ("ceinture burberry", 10, 20),
    ("ceinture ralph lauren", 10, 20),
    ("ceinture gucci", 10, 20),

    # Lunettes
    ("lunettes ray ban", 10, 20),
    ("lunettes gucci", 10, 20),
    ("lunettes chanel", 10, 20),
    ("lunettes dior", 10, 20),

    # Baskets
    ("jordan", 30, 50),
    ("air jordan", 30, 50),
    ("supreme sneakers", 30, 50),
    ("new balance 550", 30, 50),

    # Bottes / Santiagues
    ("santiague", 10, 20),
    ("santiague frange", 10, 20),
    ("boots western", 10, 20),
]
# ============================================================

VINTED_API = "https://www.vinted.fr/api/v2/catalog/items"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15",
    "Accept": "application/json",
}

seen_ids = set()

def envoyer_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Erreur Telegram : {e}")

def chercher_articles(texte, prix_min, prix_max):
    params = {
        "search_text": texte,
        "price_from": prix_min,
        "price_to": prix_max,
        "order": "newest_first",
        "per_page": 20,
    }
    try:
        r = requests.get(VINTED_API, headers=HEADERS, params=params, timeout=15)
        if r.status_code == 200:
            data = r.json()
            return data.get("items", [])
        else:
            print(f"[{texte}] Status {r.status_code}")
            return []
    except Exception as e:
        print(f"Erreur requête [{texte}] : {e}")
        return []

def formater_message(article, critere):
    titre = article.get("title", "Sans titre")
    prix = article.get("price", "?")
    marque = article.get("brand_title", "")
    taille = article.get("size_title", "")
    lien = f"https://www.vinted.fr/items/{article.get('id')}"
    photo = article.get("photo", {}).get("url", "")

    msg = (
        f"🔔 <b>NOUVELLE ALERTE VINTED</b>\n\n"
        f"👕 <b>{titre}</b>\n"
        f"💰 <b>{prix} €</b>\n"
    )
    if marque:
        msg += f"🏷 Marque : {marque}\n"
    if taille:
        msg += f"📏 Taille : {taille}\n"
    msg += f"🔍 Recherche : <i>{critere}</i>\n\n"
    msg += f"👉 <a href='{lien}'>Voir l'article</a>"
    return msg

def scanner():
    global seen_ids
    nouveaux = 0
    for (texte, prix_min, prix_max) in CRITERES:
        articles = chercher_articles(texte, prix_min, prix_max)
        for article in articles:
            article_id = article.get("id")
            if article_id and article_id not in seen_ids:
                seen_ids.add(article_id)
                msg = formater_message(article, texte)
                envoyer_telegram(msg)
                nouveaux += 1
                time.sleep(1)  # anti-spam Telegram
        time.sleep(3)  # pause entre chaque recherche
    print(f"[Scan terminé] {nouveaux} nouveaux articles trouvés")

def main():
    print("🚀 Vinted Alertes démarré !")
    envoyer_telegram("✅ <b>Vinted Alertes est en ligne !</b>\nJe scanne toutes les 2 minutes et t'envoie les bonnes affaires 🎯")

    # Premier scan : on remplit seen_ids sans notifier (évite le flood)
    print("Initialisation — chargement des articles existants...")
    for (texte, prix_min, prix_max) in CRITERES:
        articles = chercher_articles(texte, prix_min, prix_max)
        for article in articles:
            seen_ids.add(article.get("id"))
        time.sleep(2)
    print(f"{len(seen_ids)} articles existants ignorés. Surveillance active !")

    while True:
        time.sleep(SCAN_INTERVAL)
        scanner()

if __name__ == "__main__":
    main()
