import numpy as np
from nansat import Nansat, Domain
from boreali import Boreali, lm
import csv
import os


def get_r(obj, coords, wavelens):
    y, x = coords
    band_numbers = list(map(lambda x: obj._get_band_number('Rrs_' + str(x)), wavelens))
    rrs_list = np.array([obj[band][y][x] for band in band_numbers])
    rrsw_list = rrs_list / (0.52 + 1.7 * rrs_list)

    return rrsw_list


def boreali_lm(obj, wavelens, h, coords, bottom_type=0):
    y, x = coords
    b = Boreali('michigan', wavelens)
    model = b.get_homodel()
    theta = 0
    albedoType = bottom_type
    depth = h[y,x]
    albedo = b.get_albedo([albedoType])[0]

    cpa_limits = [0.01, 3,
                  0.01, 1,
                  0.01, 1, 10]

    r = get_r(obj, (y, x), wavelens)
    c_osw = lm.get_c_shal(cpa_limits, model, [r], [theta], [depth], [albedo], 4)[1]

    return c_osw


dom = Domain('+proj=latlong +datum=WGS84 +ellps=WGS84 +no_defs', '-lle -86.3 44.6 -85.2 45.3 -ts 122 78')

bathymetry = Nansat('./data/michigan_lld.grd')
bathymetry.reproject(dom)

h = bathymetry[1]
h = np.where(h >= 0, np.nan, np.float32(h) * -1)

wavelens = [412, 443, 469, 488, 531, 547, 555, 645, 667, 678]   # All MODIS channels
years = np.arange(2003, 2016)
months = np.array(['may', 'jun', 'sep', 'oct'])
DATA_PATH = '/nfs0/data_ocolor/michigan/data/{0}/{1}/'


with open('1pointdata.csv', 'w') as csvfile1:
    fieldnames = ['img', 'chl', 'tsm', 'doc', 'rmse']
    writer1 = csv.DictWriter(csvfile1, fieldnames=fieldnames)

    with open('2pointdata.csv', 'w') as csvfile2:
        writer2 = csv.DictWriter(csvfile2, fieldnames=fieldnames)

        for year in years:
            for month in months:
                data = list(os.listdir('/nfs0/data_ocolor/michigan/data/%s/%s/' % (year, month)))
                for img in data:
                    n = Nansat('/nfs0/data_ocolor/michigan/data/%s/%s/%s' % (year, month, img))
                    n.reproject(dom)

                    px_1 = boreali_lm(n, wavelens, h, (48, 13), bottom_type=0)
                    writer1.writerow({
                        'img': img,
                        'chl': px_1[0],
                        'tsm': px_1[1],
                        'doc': px_1[2],
                        'rmse': px_1[3]
                    })

                    px_2 = boreali_lm(n, wavelens, h, (60, 16), bottom_type=6)
                    writer2.writerow({
                        'img': img,
                        'chl': px_2[0],
                        'tsm': px_2[1],
                        'doc': px_2[2],
                        'rmse': px_2[3]
                    })
