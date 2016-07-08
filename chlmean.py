from nansat import Nansat, Domain
import matplotlib.pyplot as plt
import numpy as np


n_osw = Nansat('/home/artemm/Desktop/A2014301181500.L2_LAC_OC.x.nccpa_OSW.nc')
n_deep = Nansat('/home/artemm/Desktop/A2014301181500.L2_LAC_OC.x.nccpa_deep.nc')
bottom = Nansat('/home/artemm/Desktop/michigan_lld.grd')

dom = Domain('+proj=latlong +datum=WGS84 +ellps=WGS84 +no_defs', '-lle -86.3 44.6 -85.2 45.3 -ts 300 200')
bottom.reproject(dom)
h = np.copy(bottom[1])
h[np.where(h > np.float32(0.0))] = np.nan
h[np.where(h < np.float32(0.0))] *= np.float32(-1)
"""
test = np.copy(n_osw['chl'])
test[np.where(h <= -20)] = np.nan
plt.imshow(test)
plt.show()
pass
"""

osw_h_mean = []
deep_h_mean = []
for h_max in range(1, np.nanmax(h), 1):
    osw = np.copy(n_osw['chl'])
    deep = np.copy(n_deep['chl'])
    osw[np.where(h >= h_max)] = np.nan
    deep[np.where(h >= h_max)] = np.nan
    osw_h_mean.append(np.nanmean(osw))
    deep_h_mean.append(np.nanmean(deep))

h_marks = range(1, np.nanmax(h), 1)
plt.plot(h_marks, osw_h_mean, h_marks, deep_h_mean)
plt.legend()
plt.show()


print osw_h_mean
print deep_h_mean