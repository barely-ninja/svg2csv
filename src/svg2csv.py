'Parses SVG file to extract data from figures and saves as CSV'
from sys import argv
from json import load
import xml.etree.ElementTree as ET

def find_start_elem(elem, search_id):
    'searches for element'
    for child in elem:
        try:
            if child.attrib["id"] == search_id:
                return elem, child
            else:
                parent, kid = find_start_elem(child, search_id)
                if parent is not None:
                    return parent, kid
        except KeyError:
            continue
    return None, None

def parse_helper(config_file_name):
    'parses input SVG file'
    with open(config_file_name) as json_data:
        task_config = load(json_data)
    for task in task_config:
        tree = ET.parse(task['input_file'])
        root = tree.getroot()
        for graph in task["graph"]:
            container, start_elem = find_start_elem(root, graph["id_from"])
            for child in container:
                print(child.attrib["id"])


if __name__ == '__main__':
    parse_helper(argv[1])

