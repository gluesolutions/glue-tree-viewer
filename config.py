import numpy as np

from glue.core.component import CategoricalComponent
from glue.core.component_id import ComponentID
from glue.core.data import BaseCartesianData, Data
from glue.utils import view_shape
import ete3
import viewer
from glue import qglue
from glue.core.data_factories.helpers import has_extension
from glue.config import data_factory, link_function, link_helper
from glue.core.link_helpers import LinkCollection


# linking info
# http://docs.glueviz.org/en/stable/developer_guide/linking.html
def tree_process(fname):
    import os

    result = Data()
    result.label = "tree data[%s]" % os.path.basename(fname)

    tree = ete3.Tree(fname, format=0)
    result.tdata = tree

    result.tree_component_id = "tree nodes %s" % result.uuid

    nodes = np.array([n.name for n in tree.traverse("postorder")])

    result.add_component(CategoricalComponent(nodes), result.tree_component_id)

    return result


def tree_process_bad(fname):
    tree = ete3.Tree(fname, format=1)
    data = TreeData(tree)
    return data

# {A} goal: make class that can be put into UserDataWrapper spot for the ui so it can be added by helper


class TreeData(Data):
    def __init__(self, tree: "ete3.Tree class"):
        super(TreeData, self).__init__()

        self.data_cid = ComponentID(label="tree data CID", parent=self)

        self.tdata = tree
        self.nodes = np.array([n.name for n in tree.traverse("postorder")])
        self.d = CategoricalComponent(self.nodes, categories=np.unique(self.nodes))

        import uuid

        self.uuid = str(uuid.uuid4())

    @property
    def label(self):
        return "tree data label"

    @property
    def shape(self):
        return self.nodes.shape

    @property
    def main_components(self):
        return [self.data_cid]

    def get_component(self, cid):
        if cid == self.data_cid:
            return self.d
        elif cid in self.pixel_component_ids:
            return self.d
        else:
            assert False

    def get_kind(self, cid):
        return "categorical"

    def get_data(self, cid, view=None):
        print("getting cid", cid)
        if cid in self.pixel_component_ids:
            print("why?", self.pixel_component_ids)
            # return super(TreeData, self).get_data(cid, view=view)
            return self.d.data
        else:
            if cid == self.data_cid:
                return self.d.data
            else:
                print("asked for cid i dont have", cid)
                return self.d.data

    def get_mask(self, subset_state, view=None):
        mask = subset_state.to_mask(self, view=view)
        return mask

    def compute_statistic(
        self,
        statistic,
        cid,
        axis=None,
        finite=True,
        positive=False,
        subset_state=None,
        percentile=None,
        random_subset=None,
    ):
        return 4.0

    def compute_histogram(
        self,
        cid,
        range=None,
        bins=None,
        log=False,
        subset_state=None,
        subset_group=None,
    ):
        return np.random.random(bins) * 100


@data_factory("Newick tree loader", identifier=has_extension("tre nw"), priority=1000)
def read_newick(fname):
    # TODO how to give user option to choose format?
    return tree_process(fname)


# https://github.com/glue-viz/glue/blob/241edb32ab6f4a82adf02ef3711c16342fd214ed/glue/plugins/dendro_viewer/qt/data_viewer.py#L92


@link_helper(category='Tree Viewer')
class Link_Index_By_Value(LinkCollection):
    # inherit from linkCollection to skip this line https://github.com/glue-viz/glue/blob/5a878451a1636b141a687a482239a37287a32198/glue/config.py#L790
    cid_independent = False

    display = 'Link By Value'
    description = 'WARNING: once you close this dialog, this link can only be removed by restarting glue'

    labels1 = ['first value column']
    labels2 = ['second value column']

    _links = []

    def __init__(self, *args, cids1=None, cids2=None, data1=None, data2=None):
        # only support linking by one value now, even tho link_by_value supports multiple
        assert len(cids1) == 1
        assert len(cids2) == 1

        self.data1 = data1
        self.data2 = data2
        self.cids1 = cids1
        self.cids2 = cids2

        data1.join_on_key(data2, cids1[0], cids2[0])

# based on https://sourcegraph.com/github.com/glue-viz/glue/-/blob/glue/plugins/coordinate_helpers/link_helpers.py?L42:33
