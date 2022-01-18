import re
import bs4
import json

from urllib.request import urlopen, Request

URL = "http://dof.gob.mx/nota_detalle.php?codigo=5640505&fecha=12/01/2022"


def get_content_url(url):
    with urlopen(Request(url, headers={"Accept": "text/html"})) as response:
        return response.read().decode()


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
                map(lambda td: re.sub(" ", "_", re.sub("[\n\s\t]+", " ", td.get_text()).strip()).lower(),
                    filter(lambda td: td.get_text().strip() != "", el.children))
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
                        if "En adelante" in value:
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

    for itable in range(len(tables)):
        table = tables[itable]
        title = None

        if table.previous_sibling and table.previous_sibling.name != "table":
            title = table.previous_sibling.string


        list_table, heads, merged_with_last = get_table_as_list(
            table, last_heads)
        last_heads = heads

        if len(list_table) != 0:
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
    return tables_list


def main():
    value = parse_tables(
        open("./tests/input-html/real-all-tables.html", encoding="utf-8").read())
    file_json = open("./output.json", "w")
    file_json.write(json.dumps(value, indent=2, sort_keys=True))
    file_json.close()
    print("Archivo creado")


if __name__ == "__main__":
    main()
