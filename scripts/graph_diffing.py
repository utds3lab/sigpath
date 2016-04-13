#!/usr/bin/env python
"""
Created on May 23, 2013

Author: David I. Urbina
"""

# imports
from __future__ import print_function
import logging
import sys

from docopt import docopt
import matplotlib.pyplot as plt
import networkx as nx

from keyedset import KeyedSet
from segments import Stack
import graph_generator
import memorydump


# constants
__version__ = 1.0
search_paths = nx.all_shortest_paths
# search_paths = nx.all_simple_paths

# exception classes


# interface functions

def diff_memory_graphs(graphs, neggraph=None):
    diffing = _diff_memory_graphs(graphs)

    if neggraph:
        intersec2 = _diff_memory_graphs([graphs[-1], neggraph])

    return diffing


def extract_diff_graph(graph, diff):
    diff_graph = graph.copy()
    diff_graph.root_nodes = list()

    #     pnodes = collections.defaultdict(set)
    #     for m in diff[0] | diff[2]:
    #         for n in diff_graph.nodes():
    #             if nx.has_path(diff_graph, n, m):
    #                 pnodes[m].add(n)
    #
    #     nodes = set.union(*pnodes.values())
    nodes = set()
    logging.debug('Searching on-paths nodes...')
    for m in graph.root_nodes:
        for i in diff[0] | diff[2]:
            if m == i:
                nodes.add(m)
            try:
                nodes.update(*list(search_paths(diff_graph, m, i)))
            except:
                pass
        if m in nodes:
            diff_graph.root_nodes.append(m)

    logging.debug('Removing nodes off-path...')
    for n in diff_graph.nodes()[:]:
        if n not in nodes:
            diff_graph.remove_node(n)
    logging.debug('Setting node colors...')
    for n in diff_graph.nodes():
        diff_graph.node[n]['color'] = 'turquoise'
    for n in diff[0]:
        diff_graph.node[n]['color'] = 'red'
        if isinstance(n, Stack):
            diff_graph.node[n]['color'] = 'deeppink'
    for n in diff[2]:
        diff_graph.node[n]['color'] = 'green'
    logging.debug('Exporting diff_graph.dot...')
    nx.write_dot(diff_graph, 'diff_graph.dot')
    return diff_graph

# internal classes


# internal functions

def _diff_memory_graphs(graphs):

#     pool = mp.Pool()
    pairs = []
    for i in xrange(len(graphs) - 1):
        pairs.append((graphs[i], graphs[i + 1]))

    diffing = map(_diff_pair_memory_graphs, pairs)

    if len(diffing) == 1:
    #         _draw_graph_diffing(graphs[0], graphs[1], diffing[0])
        return (diffing[0][1], diffing[0][2], diffing[0][3])
    else:
        keyedsets1 = list()
        keyedsets2 = list()
        keyedsets3 = list()
        for diff in diffing:
            keyedsets1.append(KeyedSet(diff[1], key=lambda seg: str(seg)))
            keyedsets2.append(KeyedSet(diff[2], key=lambda seg: str(seg)))
            keyedsets3.append(KeyedSet(diff[3], key=lambda seg: str(seg)))

        changed = keyedsets1[0]
        for ks in keyedsets1:
            changed = changed & ks

        removed = keyedsets2[0]
        for ks in keyedsets2:
            removed = removed | ks

        added = keyedsets3[0]
        for ks in keyedsets3:
            added = added | ks

        added = added - removed
        last_md = set(graphs[-1].nodes())
        added = added & KeyedSet(last_md, key=lambda seg: str(seg))

    return changed, removed, added


def _diff_pair_memory_graphs(graph_tuple):
    graph1 = graph_tuple[0]
    graph2 = graph_tuple[1]
    diff_nodes1 = set(graph1.nodes()) - set(graph2.nodes())
    diff_nodes2 = set(graph2.nodes()) - set(graph1.nodes())
    diff_nodes1 = KeyedSet(diff_nodes1, key=lambda buf: str(buf))
    diff_nodes2 = KeyedSet(diff_nodes2, key=lambda buf: str(buf))
    changed_nodes2 = diff_nodes1 & diff_nodes2
    changed_nodes1 = diff_nodes2 & diff_nodes1
    removed_nodes = diff_nodes1 - changed_nodes1
    added_nodes = diff_nodes2 - changed_nodes2
    return (set(changed_nodes1), set(changed_nodes2), set(removed_nodes),
            set(added_nodes))

#     return set([]), set([]), set([]), set([])


def _draw_graph_diffing(graph1, graph2, differences):
    plt.subplot(121)
    pos = nx.pygraphviz_layout(graph1, prog='dot')
    nx.draw_networkx_nodes(graph1, pos,
                           graph1.nodes(), node_color='b', node_size=200)
    nx.draw_networkx_nodes(graph1, pos, differences[0],
                           node_color='r', node_size=600)
    nx.draw_networkx_nodes(graph1, pos, differences[2],
                           node_color='y', node_size=600)
    nx.draw_networkx_edges(graph1, pos, graph1.edges())
    nx.draw_networkx_labels(graph1, pos, font_size=8)
    plt.title('Graph 1')
    plt.axis('off')
    plt.subplot(122)
    pos = nx.pygraphviz_layout(graph2, prog='dot')
    nx.draw_networkx_nodes(graph2, pos, graph2.nodes(), node_color='b',
                           node_size=200)
    nx.draw_networkx_nodes(graph2, pos, differences[1], node_color='r',
                           node_size=600)
    nx.draw_networkx_nodes(graph2, pos, differences[3], node_color='g',
                           node_size=600)
    nx.draw_networkx_edges(graph2, pos, graph2.edges())
    nx.draw_networkx_labels(graph2, pos, font_size=8)
    plt.title('Graph 2')
    plt.axis('off')
    lr = plt.Circle((0, 0), 5, fc='r')
    lb = plt.Circle((0, 0), 5, fc='b')
    lg = plt.Circle((0, 0), 5, fc='g')
    ly = plt.Circle((0, 0), 5, fc='y')
    plt.legend([lb, lr, lg, ly], ['No changed', 'Changed', 'Added',
                                  'Removed'], loc=4)
    #     plt.savefig(graph1.name + '-' + graph2.name + '.png')
    plt.show()


def _process_cmd_line(argv):
    """Memory graph diffing.

Usage:
    graph_diffing.py [--verbose] <dump>... [-n <neg_dump>]
    graph_diffing.py (--help | --version)

Options:
    <dump>         The list of positive memory dumps.
    -n <neg_dump>  The negative memory dump.
    -h --help      Shows this message.
    -v --verbose   Shows details.
    --version      Shows the current version.
    """
    # initializing the parser object
    args = docopt(_process_cmd_line.__doc__, argv=argv, version=__version__)

    # checking arguments
    if args['--verbose']:
        print(args)
    return args['<dump>'], args['-n'], args['--verbose']


def main(argv=None):
    dumpfiles, neg_filename, verbose = _process_cmd_line(argv)
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    logging.debug('Loading positive memory dumps...')
    dumps = map(memorydump.load_memory_dump, dumpfiles)
    graphs = map(graph_generator.generate_graph, dumps)

    if neg_filename:
        logging.debug('Loading negative memory dump...')
        negdump = memorydump.load_memory_dump(neg_filename)
        neggraph = graph_generator.generate_graph(negdump)
        diffing = diff_memory_graphs(graphs, neggraph)
    else:
        diffing = diff_memory_graphs(graphs)

    print('Changed nodes: {}'.format(len(diffing[0])))
    print('Removed nodes: {}'.format(len(diffing[1])))
    print('Added nodes: {}'.format(len(diffing[2])))

    extract_diff_graph(graphs[-1], diffing)
    logging.info('diff_graph.dot created')

    return 0


if __name__ == '__main__':
    sys.exit(main())
