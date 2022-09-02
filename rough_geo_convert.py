# This python script reads in a self-similar topography map and convert it to rough fault geometry at designated resolution.

import csv 
import numpy as np 

res = 50 # in meters
file_path = 'rough_fault/rough_geo.txt'

meta_row = [0,1]
with open(file_path, 'r') as ld:
  reader = csv.reader(ld)
  result = [[int(s) for s in row] for i,row in enumerate(reader) if i in meta_row]
print(np.array(result))
#topo_meta = np.loadtxt("rough_fault/rough_geo.txt" , userows = 1);
topo = np.loadtxt("rough_fault/rough_geo.txt" , skiprows = 2, dtype = 'float');
print(topo) 