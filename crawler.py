from pathlib import Path
from time import sleep
from bs4 import BeautifulSoup
import requests
import pandas as pd

# 如專案資料夾底下不存在 "recipe" 資料夾，則建立它
recipes_dir = Path("__file__").resolve().parent / "recipes"
if not recipes_dir.exists():
    Path.mkdir(recipes_dir)

# 食譜們網址
url = "https://www.wecook123.com/new-recipe/"

# get 方法得到頁面
page = requests.get(url=url)

# 將食譜們頁面轉成 BeautifulSoup 物件
soup = BeautifulSoup(page.text, "html.parser")

# 利用 css selector 縮小範圍
soup = soup.select_one(".fusion-layout-column")

# 食譜的 div list
recipes = soup.select(".fusion-rollover-content")

# 用於儲存食譜們的清單
recipes_list = []
for recipe in recipes:
    # 將錨點取出，毛點的內容即為食譜名稱，href 屬性為網址
    anchar = recipe.find("a")
    recipes_list.append({
        "name": anchar.contents[0],
        "url": anchar['href']
    })

# 用 for 迴圈跑每個食譜
for page in recipes_list:
    print(f"處理 {page['name']} 中...")
    # 分別從食譜 list 中得到網址，並使用 get 方法
    page_html = requests.get(page['url']).text
    soup = BeautifulSoup(page_html, "html.parser")
    
    # 內容剛好在 content ID 內
    soup = soup.select_one("#content")

    # 以食譜名稱建立黨案，如果不存在則建立它
    recipe_file: Path = recipes_dir / (page['name'] + ".md")
    if not recipe_file.exists():
        Path.touch(recipe_file)

    # h3 們
    h3s = [i.text for i in soup.find_all("h3")]

    # 第一個一定為簡介
    intro = h3s[0]
    h3s.pop(0)

    # 以步驟關鍵字切分 table 與步驟
    step_pos = h3s.index("步驟")

    # table
    parts = h3s[:step_pos]

    # 步驟
    steps = h3s[step_pos:]

    # 格式化
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

            # 利用 pandas 讀入 html table，再用 markdown 寫入檔案
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

        # 關閉檔案 
        f.close()
    sleep(3)
