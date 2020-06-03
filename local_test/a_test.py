import os
from wind_order.func_run import main_run

THIS_DIR = os.path.dirname(__file__)


REF_STD_FOLDER = os.path.abspath(os.path.join(THIS_DIR, "../enter/参考设计风参/标准设计风参/"))
REF_CUS_FOLDER = os.path.abspath(os.path.join(THIS_DIR, "../enter/参考设计风参/定制化塔架设计风参/"))
CUS_FOLDER = os.path.abspath(os.path.join(THIS_DIR, "../enter/项目场址风参/"))

wind_path = os.path.join(CUS_FOLDER,'test.xlsx')
ref_std_wind_path = [os.path.join(REF_STD_FOLDER, d) for d in os.listdir(REF_STD_FOLDER) if d.endswith('xlsx') or d.endswith('xls')]
ref_cus_wind_path = [os.path.join(REF_CUS_FOLDER, d) for d in os.listdir(REF_CUS_FOLDER) if d.endswith('xlsx') or d.endswith('xls')]
ref_wind_path = []
ref_wind_path.extend(ref_cus_wind_path)
ref_wind_path.extend(ref_std_wind_path)

main_run(THIS_DIR, wind_path, ref_wind_path)
