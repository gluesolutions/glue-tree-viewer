import numpy as np

from glue.core.component_id import ComponentID
from glue.core.data import BaseCartesianData
from glue.utils import view_shape
import ete3
import viewer
from glue import qglue


# QUESTION
# TODO Change this class to inherit from BaseData, so that it doesn't have to shim (?)
# into Cartesian api
# (second paragrpah of http://docs.glueviz.org/en/stable/developer_guide/data.html)
class TreeData(BaseCartesianData):
    def __init__(self, *args, **kwargs):
        super(TreeData, self).__init__()
        self.data_cid = ComponentID(label='tree data componentid label', parent=self)
        self.tdata = ete3.Tree(*args, **kwargs)

    @property
    def label(self):
        return "Tree Data label"

    @property
    def shape(self):
        return (42,)

    @property
    def main_components(self):
        # only one component for now
        return [self.data_cid]

    def get_kind(self, cid):
        # QUESTION
        # one of 'numerical' => number?, 'categorical' => string, 'datetime' =>np.datetime64
        #        , 'tree' = ete3.Tree ??

        # http://etetoolkit.org/docs/latest/tutorial/tutorial_trees.html#reading-newick-trees
        return 'tree'

    def get_data(self, cid, view=None):
        # note: view is a slice of a numpy array. does not really apply to tree data

        if view is not None:
            # QUESTION
            return Exception('trees do not support numpy indexing')

        #if cid in self.pixel_component_ids:
            #return super(TreeData, self).get_data(cid, view=view)
        #else:
            #return np.random.random(view_shape(self.shape, view))

        raise Exception('tree data is not numpy data')

    def get_mask(self, subset_state, view=None):
        return subset_state.to_mask(self, view=view)

    def compute_statistic(self, statistic, cid,
                          axis=None, finite=True,
                          positive=False, subset_state=None,
                          percentile=None, random_subset=None):

        raise Exception('tree data statistic operations not yet defined')

    def compute_histogram(self ,cid, range=None, bins=None, log=False,
                          subset_state=None, subset_group=None):

        raise Exception('tree data histogram not yet defined')

    def get_ete_tree(self):
        return self.tdata

    
from glue.config import data_factory

def is_newick(fname, **kwargs):
    return filename.endswith('nw')

@data_factory('Newick tree loader', is_newick)
def read_newick(fname):
    return TreeData(fname, format=3)
