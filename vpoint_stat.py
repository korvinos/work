# coding: utf-8

from nansat import Nansat
# import matplotlib.pyplot as plt
import numpy as np
import custrepr
import csv


boreali_data_path = '/nfs0/data_ocolor/michigan/tests/boreali_data/'
boreali_osw_data_path = '/nfs0/data_ocolor/michigan/tests/boreali_osw_data_h/'
#months = ['may/', 'jun/', 'sep/', 'oct/']
months = ['may/']
with open('vpoint_stat.csv', 'w') as csvfile:
    fieldnames = ['month', 'file', 'location', 'size', 'good', 'bad', 'deep_chl', 'osw_chl']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    for month in months:
        data_deep_list = sorted(custrepr.get_data_list(boreali_data_path + month + 'cpa/'))
        data_osw_list = sorted(custrepr.get_data_list(boreali_osw_data_path + month + 'cpa/'))

        for el in range(0, len(data_deep_list)):
            print month + data_deep_list[el].split('.')[0]
            n_deep = Nansat(boreali_data_path + month + 'cpa/' + data_deep_list[el])
            n_osw = Nansat(boreali_osw_data_path + month + 'cpa/' + data_osw_list[el])
            regions = {'mp': {'name': 'ManitonPassage',
                              'deep_values': n_deep['chl'][86:134, 14:60],
                              'osw_values': n_osw['chl'][86:134, 14:60]},
                       'gtb': {'name': 'GrandTraverseBay',
                               'deep_values': n_deep['chl'][14:63, 196:264],
                               'osw_values': n_osw['chl'][14:63, 196:264]},
                       'bank': {'name': 'Bank(S.Foxisl.)',
                                'deep_values': n_deep['chl'][0:20, 112:128],
                                'osw_values': n_osw['chl'][0:20, 112:128]}
                       }

            for region in regions.keys():
                data_deep = np.where((np.isnan(regions[region]['deep_values'])) | \
                                     (regions[region]['deep_values'] == np.float64(100)),
                                     np.float64(np.nan), regions[region]['deep_values'])
                data_osw = np.where((np.isnan(regions[region]['osw_values'])) | \
                                    (regions[region]['osw_values'] == np.float64(100)),
                                    np.float64(np.nan), regions[region]['osw_values'])

                boolcount = np.isnan(data_deep)

                writer.writerow({'month': month[:-1],
                                 'file': data_deep_list[el].split('.')[0],
                                 'location': regions[region]['name'],
                                 'size': data_deep.size,
                                 'good': np.count_nonzero(boolcount == False),
                                 'bad': np.count_nonzero(boolcount == True),
                                 'deep_chl': np.nanmean(data_deep),
                                 'osw_chl': np.nanmean(data_osw)
                                 })