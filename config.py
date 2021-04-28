import numpy as np

from glue.core.component import CategoricalComponent
from glue.core.component_id import ComponentID
from glue.core.data import BaseCartesianData, Data
from glue.utils import view_shape
import ete3
import viewer
from glue import qglue
from glue.core.data_factories.helpers import has_extension
from glue.config import data_factory, link_function


@link_function(info="Link from tree data object to an ID string column", output_labels=['string'])
def node_to_string(node):
    return node.name
    



# linking info
# http://docs.glueviz.org/en/stable/developer_guide/linking.html
def tree_process(fname):
    result = Data()
    result.label = 'tree data'
    tree = ete3.Tree(fname)
    result.tdata = tree

    nodes = np.array([n.name for n in tree.traverse("postorder")])

    result.add_component(CategoricalComponent(nodes), 'tree nodes')
    
    return result
    



@data_factory("Newick tree loader", identifier=has_extension('tre nw'))
def read_newick(fname):
    # TODO how to give user option to choose format?
    return tree_process(fname)
