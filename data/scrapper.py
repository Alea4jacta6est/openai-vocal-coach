import requests
from bs4 import BeautifulSoup
import re
import json
import os

BASE_URL = "https://www.tongue-twister.net"

def fetch_index():
    resp = requests.get(BASE_URL)
    resp.encoding = resp.apparent_encoding
    html = resp.content.decode('utf-8', 'ignore')
    soup = BeautifulSoup(html, 'html.parser', from_encoding='utf-8')
    langs = {}
    # Looks for links with href like "#cpf"
    for a in soup.select("a[href^='#']"):
        code = a["href"].lstrip("#")
        name = a.text.strip()
        langs[code] = name
    return langs

def fetch_twisters(code):
    url = f"{BASE_URL}/{code}.htm"
    resp = requests.get(url)
    resp.encoding = resp.apparent_encoding
    html = resp.content.decode('utf-8', 'ignore')
    soup = BeautifulSoup(html, 'html.parser', from_encoding='utf-8')

    twisters = []
    for p in soup.select("p.TXT"):
        # Inside TXT, often the real text is in <a class="P"> or plain text
        a_tag = p.find("a", class_="P")
        if a_tag:
            text = a_tag.get_text(strip=True)
        else:
            text = p.get_text(strip=True)

        if text:
            twisters.append(text)

    return twisters

def main():
    langs = fetch_index()
    result = {}

    for code, name in langs.items():
        print(f"Fetching {name} ({code})")
        try:
            tw = fetch_twisters(code)
            if tw:
                result[name] = tw
            else:
                print(f"⚠️ No twisters found for {name}")
        except Exception as e:
            print(f"❌ Error fetching {code}: {e}")

    sorted_result = dict(
        sorted(result.items(), key=lambda item: len(item[1]), reverse=True)
    )

    # Define output file path
    output_file = os.path.join(os.getcwd(), "data/tongue_twisters.json")

    # Save to JSON
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(sorted_result, f, ensure_ascii=False, indent=2)

    print(f"✅ Saved JSON file to {output_file}")

if __name__ == "__main__":
    main()