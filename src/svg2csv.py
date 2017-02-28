'Parses SVG file to extract data from figures and saves as CSV'
from sys import argv
from json import load
import xml.etree.ElementTree as ET
from re import findall
import csv

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



def parse_circles(element, step=1):
    'Dumps translate attributes in subtree'
    def get_shift(el):
        'Extracts shift vector from transform string'
        return tuple(float(x) for x in findall(r'(-?\d+\.?\d*)', el.attrib["transform"]))
    def sum_tuples(a, b):
        'Element-wise tuple sum'
        return tuple(sum(x) for x in zip(a, b))
    last_shift = get_shift(element)
    position = [last_shift]

    count = 0
    for child in element.findall('.//svg:g', NS):
        try:
            shift = sum_tuples(last_shift, get_shift(child))
            count += 1
            last_shift = shift
            if not count % step:
                position.append(shift)
        except KeyError:
            continue
    return position

def parse_crosses(element):
    'Dumps translate attributes skipping every second one'
    return parse_circles(element, step=2)

def make_scale_func(coeff):
    'Closure for fixed params of scaling function'
    def scale(val, c):
        slope = (c['max_u']-c['min_u'])/(c['max_s']-c['min_s'])
        return c['min_u']+(val+c['off']-c['min_s'])*slope
    def scale_func(value):
        nonlocal coeff
        return tuple(scale(value[i], coeff[i]) for i in range(2))
    return scale_func

def rearrange(data):
    'sorts groups preserving the order of group elements'
    def flip(l):
        if l[0][0] > l[-1][0]:
            l.reverse()
        return l
    sorted_data = sorted([flip(l) for l in data], key=lambda l: l[0][0])
    return [item for sublist in sorted_data for item in sublist]

def parse_helper(config_file_name):
    'parses input SVG file'
    parsers = {
        "circles": parse_circles,
        "crosses": parse_crosses
    }
    with open(config_file_name) as json_data:
        task_config = load(json_data)
    for task in task_config:
        tree = ET.parse(task['input_file'])
        root = tree.getroot()
        for series in task["series"]:
            container = find_start_elem(root, series["id_from"])
            parse_ids = collect_siblings(container, series["id_from"], series["id_to"])
            data = []
            for elem_id in parse_ids:
                data.append(parsers[series["type"]](
                    container.find('./*[@id="{}"]'.format(elem_id))))
            coeff = ({
                'off': series["elem_offset_svg"][0],
                'min_u': task["x_range_shown"][0],
                'max_u': task["x_range_shown"][1],
                'min_s': task["x_range_svg"][0],
                'max_s': task["x_range_svg"][1]
            }, {
                'off': series["elem_offset_svg"][1],
                'min_u': series["y_range_shown"][0],
                'max_u': series["y_range_shown"][1],
                'min_s': series["y_range_svg"][0],
                'max_s': series["y_range_svg"][1]
            })
            sorted_data = rearrange(data)
            scale_func = make_scale_func(coeff)
            scaled_data = [scale_func(item) for item in sorted_data]
            with open(task['output_prefix']+series['y_name']+'.csv', 'wt') as fout:
                print('{},{}'.format(task['x_name'], series['y_name']), file=fout)
                cout = csv.writer(fout)
                cout.writerows(scaled_data)

if __name__ == '__main__':
    parse_helper(argv[1])

