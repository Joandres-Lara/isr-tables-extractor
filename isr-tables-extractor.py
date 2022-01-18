import re
import bs4
import json
from unidecode import unidecode

from urllib.request import urlopen, Request

URL = "http://dof.gob.mx/nota_detalle.php?codigo=5640505&fecha=12/01/2022"


def get_content_url(url):
    with urlopen(Request(url, headers={"Accept": "text/html"})) as response:
        return response.read().decode()


def normalize_str(dirty_string):
    return re.sub("[\n\s\t]+", " ", unidecode(dirty_string)).strip()


def parse_td_values(td):
    return re.sub(" ", "_", normalize_str(td.get_text())).lower()


def get_table_as_list(table, heads_if_table_has_break_point_page):

    table_list = []
    table_heads = []
    merge_with_last = False

    if table.has_attr("style"):
        if "page-break" in table.get("style"):
            table_heads = heads_if_table_has_break_point_page
            merge_with_last = True

    for el in table.descendants:
        if el and el.name == "tr":
            ignore_tr = False

            values = list(
                map(parse_td_values, filter(lambda td: td.get_text().strip()
                    != "" and not "colspan" in str(td), el.children))
            )

            # Firt element in table is the head
            if len(table_heads) == 0:
                table_heads = values
                ignore_tr = True
            elif len(table_heads) != 0 and len(table_heads) == len(values):
                dictionary_values = {}
                for ihead in range(len(table_heads)):
                    value = values[ihead]
                    try:
                        value = float(re.sub(",", "", value))
                    except:
                        if "en_adelante" in value:
                            value = 9999999999
                        else:
                            ignore_tr = True
                    dictionary_values[table_heads[ihead]] = value

                values = dictionary_values
            else:
                ignore_tr = True

            if not ignore_tr:
                table_list.append(values)
    return table_list, table_heads, merge_with_last


def find_valid_tables(tag):
    if tag and tag.name == "table":
        # Ignore table in table
        for descendant in tag.descendants:
            if descendant.name == "table":
                return False
        return True
    return False


def parse_tables(html_string):
    loader = bs4.BeautifulSoup(html_string, "html.parser")
    tables = loader.find_all(find_valid_tables)
    tables_list = []
    last_heads = []

    for table in tables:
        title = table.previous_sibling

        while title and title.name == "table" or title and title.get_text().strip() == "":
            title = title.previous_sibling
            if(table.parent == title):
                title = None
                break

        if title:
            title = normalize_str(title.get_text())

        list_table, heads, merged_with_last = get_table_as_list(
            table, last_heads)
        last_heads = heads

        # Detect page break point
        if merged_with_last:
            last_index = len(tables_list) - 1
            last_descriptor = tables_list[last_index]
            tables_list[last_index] = {
                "title": last_descriptor.get("title"),
                "table": last_descriptor.get("table") + list_table
            }
        else:
            values = {
                "title": title,
                "table": list_table
            }
            tables_list.append(values)
    # Only tables with values
    return list(filter(lambda x: x.get("table") != [], tables_list))


def main():
    value = parse_tables(
        open("./tests/input-html/real-all-tables.html", encoding="utf-8").read())
    file_json = open("./output.json", "w")
    file_json.write(json.dumps(value, indent=2))
    file_json.close()
    print("Archivo creado")


if __name__ == "__main__":
    main()
