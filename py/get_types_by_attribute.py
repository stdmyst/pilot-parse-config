from config_parse import get_soup, parsing_xml
from pprint import pprint

# import pandas as pd
import json


def main():
    with open("settings.json", encoding="UTF-8") as f:
        settings = json.load(f)
        url = settings["url"].replace("\\", "/")
    
    search_result = {}
    search_key = input("Enter attribute name: ")

    soup = get_soup(url)
    parsed_soup = parsing_xml(soup)
    
    count = 0
    for el in parsed_soup["SConfiguration"][0]["Metadata"][0]["Types"][0]["MType"].values():
        try:
            for sub_el in el["Attributes"][0]["MAttribute"].values():
                if sub_el["Name"][0] == search_key:
                    el_dict = dict()
                    el_dict["ID"] = el["Id"][0]
                    el_dict["Title"] = el["Title"][0]
                    el_dict["Name"] = el["Name"][0]
                    search_result[count] = el_dict
                    count += 1
        except KeyError as e:
            continue

    # df = pd.DataFrame(search_result)
    pprint(search_result)


if __name__ == "__main__":
    main()