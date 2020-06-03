# -*- coding: utf-8 -*-
"""
Turbulent intensity interpolation at [rated, cut-out, rated-2, rated+2] wind speed

@author: 36719
"""
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
from wind_order.models import Base


class TiInterp(Base):

    def run(self):
        """

        :return ti: turbulence intensity
        """
        ti = {}

        turbine_sites = self._inputs['sites']
        wind_condition = self._inputs['condition']
        ti_m1 = self._inputs['m1']
        ti_m10 = self._inputs['m10']
        ti_etm = self._inputs['etm']
        rated_wind_speed = self._inputs['rws']
        filename = self._inputs['filename']
        # wind_cut_in = 2.5 if ti_etm['Wind Speed'].iloc[0] < 3 else 3
        # print(f'Tips: Cut-in wind speed is {wind_cut_in}m/s.')

        wind_cut_in = 3
        wind_cut_out = int(ti_etm['Wind Speed'].iloc[-1])
        cut_out_list = [19, 19.5, 20, 20.5, 23, 23.5, 25]

        if wind_cut_out in cut_out_list:
            # print(f'Tip: Cut-out wind speed is {wind_cut_out}m/s.')
            pass
        else:
            print(f'Tip: [{filename}] Cut-out wind speed is {wind_cut_out}m/s, unconventionally.')
            pass

        wind_linspace = np.append(np.arange(3, 20, 2), 20)
        etm_index = ['ETM' + str(d) for d in wind_linspace]
        Ix_m10_index = [''.join(['I', str(d), '_m10']) for d in wind_linspace]

        for turbine_id in turbine_sites:
            interpolator_m1 = interp1d(ti_m1['Wind Speed'].values, ti_m1[turbine_id].values, kind='linear')
            interpolator_m10 = interp1d(ti_m10['Wind Speed'].values, ti_m10[turbine_id].values, kind='linear')
            interpolator_etm = interp1d(ti_etm['Wind Speed'].values, ti_etm[turbine_id].values, kind='linear')

            ti_r_m1 = interpolator_m1(rated_wind_speed[turbine_id])
            ti_rp2_m1 = interpolator_m1(rated_wind_speed[turbine_id] + 2)
            ti_rm2_m1 = interpolator_m1(rated_wind_speed[turbine_id] - 2)
            ti_out_m1 = interpolator_m1(wind_cut_out)

            ti_r_m10= interpolator_m10(rated_wind_speed[turbine_id])
            ti_in_m10 = interpolator_m10(wind_cut_in)
            ti_out_m10 = interpolator_m10(wind_cut_out)
            wind_end = (0.7 * wind_condition.loc[turbine_id]['V50'] if 0.7 * wind_condition.loc[turbine_id]['V50'] >
                        wind_cut_out + 1 else wind_cut_out + 2)
            ti_end_m10 = interpolator_m10(15)*(0.75+5.6/wind_end)/(0.75+5.6/15)

            end_value = 19 if wind_cut_out < 19 else wind_cut_out
            interp_list = np.append(wind_linspace[:-1], end_value)
            try:
                ti_etm_interp_arr = interpolator_etm(interp_list)  # 利用切出风速求ETM20
                ti_ix_m10_interp_arr = interpolator_m10(interp_list)  # 利用切出风速求I20_m10
            except ValueError:
                inner = [i for i in interp_list if i < ti_etm['Wind Speed'].values[-1]]
                ti_etm_interp_inner = interpolator_etm(inner)
                ti_outer = [float(interpolator_etm(wind_cut_out)) for i in interp_list if i > ti_etm['Wind Speed'].values[-1]]
                ti_etm_interp_arr = np.array(ti_etm_interp_inner.tolist() + ti_outer)

                ti_m10_interp_inner = interpolator_etm(inner)
                ti_outer = [float(interpolator_etm(wind_cut_out)) for i in interp_list if i > ti_etm['Wind Speed'].values[-1]]
                ti_ix_m10_interp_arr = np.array(ti_m10_interp_inner.tolist() + ti_outer)

            ti_etmx = pd.Series(ti_etm_interp_arr, index=etm_index)
            ti_ix_m10 = pd.Series(ti_ix_m10_interp_arr, index=Ix_m10_index)

            ti_tail = pd.Series({'Ir_m1': ti_r_m1, 'Ir+2_m1': ti_rp2_m1, 'Ir-2_m1': ti_rm2_m1, 'Iout_m1': ti_out_m1,
                                 'Ir_m10': ti_r_m10, 'Iin_m10': ti_in_m10, 'Iout_m10': ti_out_m10,
                                 'Iend_m10': ti_end_m10})

            ti[turbine_id] = pd.concat([ti_etmx, ti_ix_m10, ti_tail])

        self._outputs = ti

