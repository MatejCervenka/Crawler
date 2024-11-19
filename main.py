import requests
from bs4 import BeautifulSoup
import json
import os

# Fronta na odkazy ke zpracování
link_queue = ["https://www.ceskenoviny.cz/zpravy/okamura-spd-udela-maximum-aby-koalici-zabranilo-zvysit-platy-politiku/2597461"]  # Startovací URL
visited_links = set()  # Pro zamezení opakovaného zpracování

# Uložená data
articles = []

def fetch_page(url):
    """Stáhne obsah stránky."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Chyba při stahování {url}: {e}")
        return None

def parse_article(url, html):
    """Zpracuje obsah stránky a vyparsuje požadovaná data."""
    soup = BeautifulSoup(html, "html.parser")
    try:
        # Nadpis
        title = soup.find("h1").get_text(strip=True)
        # Kategorie
        category = soup.find("meta", {"name": "category"})["content"] if soup.find("meta", {"name": "category"}) else "Neznámá"
        # Počet komentářů
        comments = soup.find("span", class_="comments-count").get_text(strip=True) if soup.find("span", class_="comments-count") else "0"
        # Počet fotek
        photos = len(soup.find_all("img"))
        # Obsah
        content = " ".join(p.get_text(strip=True) for p in soup.find_all("p"))

        return {
            "url": url,
            "title": title,
            "category": category,
            "comments": int(comments),
            "photos": photos,
            "content": content,
        }
    except Exception as e:
        print(f"Chyba při parsování {url}: {e}")
        return None

def get_links(html):
    """Najde všechny odkazy na stránce."""
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        print(f"Zpracovávám odkaz: {href}")  # Debug výpis odkazu
        if href.startswith("/") or href.startswith("https://www.novinky.cz"):
            # Pokud je odkaz interní nebo na novinky.cz, vynecháme ho
            continue
        if href.startswith("https://www.ceskenoviny.cz"):
            links.append(href)
    return links



def print_last_saved_article(article):
    """Vypíše poslední uložený článek."""
    print("\nPoslední uložený článek:")
    print(f"Nadpis: {article['title']}")
    print(f"Kategorie: {article['category']}")
    print(f"Počet komentářů: {article['comments']}")
    print(f"Počet fotek: {article['photos']}")
    print(f"Obsah: {article['content'][:500]}...")  # Zkrácený obsah
    print(f"Odkaz: {article['url']}")
    print("-" * 40)

def print_links_from_page(html):
    """Vypíše odkazy <a> nalezené na stránce."""
    links = get_links(html)
    print("\nOdkazy nalezené na stránce:")
    for link in links:
        print(link)
    print("-" * 40)

MAX_ARTICLES = 10  # Maximální počet článků ke zpracování
articles_processed = 0  # Počet zpracovaných článků

# Hlavní smyčka crawleru
while link_queue and articles_processed < MAX_ARTICLES:
    current_link = link_queue.pop(0)
    if current_link in visited_links:
        continue

    print(f"Zpracovávám: {current_link}")
    visited_links.add(current_link)

    page_content = fetch_page(current_link)
    if not page_content:
        continue

    # Parsování článku
    article_data = parse_article(current_link, page_content)
    if article_data:
        articles.append(article_data)
        print_last_saved_article(article_data)  # Výpis posledního uloženého článku
        articles_processed += 1

    # Výpis odkazů na stránce
    print_links_from_page(page_content)

    # Získání dalších odkazů
    new_links = get_links(page_content)
    link_queue.extend(new_links)

    # Uložení po každých 100 článcích
    if len(articles) % 100 == 0:
        with open("articles.json", "w", encoding="utf-8") as f:
            json.dump(articles, f, ensure_ascii=False, indent=4)
        print("Uloženo 100 článků!")

# Konečné uložení dat
with open("articles.json", "w", encoding="utf-8") as f:
    json.dump(articles, f, ensure_ascii=False, indent=4)
print(f"Uloženo celkem {len(articles)} článků.")

