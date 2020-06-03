# -*- coding: utf-8 -*-
"""
Calculate ultimate Load

@author: 36719
"""

import os
import re
import math
import numpy as np
import pandas as pd
from .base_model import Base
import json


class CalcUltimateLoad(Base):

    def run(self):
        """
        --- Import regressor for calculating ultimate load ---
        :param self.regressor_dir: folder of regress_ul excel
        :return ultimate Load - Mxy at Tower Bottom
        """
        ref_loads = self._inputs['ref_loads']
        regress_ul_dir = self._inputs['u_folder']
        regress_fl_dir = self._inputs['f_folder']
        # u_variable_config_path = self._inputs['path']
        wind_condition = self._inputs['wind']['condition'][['θmean', 'α', 'ρ', 'V50']]
        wind_condition.columns = ['inflow_angle', 'wind_shear', 'air_density', 'V50']
        turbine_sites = self._inputs['wind']['sites']
        ref_loads_path = self._inputs['ref_loads_path']

        # if len(ref_loads_path) > 0:
        #     if isinstance(ref_loads_path, list):
        #         ref_loads_filename = [os.path.splitext(os.path.split(f)[-1])[0][:-6] for f in ref_loads_path]
        #     else:
        #         ref_loads_filename = os.path.splitext(os.path.split(ref_loads_path)[-1])[0][:-6]

        ti = self._inputs['ti']
        wind_cut_in = 3
        wind_cut_out = 20
        V50_alpha_beta = self._inputs['wind']['condition'][['V50', 'K', 'A']]

        u_pattern = re.compile(r'Regress_UL_.+\.xls')
        f_pattern = re.compile(r'Regress_RF_Case\d+\.xls')

        # get regress_ul
        regressor_ul = self.__get_regressor(regress_ul_dir, u_pattern, 'UL_TB_Mxy')

        # get Regress_RF
        regressor_fl = self.__get_regressor(regress_fl_dir, f_pattern, 'RF_TB_My_m4')

        # calculate ultimate load
        ultimate_load = self.__calc_load(regressor_ul, turbine_sites, wind_condition, ti)
        ultimate_load_max = self.__get_ultimate_load_max(turbine_sites, ultimate_load, ref_loads, ref_loads_path)

        # calculate fatigue load
        fatigue_load = self.__calc_load(regressor_fl, turbine_sites, wind_condition, ti)
        p_case = self.__fatigue_case_proportion(turbine_sites, wind_cut_in, wind_cut_out, V50_alpha_beta)
        fatigue_load_equivalence = \
            self.__get_fatigue_load_equivalence(turbine_sites, fatigue_load, p_case, ref_loads, ref_loads_path) # dataframe

        if len(ref_loads) == 0 and len(ref_loads_path) > 0:  # 将参考风参对应载荷写入json文件
            with open(ref_loads_path, 'w') as f:
                ul = {}
                fl = {}
                for index in ultimate_load_max.index:
                    ul[index] = ultimate_load_max.loc[index]
                for index in fatigue_load_equivalence.index:
                    fl[index] = fatigue_load_equivalence.loc[index]
                json.dump({'ul': ul, 'fl': fl}, f)

        self._outputs = {'ul': ultimate_load_max, 'fl': fatigue_load_equivalence}

    def __get_regressor(self, folder, pattern, load_name):
        """
        Regressor read and regularization
        :param df:
        :return:
        """
        regressor = {}
        for file in os.listdir(folder):
            if pattern.match(file):
                path = os.path.join(folder, file)
                df = pd.read_excel(path, index_col=0, header=None)
                df.drop([df.index[0], df.index[2]], inplace=True)
                df.columns = df.loc[df.index[0]]
                df.drop(df.index[0], inplace=True)
                df.index = self.__repl_zh(df.index)
                regressor[file] = df[load_name]

        return regressor

    @staticmethod
    def __repl_zh(list_zh):
        """
        --- Convert chinese character to alphanumeric character ---
        :param list_zh:
        :return list_en:
        """

        look_up = {'常量': 'const', '最大入流角β': 'inflow_angle', '平均入流角β': 'inflow_angle',
                   '风切变α': 'wind_shear', '空气密度ρ': 'air_density', '极限风速V50': 'V50'}
        list_en = [look_up[zh] for zh in list_zh if zh in look_up.keys()]
        if list_zh[-1] not in look_up.keys():
            list_en.append(list_zh[-1])

        return list_en

    @staticmethod
    def __calc_load(regressor, turbine_sites, wind_condition, ti):
        load = {}
        for turbine_id in turbine_sites:
            turbine_load = {}
            turbine_wind_condition = wind_condition.loc[turbine_id]
            turbine_ti = ti[turbine_id]
            for dlc, reg in regressor.items():
                observed_load = 0
                for var in reg.index:
                    if var in turbine_wind_condition.index:
                        observed_load += reg[var] * turbine_wind_condition[var]
                    elif var in turbine_ti.index:
                        observed_load += reg[var] * turbine_ti[var]
                    else:
                        observed_load += reg[var]
                turbine_load[dlc[11:-4]] = observed_load

            load[turbine_id] = pd.Series(turbine_load)

        return load

    @staticmethod
    def __cdf(x, alpha, beta):
        """
        Weibull Cumulative distribution function
        :param x:
        :param alpha:  shape parameter
        :param beta:  scale parameter
        :return cum_dist:
        """
        cum_dist = 1 - math.exp(-(x / beta) ** alpha)

        return cum_dist

    @staticmethod
    def __get_ultimate_load_max(turbine_sites, ultimate_load, ref_loads, ref_loads_path):
        ultimate_load_max = {}
        for turbine_id in turbine_sites:
            ultimate_load_max[turbine_id] = np.max(ultimate_load[turbine_id].values)

        ser_ultimate_load_max = pd.Series(ultimate_load_max, name='UL1')
        if len(ref_loads_path) > 0:
            if len(ref_loads) > 0:
                for ref in ref_loads:
                    for index in ref['ul'].index:
                        ser_ultimate_load_max = ser_ultimate_load_max.append(pd.Series({index: ref['ul'][index]}))
                ser_ultimate_load_max = ser_ultimate_load_max.copy().div(np.max(ser_ultimate_load_max.copy().values))
                ser_ultimate_load_max.name = 'UL1'
        else:
            ser_ultimate_load_max = ser_ultimate_load_max.copy().div(np.max(ser_ultimate_load_max.copy().values))

        return ser_ultimate_load_max

    @staticmethod
    def __get_fatigue_load_equivalence(turbine_sites, fatigue_load, p_case, ref_loads, ref_loads_path):
        fatigue_load_equivalence = {}
        for turbine_id in turbine_sites:
            fatigue_load_equivalence[turbine_id] = \
                np.power(np.power(fatigue_load[turbine_id].values, 4).dot(np.array(p_case[turbine_id])), 1/4)

        ser_fatigue_load_equivalence = pd.Series(fatigue_load_equivalence, name='FL1')
        if len(ref_loads_path) > 0:
            if len(ref_loads) > 0:
                for ref in ref_loads:
                    for index in ref['fl'].index:
                        ser_fatigue_load_equivalence = ser_fatigue_load_equivalence.append(pd.Series({index: ref['fl'][index]}))
                ser_fatigue_load_equivalence = \
                    ser_fatigue_load_equivalence.copy().div(np.max(ser_fatigue_load_equivalence.copy().values))
                ser_fatigue_load_equivalence.name = 'FL1'
        else:
            ser_fatigue_load_equivalence = \
                ser_fatigue_load_equivalence.copy().div(np.max(ser_fatigue_load_equivalence.copy().values))

        return ser_fatigue_load_equivalence

    def __fatigue_case_proportion(self, turbine_sites, cut_in, cut_out, V50_alpha_beta):
        """
        calculate proportion of fatigue case
        :param cut_in:
        :param cut_out:
        :param v50:
        :return: list of proportion
        """
        p_dict = {}
        V50 = V50_alpha_beta['V50']
        alpha = V50_alpha_beta['K']
        beta = V50_alpha_beta['A']

        wind_linspace = np.append(np.arange(cut_in, cut_out, 2), cut_out)
        for turbine_id in turbine_sites:
            wind_end = (0.7 * V50[turbine_id] if 0.7 * V50[turbine_id] > cut_out + 1 else cut_out + 2)
            p_list = []
            for d in wind_linspace[:8]:
                    v = (self.__cdf(d + 1, alpha[turbine_id], beta[turbine_id]) -
                         self.__cdf(d - 1, alpha[turbine_id], beta[turbine_id])) / 6 / \
                         self.__cdf(wind_end, alpha[turbine_id], beta[turbine_id])

                    p_list.extend([v]*6)

            v_19 = (self.__cdf(19.5, alpha[turbine_id], beta[turbine_id]) -
                    self.__cdf(18, alpha[turbine_id], beta[turbine_id])) / 6 / \
                    self.__cdf(wind_end, alpha[turbine_id], beta[turbine_id])
            v_20 = (self.__cdf(21, alpha[turbine_id], beta[turbine_id]) -
                    self.__cdf(19.5, alpha[turbine_id], beta[turbine_id])) / 6 / \
                    self.__cdf(wind_end, alpha[turbine_id], beta[turbine_id])
            p_list.extend([v_19] * 6 + [v_20] * 6)
            p_list.extend([9.50644441867142E-07] * 24)
            p_list.extend([1.90128888373428E-06] * 24)
            p_list.extend([0.001901289, 9.50644E-05, 9.50644E-05])
            v_lt2 = (self.__cdf(2, alpha[turbine_id], beta[turbine_id]) -
                    self.__cdf(0, alpha[turbine_id], beta[turbine_id])) / 6 / \
                   self.__cdf(wind_end, alpha[turbine_id], beta[turbine_id])
            v_gt20 = (self.__cdf(wind_end, alpha[turbine_id], beta[turbine_id]) -
                    self.__cdf(21, alpha[turbine_id], beta[turbine_id])) / 6 / \
                   self.__cdf(wind_end, alpha[turbine_id], beta[turbine_id])

            p_list.extend([v_lt2] * 6 + [v_gt20] * 6)

            p_dict[turbine_id] = p_list

        return p_dict
