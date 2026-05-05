import requests
import time
import os

# ============================================================
#  CONFIGURATION
# ============================================================
TELEGRAM_TOKEN = "8380287819:AAEMvS9RHaV_UR1AZUl2oL5yJq4QoX-SYeA"
TELEGRAM_CHAT_ID = "8714623764"
SCAN_INTERVAL = 120

VINTED_EMAIL = os.environ.get("VINTED_EMAIL", "")
VINTED_PASSWORD = os.environ.get("VINTED_PASSWORD", "")

CRITERES = [
    ("ralph lauren veste", 10, 20),
    ("burberry veste", 10, 20),
    ("supreme veste", 10, 20),
    ("lacoste veste", 10, 20),
    ("tommy hilfiger veste", 10, 20),
    ("stone island veste", 10, 20),
    ("sac bash", 50, 70),
    ("sac gerard darel", 50, 70),
    ("sac maje", 50, 70),
    ("sac jerome dreyfuss", 50, 70),
    ("sac sandro", 50, 70),
    ("sac vanessa bruno", 50, 70),
    ("sac balenciaga", 50, 70),
    ("ceinture burberry", 10, 20),
    ("ceinture ralph lauren", 10, 20),
    ("ceinture gucci", 10, 20),
    ("lunettes ray ban", 10, 20),
    ("lunettes gucci", 10, 20),
    ("lunettes chanel", 10, 20),
    ("lunettes dior", 10, 20),
    ("jordan", 30, 50),
    ("air jordan", 30, 50),
    ("supreme sneakers", 30, 50),
    ("new balance 550", 30, 50),
    ("santiague", 10, 20),
    ("santiague frange", 10, 20),
    ("boots western", 10, 20),
]
# ============================================================

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "fr-FR,fr;q=0.9",
    "Origin": "https://www.vinted.fr",
    "Referer": "https://www.vinted.fr/",
})

seen_ids = set()

def get_csrf_token():
    try:
        r = session.get("https://www.vinted.fr/", timeout=15)
        for cookie in session.cookies:
            if cookie.name == "_vinted_fr_session":
                return True
        return False
    except Exception as e:
        print(f"Erreur CSRF: {e}")
        return False

def login():
    print("Connexion à Vinted...")
    try:
        get_csrf_token()
        time.sleep(2)
        
        payload = {
            "login": VINTED_EMAIL,
            "password": VINTED_PASSWORD,
        }
        
        r = session.post(
            "https://www.vinted.fr/api/v2/sessions",
            json=payload,
            timeout=15
        )
        
        if r.status_code == 200:
            print("✅ Connecté à Vinted !")
            return True
        else:
            print(f"Echec connexion: {r.status_code}")
            return False
    except Exception as e:
        print(f"Erreur login: {e}")
        return False

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
        print(f"Erreur Telegram: {e}")

def chercher_articles(texte, prix_min, prix_max):
    params = {
        "search_text": texte,
        "price_from": prix_min,
        "price_to": prix_max,
        "order": "newest_first",
        "per_page": 20,
    }
    try:
        r = session.get(
            "https://www.vinted.fr/api/v2/catalog/items",
            params=params,
            timeout=15
        )
        if r.status_code == 401:
            print("Session expirée, reconnexion...")
            login()
            return []
        if r.status_code == 200:
            return r.json().get("items", [])
        print(f"[{texte}] Status {r.status_code}")
        return []
    except Exception as e:
        print(f"Erreur [{texte}]: {e}")
        return []

def formater_message(article, critere):
    titre = article.get("title", "Sans titre")
    prix = article.get("price", "?")
    marque = article.get("brand_title", "")
    taille = article.get("size_title", "")
    lien = f"https://www.vinted.fr/items/{article.get('id')}"

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
                time.sleep(1)
        time.sleep(3)
    print(f"[Scan terminé] {nouveaux} nouveaux articles")

def main():
    print("🚀 Vinted Alertes démarré !")
    
    if not login():
        envoyer_telegram("⚠️ Impossible de se connecter à Vinted. Vérifie les identifiants.")
        return

    envoyer_telegram("✅ <b>Vinted Alertes est en ligne !</b>\nJe scanne toutes les 2 minutes 🎯")

    print("Initialisation...")
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
