import os
import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin, urlparse
from collections import deque


# Funkce pro stažení stránky
def download_page(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Chyba při stahování stránky: {e}")
        return None


# Funkce pro extrakci informací z článku
def extract_article_data(soup, url):
    try:
        title = soup.find("h1").get_text(strip=True) if soup.find("h1") else "Neznámý nadpis"
        category = soup.find("meta", attrs={"name": "category"})["content"] if soup.find("meta", attrs={
            "name": "category"}) else "Neznámá kategorie"
        comments_count = soup.find("span", class_="comments-count").get_text(strip=True) if soup.find("span",
                                                                                                      class_="comments-count") else "0"
        photos_count = len(soup.find_all("img"))
        content = " ".join([p.get_text(strip=True) for p in soup.find_all("p")])
        date = soup.find("time")["datetime"] if soup.find("time") else "Neznámé datum"

        return {
            "url": url,
            "title": title,
            "category": category,
            "comments_count": comments_count,
            "photos_count": photos_count,
            "content": content,
            "date": date
        }
    except Exception as e:
        print(f"Chyba při extrakci dat z článku: {e}")
        return None


# Funkce pro extrakci odkazů pouze z `base_url`
def extract_links(soup, base_url):
    links = set()
    base_netloc = urlparse(base_url).netloc  # Kořen domény
    for a_tag in soup.find_all("a", href=True):
        href = urljoin(base_url, a_tag["href"])  # Normalizace odkazu
        if urlparse(href).netloc == base_netloc:  # Kontrola, zda je odkaz na stejné doméně
            links.add(href)
    return links


# Funkce pro kontrolu velikosti souboru
def is_file_size_exceeded(file_path, max_size):
    if os.path.exists(file_path):
        return os.path.getsize(file_path) >= max_size
    return False


# Hlavní funkce crawleru
def crawler(start_url, output_file, max_file_size=1 * 1024 * 1024 * 1024):  # 1 GB
    visited = set()
    queue = deque([start_url])
    articles = []

    while queue:
        # Kontrola velikosti souboru
        if is_file_size_exceeded(output_file, max_file_size):
            print("Soubor dosáhl maximální velikosti 1 GB. Ukončuji crawler.")
            break

        url = queue.popleft()
        if url in visited:
            continue
        print(f"Zpracovávám: {url}")
        visited.add(url)

        html_content = download_page(url)
        if not html_content:
            continue

        soup = BeautifulSoup(html_content, "html.parser")

        # Pokud je článek, extrahujeme data
        article_data = extract_article_data(soup, url)
        if article_data:
            articles.append(article_data)

        # Ukládání do souboru a kontrola velikosti
        with open(output_file, "a", encoding="utf-8") as f:
            json.dump(article_data, f, ensure_ascii=False)
            f.write("\n")  # Oddělíme JSON objekty novým řádkem

        # Přidáváme nové odkazy do fronty (kontrolujeme, že jsou na stejné doméně)
        links = extract_links(soup, start_url)
        queue.extend(links - visited)


# Spuštění crawleru
if __name__ == "__main__":
    start_url = "https://www.idnes.cz/"  # Počáteční stránka
    output_file = "articles.json"
    crawler(start_url, output_file)
