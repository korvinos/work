# coding:utf-8
"""
Набор функций для перепроецирования, осреднения и дальнейшей обработки по boreali и boreali_osw
Перепроецирование файлов снимков производится функцией make_reproject
Осредение make_average
Для обработки boreali есть функции boreali_processing и boreali_osw_processing соответственно
За подробностями см. описания функций
"""
import os
from nansat import Nansat, Domain, mosaic
import matplotlib.pyplot as plt
import numpy
from boreali import Boreali, lm
import scipy


def create_mask_beta(obj, show='off'):

    """
    Маска, которая оставляет только те пиксели, которые на всех каналах имеют положительные значения Rrs
    Создание маски происходит следующим образом:

        1. Cоздается булева маска (mask_bool) с размерностью поступаещего снимка заполненная значениями True и схожая с
        ней по размерности нулевая матрица (mask) на осно которой и будет после построена конечная маска
        2. Происходит умножение исходной маски (п.1) на масскив каждого банда с проверкой на отрицетальные значения.
        Таким образом, после перемножения всех каналов, значения True останультся только в точках, для которых со всех
        каналов поступило положительное значение Rrs;
        3. Происходит генерация конечной маски: если значение точки в конечной булевой маске mask_bool[i][j] == True,
        то mask[i][j] == 64.0, иначе без изменений
        4. Новая маска добавляется в исходный объект

    :param obj: Nansat объект
    :param show: Флаг для отрисовки маски. По умолчанию 'off', чтобы включить show='on'
    :return: Nasat объект с добавленным в него бандом 'mask_beta', где: 64.0 - хорошие значения (положительные на всех
    каналах), а 0.0 - плохие значения (т.е. хотя бы один канал имел Rrs < 0)
    """

    size = obj[2].shape
    mask_bool = numpy.zeros((size[0], size[1])) == 0
    mask = numpy.zeros((size[0], size[1]))
    count_bands = len(obj.bands())

    for band in range(1, count_bands):
        mask_bool *= (obj[band] > 0)

    if scipy.any(mask):
        print 'There are good values in the mask'

    for line in range(0, len(mask_bool)):
        for row in range(0, len(mask_bool[0])):
            if mask_bool[line][row] == numpy.bool_(True):
                mask[line][row] = 64
            else:
                mask[line][row] = 0
    if show == 'on':
        plt.imshow(mask)
        plt.show()

    obj.add_band(array=mask, parameters={'name': 'mask_beta'})
    print 'The new \'mask_beta\' was successfully added to Nansat object as band: '\
          + str(obj._get_band_number('mask_beta'))
    return obj


def create_mask(obj, show='off'):

    """
    Маска, в которой все элементы котоые в исходном файле помечены как no data, т.е. значениями -0.015534, помечаются
    как плохие, а все остальные, без учета отрицательного Rrs помечаются как хорошие
        1. Создается (mask) копия массива из второго банда (первый банд содержащий Rrs)
        2. Выполняется проверка в ходе которой все значения mask[i][j] == -0.015534 заменяются на флаг плохих значений
        (0.0), а все остальные на флаг хороших (64.0)
        3. Новая маска добавляется в исходный объект
    :param obj: Nansat объект
    :param show: Флаг для отрисовки маски. По умолчанию 'off', чтобы включить show='on'
    :return: Nansat объект с добавленным в него бандом 'mask', где: 64.0 - хорошие значения (не равные -0.015534),
    а 0.0 - плохие значения (т.е. равные -0.015534)
    """

    mask = numpy.copy(obj[2])
    for line in range(0, len(mask)):
        for row in range(0, len(mask[0])):
            if mask[line][row] == numpy.float32(-0.015534):
                mask[line][row] = 0
            else:
                mask[line][row] = 64.0

    obj.add_band(array=mask, parameters={'name': 'mask'})

    print 'The new \'mask\' was successfully added to Nansat object as band: ' + str(obj._get_band_number('mask'))

    if show == 'on':
        plt.imshow(obj[obj._get_band_number('mask')])
        plt.colorbar()
        plt.show()
    return obj


def get_data_list(path):
    return list(os.listdir(path))


def group(lst, n):
    # Хороший инструмент для разбиения на равные отрезки + отрезок остатков (в данном коде не используется)
    return [lst[i:i + n] for i in range(0, len(lst), n)]


def group_beta(lst, n):
    """
    Функция, которая разбивает заданный список элементов на подсписки нужной длины.
    В данном случае, ключом для проверки является день года (начиная с наименьшего в списке)
    т.е. При имени файла А2015274.* ключем будет 274 или соовтетственно диапазон символов имени с 5 по 8
    :param lst: Список содержащий значения осреднения
    :param n: Интервал осреднения
    :return: Словарь, где ключ [Ayyyyd1d1d1d2d2d2.datatype] год yyyy, первый d1 и последний d2 день периода осреднения,
                а значение list имен файлов.
    """
    data_list = sorted(lst)
    first_day = int(data_list[0][5:8])    # В имени файла номер дня в году лежит между этими двумя индексами
    last_day = first_day + n - 1
    # тут все плохо
    year = data_list[0][:5]
    file_type = data_list[0][14:]
    result = {}
    current = []  # Сюда накапливаем Значения для текущего временного отрезка
    for image in data_list:
        if first_day <= int(image[5:8]) <= last_day:
            current.append(image)
        else:
            result[year + str(first_day) + str(last_day) + file_type] = current
            current = []
            current.append(image) # Добавляем снимок который не удовлетворил условию уже в следующий интервал
            # Двигаем границы временного интервала вправо
            first_day = last_day + 1
            last_day += n
    result[year + str(first_day) + str(last_day) + file_type] = current  # Добавляем последний интервал
    return result


def make_reproject(path, final_path, file_name, show='off'):
    """
    Функция для перепроецирования снимков согласно параметрам указываемым в dom.
    После перепроецирования к файлу снимку генерируется и добавляется маска
    :param path: Путь до папки в которой лежит файл
    :param final_path: Путь до папки в которую нужно положить перепроецированный файл
    :param file_name: Имя файла (исходного)
    :param show: Флаг для отрисовки [2] канала. По умолчанию 'off', чтобы включить show='on'
    :return: Перепроецированный файл с иходным file_name
    """
    print path + file_name
    nansat_obj = Nansat(path + file_name)
    #  Для маленького конечного куска
    dom = Domain('+proj=latlong +datum=WGS84 +ellps=WGS84 +no_defs', '-lle -86.20 45.10 -86.10 45.20 -ts 300 300')
    #   Для всего района
    #dom = Domain('+proj=latlong +datum=WGS84 +ellps=WGS84 +no_defs', '-lle -86.3 44.6 -85.2 45.3 -ts 300 200')
    nansat_obj.reproject(dom)
    nansat_obj = create_mask(nansat_obj)

    if show == 'on':
        plt.imshow(nansat_obj[2])
        plt.colorbar()
        plt.show()

    nansat_obj.export(final_path + file_name + '.reproject.nc')


def make_average(path, final_path, period=7):
    """
    Осреднение снимков за произвольный период (по умолчанию 7 дней)
    :param path:
    :param final_path: Путь для сохранения файлов
    :param period: Период осреднения. по умолчанию 7 дней
    :return: Осредненный за period снимок
    """
    data_list = sorted(get_data_list(path))
    weekly_data = group_beta(data_list, period)
    for week, week_data in weekly_data.items():
        print '\n' + 'Average data: ' + week + '\n'
        full_name_data_list = list(map(lambda name: path + name, week_data)) # получаем список абсолютных путей к файлам
        nansat_obj = Nansat(full_name_data_list[0])
        mosaic_obj = mosaic.Mosaic(domain=nansat_obj)
        mosaic_obj.average(full_name_data_list, [2, 3, 4, 5, 6, 7, 8, 9, 10, 11], doReproject=False, maskName='mask', threads=2)
        mosaic_obj.export(final_path + week + '.mosaic.nc')


def boreali_processing(obj, final_path):
    wavelen = [412, 443, 469, 488,
               531, 547, 555,
               645, 667, 678]
    cpa_limits = [0.01, 2,
                 0.01, 1,
                 0.01, 1, 10]
    b = Boreali('michigan', wavelen)

    n = Nansat(obj)
    dom = Domain('+proj=latlong +datum=WGS84 +ellps=WGS84 +no_defs', '-lle -86.3 44.6 -85.2 45.3 -ts 300 200')
    n.reproject(dom)
    theta = numpy.zeros([200, 300])

    custom_n = Nansat(domain=n)
    band_rrs_numbers = list(map(lambda x: n._get_band_number('Rrs_' + str(x)),
                                wavelen))

    for index in range(0, len(wavelen)):
        # Преобразуем в Rrsw
        rrsw = n[band_rrs_numbers[index]] / (0.52 + 1.7 * n[band_rrs_numbers[index]])
        custom_n.add_band(rrsw, parameters={'name': 'Rrsw_' + str(wavelen[index]),
                                            'units': 'sr-1',
                                            'wavelength': wavelen[index]})
    cpa = b.process(custom_n, cpa_limits, theta=theta, threads=4)

    custom_n.add_band(array=cpa[0], parameters={'name': 'chl', 'long_name': 'Chlorophyl-a', 'units': 'mg m-3'})
    custom_n.add_band(array=cpa[1], parameters={'name': 'tsm', 'long_name': 'Total suspended matter', 'units': 'g m-3'})
    custom_n.add_band(array=cpa[2], parameters={'name': 'doc', 'long_name': 'Dissolved organic carbon', 'units': 'gC m-3'})
    custom_n.add_band(array=cpa[3], parameters={'name': 'mse', 'long_name': 'Root Mean Square Error', 'units': 'sr-1'})
    custom_n.add_band(array=cpa[4], parameters={'name': 'mask', 'long_name': 'L2 Boreali mask', 'units': '1'})

    custom_n.export(final_path + obj.split('/')[-1] + 'cpa_deep.nc')

    figParams = {'legend': True, 'LEGEND_HEIGHT': 0.5, 'NAME_LOCATION_Y': 0, 'mask_array': cpa[4],
                 'mask_lut': {1: [255, 255, 255], 2: [128, 128, 128], 4: [200, 200, 255]}}
    custom_n.write_figure(final_path + obj.split('/')[-1] + 'chl_deep.png', 'chl', clim=[0, 1.], **figParams)
    custom_n.write_figure(final_path + obj.split('/')[-1] + 'tsm_deep.png', 'tsm', clim=[0, 1.], **figParams)
    custom_n.write_figure(final_path + obj.split('/')[-1] + 'doc_deep.png', 'doc', clim=[0, .2], **figParams)
    custom_n.write_figure(final_path + obj.split('/')[-1] + 'mse_deep.png', 'mse', clim=[1e-5, 1e-2], logarithm=True, **figParams)
    n.write_figure(final_path + obj.split('/')[-1] + 'rgb_deep.png', [16, 14, 6], clim=[[0, 0, 0],
                                                                                            [0.006, 0.04, 0.024]],
                   mask_array=cpa[4],
                   mask_lut={2: [128, 128, 128]})


def boreali_osw_processing(obj, final_path):
    """
    Мой код в данной функции основан на tutorial.py который я нашел в репозитории boreali.

    :param obj: Nansat объект
    :param final_path: Путь для сохранения файлов
    :return:
    """
    print obj, final_path
    wavelen = [412, 443, 469, 488,
               531, 547, 555,
               645, 667, 678]
    h = 50  # Средняя глубина исследуемого района

    cpa_limits = [0.01, 2,
                 0.01, 1,
                 0.01, 1, 10]

    b = Boreali('michigan', wavelen)
    n = Nansat(obj)
    dom = Domain('+proj=latlong +datum=WGS84 +ellps=WGS84 +no_defs', '-lle -86.3 44.6 -85.2 45.3 -ts 300 200')
    n.reproject(dom)
    dep = numpy.copy(n[2])
    dep[:, :] = h
    theta = numpy.zeros([200, 300])

    custom_n = Nansat(domain=n)
    band_rrs_numbers = list(map(lambda x: n._get_band_number('Rrs_' + str(x)),
                                wavelen))   # Получаем список номеров бандов в которых лежат значения Rrs


    for index in range(0, len(wavelen)):
        rrsw = n[band_rrs_numbers[index]] / (0.52 + 1.7 * n[band_rrs_numbers[index]])   # Пересчитываем Rrs в Rrsw
        custom_n.add_band(rrsw, parameters={'name': 'Rrsw_' + str(wavelen[index]),  # Складываем в новый объект
                                            'units': 'sr-1',
                                            'wavelength': wavelen[index]})
        custom_n.add_band(n[band_rrs_numbers[index]], parameters={'name': 'Rrs_' + str(wavelen[index]),   # Складываем в новый объект
                                                                    'units': 'sr-1',
                                                                    'wavelength': wavelen[index]})

    cpa = b.process(custom_n, cpa_limits, depth=dep, theta=theta, threads=4)

    custom_n.add_band(array=cpa[0], parameters={'name': 'chl',
                                                'long_name': 'Chlorophyl-a',
                                                'units': 'mg m-3'})
    custom_n.add_band(array=cpa[1], parameters={'name': 'tsm',
                                                'long_name': 'Total suspended matter',
                                                'units': 'g m-3'})
    custom_n.add_band(array=cpa[2], parameters={'name': 'doc',
                                                'long_name': 'Dissolved organic carbon',
                                                'units': 'gC m-3'})
    custom_n.add_band(array=cpa[3], parameters={'name': 'mse',
                                                'long_name': 'Root Mean Square Error',
                                                'units': 'sr-1'})
    custom_n.add_band(array=cpa[4], parameters={'name': 'mask',
                                                'long_name': 'L2 Boreali mask',
                                                'units': '1'})

    custom_n.export(final_path + obj.split('/')[-1] + 'cpa_OSW.nc')

    figParams = {'legend': True, 'LEGEND_HEIGHT': 0.5, 'NAME_LOCATION_Y': 0, 'mask_array': cpa[4],
                 'mask_lut': {1: [255, 255, 255], 2: [128, 128, 128], 4: [200, 200, 255]}}
    custom_n.write_figure(final_path + obj.split('/')[-1] + 'chl_OSW.png', 'chl', clim=[0, 1.], **figParams)
    custom_n.write_figure(final_path + obj.split('/')[-1] + 'tsm_OSW.png', 'tsm', clim=[0, 1.], **figParams)
    custom_n.write_figure(final_path + obj.split('/')[-1] + 'doc_OSW.png', 'doc', clim=[0, .2], **figParams)
    custom_n.write_figure(final_path + obj.split('/')[-1] + 'mse_OSW.png', 'mse', clim=[1e-5, 1e-2],
                          logarithm=True, **figParams)
    n.write_figure(final_path + obj.split('/')[-1] + 'rgb_OSW.png', [16, 14, 6], clim=[[0, 0, 0], [0.006, 0.04, 0.024]],
                   mask_array=cpa[4],
                   mask_lut={2: [128, 128, 128]})

'''
REPROJECT_DATA_PATH = os.path.join('/', 'home', 'artemm', 'Documents', 'michigan', 'reprojected_data', '2014/')
AVERAGE_DATA_PATH = os.path.join('/', 'home', 'artemm', 'Documents', 'michigan', 'average_data', '2014/')
BOREALI_PATH = os.path.join('/', 'home', 'artemm', 'Documents', 'michigan', 'boreali_osw_data', '2014/')
DATA_PATH = os.path.join('/', 'home', 'artemm', 'Documents', 'michigan', 'data', '2014/')
months = ['may/', 'jun/', 'sep/', 'oct/']
for month in months:
    data = get_data_list(AVERAGE_DATA_PATH + month)
    for element in data:
        print month + element
        boreali_osw_processing(element, BOREALI_PATH + month)

root = '/home/artemm/Documents/michigan/tests/last/'
repr = '/home/artemm/Documents/michigan/tests/last/reproject_data/'
aver = '/home/artemm/Documents/michigan/tests/last/average_data/'
boreali = '/home/artemm/Documents/michigan/tests/last/boreali_data/'
boreali_osw = '/home/artemm/Documents/michigan/tests/last/boreali_osw_data/'


months = ['may/', 'oct/']
for month in months:
    data = get_data_list(root + month)
    for element in data:
        make_reproject(root + month, repr + month, element)
    make_average(repr + month, aver + month)
    #name = get_data_list(aver)
boreali_processing('/home/artemm/michigan/average_data/oct/A2014281287.L2_LAC_OC.x.nc.reproject.nc.mosaic.nc', '/home/artemm/michigan/oct/')
boreali_osw_processing('/home/artemm/michigan/average_data/oct/A2014281287.L2_LAC_OC.x.nc.reproject.nc.mosaic.nc', '/home/artemm/michigan/oct/')


boreali_processing('/home/artemm/michigan/average_data/may/A2014135141.L2_LAC_OC.x.nc.reproject.nc.mosaic.nc', '/home/artemm/michigan/may/')
boreali_osw_processing('/home/artemm/michigan/average_data/may/A2014135141.L2_LAC_OC.x.nc.reproject.nc.mosaic.nc', '/home/artemm/michigan/may/')
'''     # Сценарии
