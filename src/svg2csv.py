'Parses SVG file to extract data from figures and saves as CSV'
from sys import argv
from json import load
import xml.etree.ElementTree as ET
from re import search

NS = {
    'svg': 'http://www.w3.org/2000/svg'
}

def find_start_elem(elem, search_id):
    'searches for element'
    for child in elem:
        try:
            if child.attrib["id"] == search_id:
                return elem
            else:
                parent = find_start_elem(child, search_id)
                if parent is not None:
                    return parent
        except KeyError:
            continue
    return None

def collect_siblings(parent, id_from, id_to):
    'Collects siblings to parse between 2 IDs'
    id_list = []
    add = False
    for child in parent:
        if child.attrib["id"] == id_from:
            add = True
        if add:
            id_list.append(child.attrib["id"])
        if child.attrib["id"] == id_to:
            return id_list

def parse_circles(element):
    'Dumps translate attributes in subtree'
    for child in element.findall('.//svg:g', NS):
        try:
            vector = search(r'\((\S+)\)', child.attrib["transform"]).group(1).split(',')
            print(child.attrib["id"], vector)
        except KeyError:
            continue
    return None

def parse_helper(config_file_name):
    'parses input SVG file'
    parsers = {
        "circles": parse_circles
    }
    with open(config_file_name) as json_data:
        task_config = load(json_data)
    for task in task_config:
        tree = ET.parse(task['input_file'])
        root = tree.getroot()
        for graph in task["graph"]:
            container = find_start_elem(root, graph["id_from"])
            parse_ids = collect_siblings(container, graph["id_from"], graph["id_to"])
            for elem_id in parse_ids:
                parsers[graph["type"]](container.find('./*[@id="{}"]'.format(elem_id)))

if __name__ == '__main__':
    parse_helper(argv[1])

