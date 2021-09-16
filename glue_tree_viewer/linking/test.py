# goal, to find what the random distrobution looks like with my bucketing method
# graph in 3d using glue, 3rd dimension is randomness.

import random


def sample_one_point(randomness):
    if randomness == 1.0:
        return -1
    idx = 0
    while True:
        if random.random() > randomness:
            return idx
        else:
            idx += 1


from collections import OrderedDict


def sample_n_points(n, randomness):
    counter = OrderedDict()
    for _ in range(n):
        idx = sample_one_point(randomness)
        counter[idx] = counter.get(idx, 0) + 1

    return counter


alldata = {}

for n, randomness in enumerate(np.linspace(0.1, 1.0, 10, endpoint=False)):
    data = sample_n_points(1000, randomness)
    alldata[randomness] = data
    largest = max(max(data.keys()) for data in alldata.values())

xs = []
ys = []
zs = []
for n in alldata.keys():
    for i in range(largest):
        xs.append(n)
        ys.append(i)
        zs.append(alldata[n].get(i, 0))

import pandas as pd
from pandas import DataFrame
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

threedee = plt.figure().gca(projection="3d")
threedee.scatter(xs, ys, zs)
threedee.set_xlabel("randomness")
threedee.set_ylabel("idx")
threedee.set_zlabel("how frequent")
plt.show()
