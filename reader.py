# Author: Carlos Natalino
# 

import networkx as nx
import matplotlib.pyplot as plt

from xml.dom.minidom import parse
import xml.dom.minidom
import math
import numpy as np

import os

def calculate_geographical_distance(latlong1, latlong2):
    R = 6373.0

    lat1 = math.radians(latlong1[0])
    lon1 = math.radians(latlong1[1])
    lat2 = math.radians(latlong2[0])
    lon2 = math.radians(latlong2[1])

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    length = R * c
    return length

def read_file(file, topology_name):
    if file.endswith('.xml'):
        return read_sndlib_topology(file, topology_name)
    with open(file, 'r') as nodes_lines:
        for idx, line in enumerate(nodes_lines):
            if line.replace("\n", "") == "1":
                return read_txt_file(file, topology_name)

def read_txt_file(file, topology_name):
    graph = nx.Graph(name=topology_name)
    nNodes = 0
    nLinks = 0
    with open(file, 'r') as nodes_lines:
        for idx, line in enumerate(nodes_lines):
            if idx > 2 and idx <= nNodes + 2: # skip title line
                info = line.replace("\n", "").replace(',', '.').split("\t")
                graph.add_node(info[0], name=info[1], pos=(float(info[2]), float(info[3])))
            elif idx > 2 + nNodes and idx <= 2 + nNodes + nLinks: # skip title line
                info = line.replace("\n", "").split("\t")
                n1 = graph.nodes[info[1]]
                n2 = graph.nodes[info[2]]
                dist = calculate_geographical_distance(n1['pos'], n2['pos'])
#                 print(n1['name'], n1['pos'], n2['name'], n2['pos'], '{:.2f}'.format(dist), info[3])
                final_distance = float('{:.2f}'.format(max(dist, float(info[3]))))
                graph.add_edge(info[1], info[2], id=int(info[0]), weight=final_distance)
            elif idx == 1:
                nNodes = int(line)
            elif idx == 2:
                nLinks = int(line)
    return graph

def read_simmons_txt(file):
    graph = nx.Graph()
    topology_name = file.split(".")[0]
    nNodes = 0
    nLinks = 0
    with open("topologies/" + file, 'r') as nodes_lines:
        for idx, line in enumerate(nodes_lines):
            if idx > 1 and idx <= nNodes + 1:  # skip title line
                info = line.replace("\n", "").replace(",", ".").split("\t")
                graph.add_node(info[0], name=info[0], pos=(float(info[2]), float(info[1])))
            elif idx > 1 + nNodes and idx <= 1 + nNodes + nLinks:  # skip title line
                info = line.replace("\n", "").split("\t")
                graph.add_edge(info[0], info[1], weight=float(info[2]))
            elif idx == 0:
                nNodes = int(line)
            elif idx == 1:
                nLinks = int(line)
    return graph

def read_sndlib_topology(file, topology_name):
    graph = nx.Graph(name=topology_name)

    max_lat = np.finfo(0.0).min
    max_lng = np.finfo(0.0).min
    min_lat = np.finfo(0.0).max
    min_lng = np.finfo(0.0).max
    with open(file) as file:
        tree = xml.dom.minidom.parse(file)
        document = tree.documentElement

        graph.graph["coordinatesType"] = document.getElementsByTagName("nodes")[0].getAttribute("coordinatesType")

        nodes = document.getElementsByTagName("node")
        node_names = {}
        for idn, node in enumerate(nodes):
            x = node.getElementsByTagName("x")[0]
            y = node.getElementsByTagName("y")[0]
            # print(node['id'], x.string, y.string)
            node_names[node.getAttribute("id")] = str(idn+1)
            graph.add_node(str(idn+1), name=node.getAttribute("id"), pos=((float(x.childNodes[0].data), float(y.childNodes[0].data))))
        print("Total nodes: ", graph.number_of_nodes())

        links = document.getElementsByTagName("link")
        for link in links:
            source = link.getElementsByTagName("source")[0]
            target = link.getElementsByTagName("target")[0]

            if graph.graph["coordinatesType"] == "geographical":
                length = np.around(calculate_geographical_distance(graph.nodes[node_names[source.childNodes[0].data]]["pos"], graph.nodes[node_names[target.childNodes[0].data]]["pos"]), 3)
                max_lat = max(max_lat, graph.nodes[node_names[source.childNodes[0].data]]["pos"][0])
                max_lng = max(max_lng, graph.nodes[node_names[source.childNodes[0].data]]["pos"][1])
                min_lat = min(min_lat, graph.nodes[node_names[source.childNodes[0].data]]["pos"][0])
                min_lng = min(min_lng, graph.nodes[node_names[source.childNodes[0].data]]["pos"][1])
            else:
                latlong1 = graph.nodes[node_names[source.childNodes[0].data]]["pos"]
                latlong2 = graph.nodes[node_names[target.childNodes[0].data]]["pos"]
                length = np.around(math.sqrt((latlong1[0] - latlong2[0]) ** 2 + (latlong1[1] - latlong2[1]) ** 2), 3)

            graph.add_edge(node_names[source.childNodes[0].data], node_names[target.childNodes[0].data], id=link.getAttribute("id"), weight=length)
        print("Total edges: ", graph.number_of_edges())
    graph.graph["max_latlong"] = np.array([max_lat, max_lng])
    graph.graph["min_latlong"] = np.array([min_lat, min_lng])
    graph.graph["node_indices"] = node_names
    return graph

# read_simmons_txt("usnet.txt")
#
# for file in os.listdir("./topologies/sndlib-networks-xml/"):
#     if file.endswith(".xml"):
#         read_sndlib_topology(file)
import subprocess
def compress():
    try:
        output = subprocess.check_output("zip -r allfiles.zip * -x \"*pycache*\" -x \"*ipynb_checkpoints*\"", shell=True, stderr=subprocess.STDOUT)
        output = output.decode("utf-8")
        if(output):
            print(output, end="")
    except subprocess.CalledProcessError as e:
        print('FATAL ERROR: [%s] %s' % (e.returncode, e.output.decode("utf-8")))
        print("FAIL")
        return
    print("SUCCESS")
    print("Right click on the allfiles.zip file and select download")
    return
    
