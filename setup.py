from setuptools import setup,find_packages

name = "wind_order"
version = "1.0"                                            # models have own version numbering
release = "1.0.0"                                          # and build numbering
description = "wind order models"                                       # descrption used by package server and other users

setup(name=name,
      version=release,
      description=description,
      url='GW',
      author='36719',
      license='',
      python_requires='>=3',
      keywords='' + name,
	  packages=find_packages(),
      # packages=['gw_tower'],
      # package_data = {'gw_tower': ['tower_schema.json']},   # extra, non-python data
      install_requires=['pandas', 'numpy', 'scipy']       # other packages we depend on!
)