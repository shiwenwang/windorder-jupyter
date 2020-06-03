# -*- coding: utf-8 -*-
"""
Get wind parameter from standard excel file

@author: 36719
"""

import os
import numpy as np
import pandas as pd
from .base_model import Base


class WindParse(Base):

    def run(self):

        """
        --- Parse wind parameters from EXCEL ---
        """
        
        wind_path = self._inputs['path']
        ref_wind_path = self._inputs['ref_path']
        cur_dir = self._inputs['cur_dir']

        cur_wind_params = self.__excel_paras(wind_path)
        ref_load_dir = os.path.abspath(os.path.join(cur_dir, '../files/Loads'))

        ref_wind_params = []
        ref_loads_path = []
        if len(ref_wind_path) > 0:
            ref_loads_path = [os.path.join(ref_load_dir, os.path.split(d)[-1].replace('.xlsx', '_loads.json'))
                              for d in ref_wind_path]

            #  如果Loads路径下没有参考风参对应的载荷，则在func_run.py计算载荷；如果存在, 则在func_run.py导入载荷
            for i, ref_load in enumerate(ref_loads_path):
                if not os.path.exists(ref_load) or not os.path.getsize(ref_load):
                    ref_wind_params.append(self.__excel_paras(ref_wind_path[i]))
                else:
                    ref_wind_params.append(0)

        self._outputs = {'cus': cur_wind_params, 'ref': ref_wind_params, 'ref_loads_path': ref_loads_path}

    def __excel_paras(self, path):
        wind_params = {}
        
        # base data
        wind_condition = pd.read_excel(path, sheet_name='Site Condition', index_col=0)
        wind_condition = self.__clean_data(wind_condition)

        # wind base parameters
        wind_params['condition'] = wind_condition

        # turbine sites
        wind_params['sites'] = list(wind_condition.index)

        # turbulence m1
        wind_data_m1 = pd.read_excel(path, sheet_name='M=1')
        wind_params['m1'] = self.__clean_data(wind_data_m1)

        # turbulence m1
        wind_data_m10 = pd.read_excel(path, sheet_name='M=10')
        wind_params['m10'] = self.__clean_data(wind_data_m10)

        # turbulence etm
        wind_data_etm = pd.read_excel(path, sheet_name='ETM')
        wind_params['etm'] = self.__clean_data(wind_data_etm)

        wind_params['filename'] = os.path.splitext(os.path.split(path)[-1])[0]

        return wind_params

    # @staticmethod
    def __clean_data(self, df_raw):
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

        return self.__fill_data(df_fine)

    @staticmethod
    def __fill_data(df):
        for row_i, row_name in enumerate(df.index):
            if pd.isnull(df.loc[row_name]).any():
                line = [df.iloc[row_i - 1, col_i] if pd.isnull(data) 
                    else data for col_i, data in enumerate(df.loc[row_name])]
                df.loc[row_name] = np.array(line)
            
        return df

