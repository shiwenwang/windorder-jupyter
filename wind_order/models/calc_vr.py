# -*- coding: utf-8 -*-
"""
Calculate rated wind speed at hub height

@author: 36719
"""

import numpy as np
import pandas as pd
from .base_model import Base


class CalcRatedWindSpeed(Base):

    def run(self):
        """
        --- Import regressor for calculating rated wind speed at hub height ---
        :param self.regressor_path: path of wind paras excel
        :param self.wind_condition: include inflow angle, wind_shear, air_density of every turbine
        :return rated_wind_speed
        """
        wind_condition = self._inputs['wind_condition'][['θmean', 'α', 'ρ']]
        # wind_condition = wind_condition.drop('Ve50', axis=1)
        wind_condition.columns = ['inflow_angle', 'wind_shear', 'air_density']
        regressor = {'const': 14.54212663, 'inflow_angle': 0.031650249,
                     'wind_shear': 0.230199432, 'air_density': -3.999156118}

        dict_rated_wind_speed = {}
        for turbine_id in wind_condition.index:
            turbine_wind_condition = wind_condition.loc[turbine_id]
            dict_rated_wind_speed[turbine_id] = sum(
                [turbine_wind_condition[var] * regressor[var] for var in wind_condition.columns]) \
                                                + regressor['const']

        self._outputs = dict_rated_wind_speed

    @staticmethod
    def __clean_data(df_raw):
        """
        --- Remove useless data ---
        :param df_raw: original data frame
        :return df_fine: data frame except useless data (e.g. Note)
        """

        rows = df_raw.shape[0]
        for head_idx, head_str in enumerate(df_raw.columns):
            if 'Unnamed:' in head_str:
                cols = head_idx
                break
        else:
            cols = head_idx + 1
        df_fine = df_raw.iloc[0:rows, 0:cols].dropna(how='all')
        df_fine.drop(df_fine.index[0], inplace=True)  # drop first line (unit)
        if df_fine.shape[0] > 4:
            df_fine.drop(df_fine.index[4:], inplace=True)

        return df_fine
