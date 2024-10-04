from config import Config
from config_parse import get_soup, parsing_xml
from bs4 import BeautifulSoup as Soup
from typing import Any
from binascii import Error as binasciiError

import pandas as pd
import ast
import xlsxwriter
import base64


def get_id_by_name(tree: dict, name: str) -> (str | None):
    for key, val in tree.items():
        if val["Name"][0] == name:
            return key
        

def search_children(
        type_id: str,
        obj_tree: dict,
        new_obj_tree: list = [],  # result object
        cache_id: list[str] = [],  # to check if an object is included in a branch more than once,
                                   # a copy is passed to each branch (function)
        cache_attrs: list[str] = [],  # to check the required attributes
        level_x: list = [-1],  # list, as it allows the current value to be used as a parameter to a recursive function
        level_y: list = [-1],
        max_level_x: list = [0],
        ) -> (tuple[list, int, int, list[str]] | None):
    
    level_y[0] += 1
    level_x[0] += 1
    if not (flag := (type_id in cache_id)):
        cache_id.append(type_id)  
    current_type = (obj_tree[type_id])
    current_type.update(
        {
            "level_x": level_x[0],
            "level_y": level_y[0],
            "Recursion": {0: flag if flag else None},
            }
            )
    new_obj_tree.append(current_type.copy())  # it is important to use a copy of dict
    if flag:
        return
    cache_attrs.extend([attr for attr in current_type.keys() if (
        attr not in cache_attrs and attr not in ("level_x", "level_y")
        )])
    try:
        type_child = obj_tree[type_id]["Children"][0]["int"].values()
        if level_x[0] > max_level_x[0]:
            max_level_x[0] = level_x[0]
        [search_children(
            type_id=ch,
            obj_tree=obj_tree,
            new_obj_tree=new_obj_tree,
            cache_id=cache_id.copy(),
            cache_attrs=cache_attrs,
            level_x=level_x.copy(),
            level_y=level_y,
            max_level_x=max_level_x,
            ) for ch in type_child]
        return new_obj_tree, max_level_x[0], level_y[0], cache_attrs
    except KeyError:
        return


def make_attr_as_str(a) -> (str | Any):
    try:
        d = ast.literal_eval(a)  # see https://docs.python.org/3/library/ast.html
        if not isinstance(d, dict):
            raise TypeError
        if len(d) == 0:
            raise Exception("Empty dict")
    except TypeError:
        return a
    except Exception:
        return a
    else:
        ar = list()
        count = 0
        for i in range(len(x := d['MAttribute'])):
            ar.append([x[i]["Title"][0], x[i]["Name"][0]])
            count = i+1
        indent = max([len(el[0]) for el in ar]) + 1 #len(str(count)) + 6
        # on the line
        s = [f'{i+1}.'.ljust(len(str(count))+2) + (f'\"{el[0]}\":').ljust(indent+3) + f'\"{el[1]}\"' for i, el in enumerate(ar)]
        # under the line
        # s = [f'{i+1}.'.ljust(len(str(count))+2) + (f'\"{el[0]}\":\n') + (" " * (len(str(count))+2)) + f'\"{el[1]}\"' for i, el in enumerate(ar)]
        return '\n'.join(s)
    

# iterates over a dictionary and gets unique attribute keys
def get_attr_keys(tree, cache=[]) -> dict[Any, list]:
    for el in tree:
        try:
            for s in list(list(el["Attributes"][0]["MAttribute"].values())[0].keys()):
                 if s not in cache:
                      cache.append(s)
        except Exception:
            continue
    return {k: [] for k in sorted(cache)}


def make_attrs_df(tree) -> pd.DataFrame:
    cache_types = []  # to avoid getting duplicate types in the tree
    search_result = {"Id": [], "TypeTitle": [], "TypeName": []}
    attrs_keys = get_attr_keys(tree)
    search_result.update({k: [] for k in attrs_keys})
    for el in tree:
        if el["Id"][0] in cache_types:
            continue
        cache_types.append(el["Id"][0])
        search_result["Id"].append(el["Id"][0])
        search_result["TypeName"].append(el["Name"][0])
        search_result["TypeTitle"].append(el["Title"][0])
        try:
            attrs = el["Attributes"][0]["MAttribute"].values()
            flag = 1
            for attr in attrs:
                k = set(list(attr.keys()))
                diff_k = set(attrs_keys).difference(k)
                [search_result[x].append(attr[x][0]) for x in attr.keys()]
                [search_result[x].append(None) for x in diff_k]
                if flag:
                    flag = 0
                    continue
                [search_result[x].append(None) for x in ["Id", "TypeName", "TypeTitle"]]
        except KeyError:
            [search_result[x].append(None) for x in attrs_keys]                  
    return pd.DataFrame(search_result)
        

def main() -> None:
    config: Config = Config()
    CONFIG_PATH: str = config.CONFIG_PATH
    BASE_ELEMENT: str = config.BASE_ELEMENT
    
    soup: Soup = get_soup(CONFIG_PATH)
    parsed_soup_w_id: dict = {
        t["Id"][0]: t for t in list(parsing_xml(soup)["MType"].values())
        }
    el_id: str = (
        "0" if BASE_ELEMENT == "Root_object_type"
        else get_id_by_name(parsed_soup_w_id, Config.BASE_ELEMENT)
        )
    data, max_level_x, max_level_y, attrs = search_children(
        type_id=el_id,
        obj_tree=parsed_soup_w_id,
        )
    columns = [f"level_{x}" for x in range(max_level_x+1)]
    columns.extend(attrs)
    ids = [y for y in range(max_level_y+1)]
    df = pd.DataFrame(
        columns=columns,
        index=ids,
        data=None
    )
    for d in data:
        y, x = d["level_y"], d["level_x"]
        # n = d["Title"][0]
        # df.iloc[y, x] = n
        for attr in attrs:
            if attr not in d:
                d[attr] = None
            try:
                df.loc[y, attr] = (
                    d[attr][0] if attr == "Recursion" else str(d[attr][0])
                    )  # to see bool/none value in data frame
                       # and set empty field in excel if value is none
            except Exception as e:
                print(e)
                pass
    df_hierarchy = df.copy()
    if "Attributes" in df_hierarchy.columns:
        df_hierarchy.loc[:, "Attributes"] = (
            df_hierarchy.loc[:, "Attributes"].apply(lambda x: make_attr_as_str(x))
            )
    if "Children" in df_hierarchy.columns:
        df_hierarchy = df_hierarchy.drop(columns=["Children"])
    df_attrs = make_attrs_df(tree=data)
    
    # see XlsxWriter: https://stackoverflow.com/questions/17326973/is-there-a-way-to-auto-adjust-excel-column-widths-with-pandas-excelwriter
    writer = pd.ExcelWriter('files/Карта типов конфигурации.xlsx', engine='xlsxwriter')
    
    df_hierarchy.to_excel(writer, sheet_name='Карта типов конфигурации', index=False)  # send df to writer
    df_attrs.to_excel(writer, sheet_name='Атрибуты типов', index=False)
    
    # save the icon and set the link in the "Icon" column
    workbook  = writer.book
    worksheet = workbook.get_worksheet_by_name('Карта типов конфигурации')

    col = df_hierarchy.columns.get_loc("Icon")
    
    '''
    # need exception handler
    images = [base64.b64decode(image) for image in df_hierarchy.loc[:, "Icon"].to_list()]
    '''
    # need to add caching to avoid saving already saved icons
    images = []
    for image in df_hierarchy.loc[:, "Icon"].to_list():
        try:
            images.append(base64.b64decode(image))  # checking if correct string
        except binasciiError:
            images.append("")
        except TypeError:
            images.append("")

    count = 0
    # path = "/".join(__file__.replace("\\", "/").split("/")[:-2]) + "/files/icons/"
    path = "files/icons/"
    for row, image in enumerate(images):
        # ic = f"icon_0.svg"  # testing
        ic = f"icon_{count}.svg"
        if image == "":
            continue
        with open(path+ic, "wb") as f:
            f.write(image)
        ''' 
        # svg2png uses third path dll
        svg2png(bytestring=image, write_to=(path+".png"))
        worksheet.embed_image(row+1, col, p)
        '''
        worksheet.write_url(row+1, col, "icons/"+ic, string="Open icon")  # "icons/"+ic instead path+ic
        count += 1
    
    writer.close()


if __name__ == "__main__":
    main()