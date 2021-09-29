import numpy as np

from glue.core.component import CategoricalComponent
from glue.core.component_id import ComponentID
from glue.core.data import BaseCartesianData, Data
from glue.utils import view_shape
from glue.core.component_link import KeyLink

import ete3
#from .viewer import TreeLayerState #Do we need this?
from glue import qglue
from glue.core.data_factories.helpers import has_extension
from glue.config import data_factory, link_function, link_helper
from glue.core.link_helpers import LinkCollection
from glue.core.data_factories.helpers import data_label


def find_type(string):
    if string == '':
        return None

    if string.isnumeric():
        return int

    try:
        float(string)
        return float
    except ValueError:
        return str
    

def determine_format(fname):
    # formats described here
    # http://etetoolkit.org/docs/latest/tutorial/tutorial_trees.html#reading-and-writing-newick-trees

    # default to format=1, unless file has support values instead of internal
    # node names.

    t = ete3.Tree(fname, format=1)
    leaf_types = set(find_type(n.name) for n in t.traverse() if n.is_leaf())

    parent_types = set(find_type(n.name) for n in t.traverse() if not n.is_leaf())

    if len(leaf_types) != 1:
        # maybe revert to just str in this case?
        raise Exception('could not load tree, leaves are not homogenous types')

    if None in parent_types:
        parent_types.remove(None)

    if leaf_types != parent_types and parent_types == set([float]):
        # we have detected structure values, format 0 is correct
        return 0
    else:
        # no structures detected, use 1 (internal node names)
        return 1


        

# linking info
# http://docs.glueviz.org/en/stable/developer_guide/linking.html
def tree_process(newickstr, title):
    import os

    #result = Data(newickstr=[newickstr])
    result = Data()

    result.label = "%s [tree data]" % title

    tree = ete3.Tree(newickstr, format=determine_format(newickstr))
    result.tdata = tree

    result.tree_component_id = "tree nodes %s" % result.uuid

    # ignore nameless nodes as they cannot be indexed
    names = [n.name for n in tree.traverse("postorder") if n.name != ""]

    allint = all(name.isnumeric() for name in names)

    nodes = np.array([(int(name) if allint else name) for name in names])

    for node in tree.traverse("postorder"):
        if allint:
            node.idx = int(node.name) if node.name != "" else None
        else:
            node.idx = node.name

    result.add_component(CategoricalComponent(nodes), result.tree_component_id)

    return result


@data_factory("Newick tree loader", identifier=has_extension("tre nw"), priority=1000)
def read_newick(fname):
    # TODO how to give user option to choose format?
    with open(fname) as f:
        contents = f.read()
        return tree_process(contents, data_label(fname))

import glue.plugins.dendro_viewer.data_factory as df


@data_factory("Tree Dendogram", identifier=df.is_dendro, priority=1001)
def read_dendro(fname):
    def to_newick_str(dg):
        return "(" + ",".join(x.newick for x in dg.trunk) + ");"

    from astrodendro import Dendrogram

    label = data_label(fname)

    dg = Dendrogram.load_from(fname)

    tree = tree_process(to_newick_str(dg), label)

    im = Data(
        intensity=dg.data, structure=dg.index_map, label="{} [data]".format(label)
    )

    im.join_on_key(tree, "structure", tree.tree_component_id)

    return [tree, im]


# https://github.com/glue-viz/glue/blob/241edb32ab6f4a82adf02ef3711c16342fd214ed/glue/plugins/dendro_viewer/qt/data_viewer.py#L92


@link_helper(category="Link by ID")
class Link_Index_By_Value(LinkCollection):
    # inherit from linkCollection to skip this line https://github.com/glue-viz/glue/blob/5a878451a1636b141a687a482239a37287a32198/glue/config.py#L790
    cid_independent = False

    display = "Link by ID"
    description = "Link two datasets by a common ID (for example, if two datasets have the same experiment ID)"

    labels1 = ["first value column"]
    labels2 = ["second value column"]

    

    def __init__(self, *args, cids1=None, cids2=None, data1=None, data2=None):
        # only support linking by one value now, even tho link_by_value supports multiple
        assert len(cids1) == 1
        assert len(cids2) == 1

        self.data1 = data1
        self.data2 = data2
        self.cids1 = cids1
        self.cids2 = cids2

        data1.join_on_key(data2, cids1[0], cids2[0])
        
        self._links = [KeyLink()]
        
        


# based on https://sourcegraph.com/github.com/glue-viz/glue/-/blob/glue/plugins/coordinate_helpers/link_helpers.py?L42:33
