import os
import sys
import datetime
import numpy as np
import networkx as nx

from cross_solver import ModelFile, mode
        

def rpp_min_d(graph, budget):
    file = ModelFile('./models/rpp-{}_{}'.format(graph.graph['name'], budget), 'rpp-{}_{}'.format(graph.graph['name'], budget), mode=mode) # open with 'w' flag to write over existing file

    file.comment(f'writing an RPP model ')
    file.comment(f'Now: {datetime.datetime.now().astimezone()} ')
    
    file.comment('objective function')
    file.minimize('sum_distance')

    file.comment('sum distances')
    file.write('sum_distance', end=False)
    for s in graph.nodes():
        for (i, j) in graph.edges(): # for set A, we need to to i->j and j->i
            file.write(' - {weight} z_{s}_{i}_{j}'.format(weight=graph[i][j]['weight'], s=s, i=i, j=j), end=False)
            file.write(' - {weight} z_{s}_{j}_{i}'.format(weight=graph[i][j]['weight'], s=s, i=i, j=j), end=False)
    file.write(' = 0')
    
    file.comment('limiting the number of replicas')
    first = True
    for q in graph.nodes():
        if not first:
            file.write(' + ', end=False)
        else:
            first = False
        file.write('r_{q}'.format(q=q), end=False)
    file.write(' = {R}'.format(R=budget))
    
    file.comment('only one DC is the source for every node')
    for s in graph.nodes():
        first = True
        for q in graph.nodes():
            if not first:
                file.write(' + ', end=False)
            else:
                first = False
            file.write('y_{q}_{s}'.format(q=q, s=s), end=False)
        file.write(' = 1')
        
    for s in graph.nodes():
        for q in graph.nodes():
            file.write('y_{q}_{s} - r_{q} <= 0'.format(q=q, s=s))
            
    for s in graph.nodes():
        for i in graph.nodes():
            t_i_s = 1 if s == i else 0
            file.write('y_{i}_{s}'.format(i=i, s=s), end=False)
            for j in graph.neighbors(i):
                file.write(' + z_{s}_{i}_{j} - z_{s}_{j}_{i}'.format(s=s, i=i, j=j), end=False)
            file.write(' = {t}'.format(t=t_i_s))
    file.comment('defining the bounds')
    file.bounds()
    binary_variables = ''
    for q in graph.nodes():
        binary_variables += ' r_{q}'.format(q=q)
        for s in graph.nodes():
            binary_variables += ' y_{q}_{s}'.format(q=q, s=s)
        for (i, j) in graph.edges():
            binary_variables += ' z_{s}_{i}_{j}'.format(s=q, i=i, j=j)
            binary_variables += ' z_{s}_{j}_{i}'.format(s=q, i=i, j=j)
    file.binary_variables(binary_variables)
    file.close()
    
    variables_rpp = file.solve()

    print('done')
    print('found', len(variables_rpp), 'variables in the solution')
    return variables_rpp

def clsd(graph, variables_rpp, p):
    topology = graph.graph['name']
    file = ModelFile(f'./models/clsd-{topology}_{p}', f'clsd-{topology}_{p}', mode=mode) # open with 'w' flag to write over existing file

    file.comment(f'writing a CLSD model for p={p}')
    file.comment('Now: {}'.format(datetime.datetime.now().astimezone()))

    file.comment('objective function')
    file.minimize('sum_connected')

    # (10)
    file.comment('sum distances for (10)')
    file.write('sum_connected', end=False)
    for i in graph.nodes(): # for all nodes
        if variables_rpp[f'r_{i}'] == 0: # if node is not in the set of replicas
            file.write(f' - v_{i}', end=False)
    file.write(' = 0')
    
    # (11)
    file.comment('ensuring p (11)')
    first = True
    for i, j in graph.edges(): # for set E, i < j
        if first:
            first = False
        else:
            file.write(' + ', end=False)
        file.write(f'x_{i}_{j}', end=False)
    file.write(f' = {p}')
    
    # (12)
    for i,j in graph.edges():
        file.write(f'u_{i}_{j} + x_{i}_{j} >= 1')
    
    # (13)
    file.comment('guarantee that non-adjascent nodes i and j are connected if there exists a node k that is connected to both')
    for i in graph.nodes():
        for j in graph.nodes():
            if int(i) < int(j) and not graph.has_edge(i, j):
                if graph.degree(i) <= graph.degree(j):
                    v_ij = graph.neighbors(i)
                else:
                    v_ij = graph.neighbors(j)

                for k in v_ij:
                    if int(k) > int(j):
                        file.write(f'u_{i}_{k} + u_{j}_{k} - u_{i}_{j} <= 1')
                    elif int(k) > int(i):
                        file.write(f'u_{i}_{k} + u_{k}_{j} - u_{i}_{j} <= 1')
                    else:
                        file.write(f'u_{k}_{i} + u_{k}_{j} - u_{i}_{j} <= 1')
    
    # (14) and (15)
    for i in graph.nodes():
        for j in graph.nodes():
            if int(i) < int(j) and variables_rpp[f'r_{i}'] == 0 and variables_rpp[f'r_{j}'] == 1: # set F such that j in D
                file.write(f'u_{i}_{j} - v_{i} <= 0')
            if int(i) < int(j) and variables_rpp[f'r_{i}'] == 1 and variables_rpp[f'r_{j}'] == 0: # set F such that i in D
                file.write(f'u_{i}_{j} - v_{j} <= 0')
    
    file.bounds()
    file.int_variables('sum_connected')
    binary_variables = ''
    for i,j in graph.edges():
        binary_variables += f' x_{i}_{j}'
    for i in graph.nodes(): # for all nodes
        if variables_rpp[f'r_{i}'] == 0: # if node is not in the set of replicas
            binary_variables += f' v_{i}'
    for i in graph.nodes():
        for j in graph.nodes:
            if int(i) < int(j):
                binary_variables += f' u_{i}_{j}'
    file.binary_variables(binary_variables)
    file.close()
    
    variables_clsd = file.solve()

    print('done for p', p)
    print('found', len(variables_clsd), 'variables in the solution')
    return variables_clsd

def a2tr(cur_graph, original_graph):
    count = 0
    for n1 in original_graph.nodes():
        for n2 in original_graph.nodes():
            if n1 != n2 and n1 in cur_graph.nodes() and n2 in cur_graph.nodes():
                if n2 in nx.algorithms.descendants(cur_graph, n1):
                    count += 1
    return count / (original_graph.number_of_nodes() * (original_graph.number_of_nodes() - 1))

def aca(cur_graph, original_graph):
    count = 0
    for n1 in original_graph.nodes():
        for dc in original_graph.graph['dcs']:
            if n1 != dc and n1 in cur_graph.nodes() and dc in cur_graph.nodes():
                if dc in nx.algorithms.descendants(cur_graph, n1):
                    count += 1
                    break # breaks the DC loop once finds a DC
    return count / original_graph.number_of_nodes()

    