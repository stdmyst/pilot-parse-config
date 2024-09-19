# from pprint import pprint
from config_parse import get_soup, parsing_xml

# import xlsxwriter
# import openpyxl
# import numpy as np
import json
import pandas as pd


# See example:
# - https://stackoverflow.com/questions/13575090/construct-pandas-dataframe-from-items-in-nested-dictionary
#
def flatten_dict(nested_dict):
    res = {}
    if isinstance(nested_dict, dict):
        for k in nested_dict:
            flattened_dict = flatten_dict(nested_dict[k])
            for key, val in flattened_dict.items():
                key = list(key)
                key.insert(0, k)
                res[tuple(key)] = val
    else:
        res[()] = nested_dict
    return res


def create_multiindex_df(values_dict, tree):
    flat_dict = flatten_dict(values_dict)
    result_list = []
    cache = dict()
    # Insert images:
    # - https://stackoverflow.com/questions/51601031/python-writing-images-and-dataframes-to-the-same-excel-file
    #
    # "Icon" and some other parameters are not specified in the script
    attr_d = {"Id": [], "Name": [], "Title": [], "Sort": [],
              "HasFiles": [], "IsDeleted": [], "Kind": [], "Attributes": [] ,
              "IsMountable": [], "IsService": [], "IsProject": [], "Configuration": []}
    for tupple_el in flat_dict:
        for i, el in enumerate(tupple_el):
            if not cache.__contains__(i):
                cache[i] = [el]
            elif el not in cache[i]:
                for to_del in [x for x in cache if x >= i]:
                    del cache[to_del]
                cache[i] = [el]
            else:
                continue
            n = [None] * i
            n.append(el)
            result_list.append({tuple(n):
                                     flat_dict[tupple_el] if i == (len(tupple_el)-1) else None})
            for k in attr_d:
                try:
                    attr_d[k].append(get_value_by_id(tree, get_id_by_title(tree, el), value=k))
                except KeyError:
                    attr_d[k].append(None)
                
    indexes = list()
    values = list()
    for el in result_list:
        indexes.append(list(el.keys())[0])
        values.append(list(el.values())[0])

    m_indexes = pd.MultiIndex.from_tuples(indexes)

    df = pd.DataFrame(data={'Комментарии': values}, index=m_indexes)
    df = df.reset_index()
    df1 = pd.DataFrame.from_dict(attr_d)
    df1 = df1.astype({"Id": int, "Sort": int})
    df = df.join(df1)

    # for el in attr_d.items():
    #     df[el[0]] = el[1]

    return df


def get_id_by_name(tree, name):
    for el in tree["SConfiguration"][0]["Metadata"][0]["Types"][0]["MType"].values():
        if el["Name"][0] == name:
            return el["Id"][0]

        
def get_id_by_title(tree, title):
    for el in tree["SConfiguration"][0]["Metadata"][0]["Types"][0]["MType"].values():
        if el["Title"][0] == title:
            return el["Id"][0]


def get_value_by_id(tree, el_id, value="Name"):
    for el in tree["SConfiguration"][0]["Metadata"][0]["Types"][0]["MType"].values():
        if el["Id"][0] == el_id:
            if value == 'Attributes':
                ar = list()
                for i in range(len(x := el[value][0]['MAttribute'])):
                    try:
                        ar.append(f'{i+1}. {x[i]['Title'][0]} ({x[i]["Name"][0]})')
                    except Exception as ex:
                        print(ex)
                        pass  
                return '\n'.join(ar)
            return el[value][0]


def search_children(tree, el_id, cache=[]):
    for el in tree["SConfiguration"][0]["Metadata"][0]["Types"][0]["MType"].values():
        if el_id == el["Id"][0]:
            try:
                if check := list(el["Children"][0]["int"].values()):
                    pass
            except KeyError:
                return
            if el_id in cache:
                return "Recursively enters the current branch."
            else:
                cache.append(el_id)
            return {f"{get_value_by_id(tree, key, value="Title")}":
                    search_children(tree, key, cache=cache.copy()) for key in check}


def main():
    with open("settings.json", encoding="UTF-8") as f:
        settings = json.load(f)
        url = settings["url"].replace("\\", "/")
        name = settings["base_element"]
    
    soup = get_soup(url)
    parsed_soup = parsing_xml(soup)
    name = 'Root_object_type'
    element_id = get_id_by_name(parsed_soup, name)
    
    if element_id:
        df = create_multiindex_df({f"{get_value_by_id(parsed_soup, element_id, value="Title")}": search_children(parsed_soup, element_id)}, parsed_soup)

        writer = pd.ExcelWriter('files/Карта типов конфигурации.xlsx', engine='xlsxwriter')
        df.to_excel(writer, sheet_name='Карта типов конфигурации', index=False)  # send df to writer
        writer.close()

        # See XlsxWriter:
        # - https://stackoverflow.com/questions/17326973/is-there-a-way-to-auto-adjust-excel-column-widths-with-pandas-excelwriter
        # 
        # Example:
        #
        # writer = pd.ExcelWriter('file_name', engine='xlsxwriter')
        # df.to_excel(writer, sheet_name='Type_tree')  # send df to writer
        # worksheet = writer.sheets['Type_tree']  # pull worksheet object
        # for idx, col in enumerate(df):  # loop through all columns
        #     series = df[col]
        #     max_len = max((
        #         series.astype(str).map(len).max(),  # len of largest item
        #         len(str(series.name))  # len of column name/header
        #         )) + 1  # adding a little extra space
        #     worksheet.set_column(idx, idx, max_len)  # set column width
        # writer.close()
        
        # To JSON:
        #
        # with open(f"files/pilot_types.json", "w", encoding="UTF-8") as f:
        #     json.dump({get_value_by_id(parsed_soup, element_id, value="Title"): search_children(parsed_soup, element_id)}, f, ensure_ascii=False, indent=4)
    else:
        print("Invalid name!")


if __name__ == "__main__":
    main()