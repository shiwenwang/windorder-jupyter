# -*- coding: utf-8 -*-
"""
Main run

@author: 36719
"""

from functools import partial
from collections import OrderedDict
from wind_order.models import WindParse
from wind_order.models import CalcRatedWindSpeed
from wind_order.models import CalcUltimateLoad
from wind_order.models import TiInterp
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import json
import os
import re


def main_run(enter_dir, wind_path, ref_path,
             regress_ul_folder="../files/Regress_UL_01-39", regress_fl_folder="../files/Regress_FL_001-123"):
    """
    wind-order startup function
    :param enter_dir: the dir of file calling this function
    :param wind_path: farm wind parameter path
    :param ref_path: reference wind parameter path
    :param regress_ul_folder: dir of ultimate load regressor
    :param regress_fl_folder: dir of fatigue load regressor
    :return:
    """

    custom_wind_name = os.path.splitext(os.path.split(wind_path)[-1])[0]
    ref_path = ref_path

    regress_ul_folder = os.path.abspath(os.path.join(enter_dir, regress_ul_folder))
    regress_fl_folder = os.path.abspath(os.path.join(enter_dir, regress_fl_folder))

    """ wind_parse model """
    wind = WindParse(cur_dir=enter_dir, path=wind_path, ref_path=ref_path)
    wind.run()
    wind_outputs = wind.pop()

    wind2loads = partial(gen_loads, enter_dir=enter_dir, regress_ul_folder=regress_ul_folder,
                         regress_fl_folder=regress_fl_folder)

    ref_loads = []
    ref_loads_path = wind_outputs['ref_loads_path']
    if len(ref_loads_path) > 0:
        for i, ref in enumerate(wind_outputs['ref']):
            if ref == 0:  # 参考风参对应的载荷存在
                with open(ref_loads_path[i], 'r') as f:
                    loads = json.load(f)
                ref_loads.append(loads)
            else:
                ref_loads.append(wind2loads(wind_outputs['ref'][i], [], ref_loads_path[i]))
        for ref in ref_loads:
            ref['ul'] = pd.Series(ref['ul'])
            ref['fl'] = pd.Series(ref['fl'])

    cur_loads = wind2loads(wind_outputs['cus'], ref_loads, ref_loads_path, save_loads=False)
    ultimate_load = cur_loads['ul']
    fatigue_load = cur_loads['fl']

    plt.close()
    fig = plt.figure(figsize=(9, 5))
    bar_plot = partial(draw, ref_loads_path=ref_loads_path, custom_wind_name=custom_wind_name)
    bar_plot(fig, ultimate_load, 211)
    bar_plot(fig, fatigue_load, 212)
    plt.tight_layout()
    fig.suptitle(custom_wind_name, y=1, fontsize=14, weight='bold')
    plt.show()


def gen_loads(wind_outputs, ref_loads,  ref_loads_path,
              enter_dir, regress_ul_folder, regress_fl_folder, save_loads=False):
    """
    Calculate loads(U,F) according to wind resource parameter and regressor
    :param wind_outputs:
    :param ref_loads:
    :param ref_loads_path:
    :param enter_dir:
    :param regress_ul_folder:
    :param regress_fl_folder:
    :param save_loads:
    :return:
    """

    ''' calc_rated_wind_speed model '''
    calc_vr_inputs = OrderedDict(wind_condition=wind_outputs['condition'])
    calc_vr = CalcRatedWindSpeed(**calc_vr_inputs)
    calc_vr.run()

    ''' turbulence intensity interpolation '''
    ti_inputs = wind_outputs
    ti_inputs['rws'] = calc_vr.pop()
    ti_interp = TiInterp(**ti_inputs)
    ti_interp.run()

    ''' calculate load '''
    cl_inputs = OrderedDict(ref_loads=ref_loads, u_folder=regress_ul_folder, f_folder=regress_fl_folder,
                            ti=ti_interp.pop(), wind=wind_outputs, ref_loads_path=ref_loads_path)
    cl = CalcUltimateLoad(**cl_inputs)
    cl.run()
    loads = cl.pop()
    ultimate_load = loads['ul']
    fatigue_load = loads['fl']

    if save_loads:
        save_path = os.path.abspath(os.path.join(enter_dir, '../files/Loads/loads.xlsx'))
        with pd.ExcelWriter(save_path) as writer:
            ultimate_load.to_excel(writer, sheet_name='Ultimate Load')
            fatigue_load.to_excel(writer, sheet_name='Fatigue Load')
    
    return loads


def draw(fig, load, sub, ref_loads_path, custom_wind_name):
    """
    plot bar
    :param fig:
    :param load:
    :param sub:
    :param ref_load_path:
    :param custom_wind_name:
    :return:
    """
    fig.add_subplot(sub)

    ref_labels = json_parse(ref_loads_path)

    len_ref_label = lambda x: sum([len(list(v)) for v in x.values()])
    raw_labels = list(load.index)[:-(len_ref_label(ref_labels))] if len(ref_labels) > 0 else list(load.index)

    load_sorted = load.sort_values(ascending=False)

    x_label, values, color_list, legend_handles = bar_config(load_sorted, custom_wind_name, raw_labels, ref_labels)

    if len(x_label) < 10:
        plt.bar(x_label, values, color=color_list, width=0.2)
    else:
        plt.bar(x_label, values, color=color_list)

    y_label = {211: 'Ultimate_load', 212: 'Fatigue_load'}
    plt.ylabel(y_label[sub])

    y_ticks_min = max(round(min(values), 2) - 0.2, 0)
    y_ticks_max = 1.5
    plt.ylim(y_ticks_min, y_ticks_max)
    plt.yticks(np.arange(y_ticks_min, y_ticks_max, 0.2), fontsize=8)

    plt.legend(handles=legend_handles, ncol=len(ref_loads_path) + 1, fontsize='xx-small')
    # mode="expand"（平铺， 默认向右靠拢）  loc='upper right' (默认),

    if len(x_label) > 5:
        plt.xticks(rotation=45, horizontalalignment='right', size=6)
    for a, b in zip(x_label, values):
        plt.text(a, b + 0.005, '%.3f' % b, ha='center', va='bottom', fontsize=6)


def bar_config(load_sorted, custom_wind_name, raw_labels, ref_labels):
    """
    set bar plot attributes(color, label, legend)
    :param load_sorted:
    :param custom_wind_name:
    :param raw_labels:
    :param ref_labels:
    :return:
    """
    values = load_sorted.values

    sorted_labels = list(load_sorted.index)
    show_labels = sorted_labels.copy()

    colors = ['y', 'm', 'g', 'c', 'r', 'k', 'w']
    color_list = []
    for lbl in sorted_labels:
        if lbl in raw_labels:
            color_list.append('b')
        else:
            for i, ref_lbl in enumerate(list(ref_labels.values())):
                if lbl in ref_lbl:
                    color_list.append(colors[i])

    handles = list()
    handles.append(mpatches.Patch(color='b', label=custom_wind_name))
    for filename, ref_lbl in ref_labels.items():
        handles.append(mpatches.Patch(color=color_list[sorted_labels.index(ref_lbl[0])], label=filename))
        for i, lbl in enumerate(ref_lbl):
            replaced_label = lbl.replace(filename + '-', '')
            show_labels[sorted_labels.index(lbl)] = replaced_label

    return show_labels, values, color_list, handles


def json_parse(ref_loads_path):
    """
    count reference labels
    :param ref_loads_path:
    :return:
    """
    ref_labels = {}
    if len(ref_loads_path) > 0:
        for path in ref_loads_path:
            with open(path, 'r') as f:
                loads = json.load(f)
                filename = os.path.splitext(os.path.split(path)[-1])[0][:-6]
                ref_labels[filename] = list(loads['ul'].keys())

    return ref_labels


# -- discarded --
# def get_same_string(s_list):
#     set_s = get_sub_string(s_list[0])
#     for s in s_list[1:]:
#         set_s = set_s.intersection(get_sub_string(s))
#
#     strlen_list = [len(s) for s in list(set_s)]
#
#     return list(set_s)[strlen_list.index(max(strlen_list))]
#
#
# def get_sub_string(s):
#     len_s = len(s)
#     list_s = set()
#
#     for i in range(0, len_s):
#         for j in range(i + 1, len_s):
#             two_s = s[i:j]
#             list_s.add(two_s)
#
#     return list_s
