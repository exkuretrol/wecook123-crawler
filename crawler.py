from pathlib import Path
from time import sleep
from bs4 import BeautifulSoup
import requests
import pandas as pd

recipes_dir = Path("__file__").resolve().parent / "recipes"
if not recipes_dir.exists():
    Path.mkdir(recipes_dir)

url = "https://www.wecook123.com/new-recipe/"

page = requests.get(url=url)

soup = BeautifulSoup(page.text, "html.parser")
soup = soup.select_one(".fusion-layout-column")

recipes = soup.select(".fusion-rollover-content")

recipes_list = []
for recipe in recipes:
    anchar = recipe.find("a")
    recipes_list.append({
        "name": anchar.contents[0],
        "url": anchar['href']
    })

for page in recipes_list:
    print(f"處理 {page['name']} 中...")
    page_html = requests.get(page['url']).text
    soup = BeautifulSoup(page_html, "html.parser")
    soup = soup.select_one("#content")

    recipe_file: Path = recipes_dir / (page['name'] + ".md")

    if not recipe_file.exists():
        Path.touch(recipe_file)

    h3s = [i.text for i in soup.find_all("h3")]

    intro = h3s[0]
    h3s.pop(0)

    step_pos = h3s.index("步驟")

    parts = h3s[:step_pos]
    steps = h3s[step_pos:]

    with recipe_file.open("w", encoding="utf-8") as f:
        f.write(f"# {soup.find('h1').text}\n")
        f.write(f"\n原文連結：{page['url']}\n")
        f.write(f"\n## {intro}\n")
        f.write("\n")
        ps = soup.find('h3', text=intro).findNext("p").parent()
        for p in ps:
            f.write(str(p).replace("<br/> ", "\n").replace("<p>",
                    "").replace("</p>", "").replace("<br/>", ""))
        f.write("\n")

        for table in parts:
            f.write(f"\n## {table}\n")
            f.write("\n")
            table_html = soup.find('h3', text=table).findNext("table")
            df = pd.read_html(str(table_html), header=0)[0]
            f.write(df.to_markdown(index=False))
            f.write("\n")

        for step in steps:
            f.write(f"\n## {step}\n")

            steps_text = [i.text for i in soup.find(
                "h3", text=step).findNext("p").findParent().find_all("p")]

            for text in steps_text:
                dot_pos = text.find(".", 0, 3) + 1
                output = text[:dot_pos] + " " + text[dot_pos:]
                f.write("\n")
                f.write(output)
                f.write("\n")

        f.close()
    sleep(3)
