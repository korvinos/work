import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as imread
from nansat import Nansat, Domain, Mosaic
from boreali import Boreali, lm
import pandas as pd
import csv

with open('test1.csv', 'w') as csvfile:
    fieldnames = ['coordinates', 'alg_type', 'h', 'chl', 'tsm', 'doc', 'rmse']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    for el in positive_px:
        osw, deep, depth = boreali_lm(test1, wavelens_base, h, el)
        writer.writerow({
            'coordinates': el,
            'alg_type': 'osw',
            'h': round(depth, 2),
            'chl': round(osw[0], 2),
            'tsm': round(osw[1], 2),
            'doc': round(osw[2], 2),
            'rmse': round(osw[3], 2)
        })

        writer.writerow({
            'coordinates': el,
            'alg_type': 'deep',
            'h': round(depth, 2),
            'chl': round(deep[0], 2),
            'tsm': round(deep[1], 2),
            'doc': round(deep[2], 2),
            'rmse': round(deep[3], 2)
        })