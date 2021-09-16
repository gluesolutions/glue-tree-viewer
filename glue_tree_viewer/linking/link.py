# https://www.treelinkapp.com/manual.html
# start with the csv/tre data
# eventaully add this type of data?? probably not me
# https://www.treelinkapp.com/exdata/hiv-db2006.fasta

import pandas as pd
import ete3
from collections import defaultdict

data = pd.read_csv("data.csv")

tree = ete3.Tree("data.tre")

counts = defaultdict(int)

for nde in tree:
    lookup = data[data["ID Key"] == nde.name]
    rows, _ = lookup.shape
    counts[rows] += 1
counts
