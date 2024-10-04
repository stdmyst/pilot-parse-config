from bs4 import (
    ProcessingInstruction, Doctype, NavigableString,
                 BeautifulSoup as Soup)
from config import Config
from pathlib import Path

import json
# import requests


def parsing_xml(tree: Soup) -> (str | dict):
    cache = {}
    result = {}
    for sub_tree in tree.contents:
        if any([isinstance(sub_tree, x) for x in (ProcessingInstruction, Doctype)]):
            pass
        else:
           if str(sub_tree) != "\n":
                if isinstance(sub_tree, NavigableString):
                    return str(sub_tree)
                if sub_tree.name not in result:
                    result[sub_tree.name] = {}
                    cache[sub_tree.name] = 0
                result[sub_tree.name][cache[sub_tree.name]] = parsing_xml(sub_tree)
                cache[sub_tree.name] += 1
    return result


def get_soup(url: str) -> Soup:
    # if url.startswith("http"):
    #     try:
    #         req = requests.get(url)
    #         req.raise_for_status()
    #     except requests.HTTPError as e:
    #         print(e)
    #         return
    #     except Exception as e:
    #         print(e)
    #         return
    #     else:
    #         print(req)
    #         req.encoding = "UTF-8"
    #         soup = Soup(req.text, "xml")
    # else:
    
    try:
        with open(url, encoding="UTF-8") as f:
            t = Soup(f, "xml").find("Types")
            return t
    except OSError as e:
        print(e)


def main() -> None:
    # with open("settings.json", encoding="UTF-8") as f:
    #     settings = json.load(f)
    #     url = settings["url"].replace("\\", "/")

    url = Config.CONFIG_PATH 
    
    if (bs_obj := get_soup(url)):
        result = parsing_xml(bs_obj)
        with open(f"files/{Path(url).stem}.json", "w", encoding="UTF-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()