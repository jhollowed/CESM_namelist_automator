import pdb
import sys
import pathlib

sys.path.append('{}/..'.format(pathlib.Path(__file__).parent.absolute()))
from namelist_lattice import namelist_lattice as f 

def build_lattice():

    namelist_configs = f('cam')
    #namelist_configs.expand('fv3_kord_tm', values=[-9, 9])
    namelist_configs.expand('fv3_kord_tm', values=[9])
    namelist_configs.expand('fv3_n_sponge', values=[5, 10, 15])
    #namelist_configs.expand('fv3_d2_bg', limits=[0, 0.02], nsamples = 3)
    #namelist_configs.expand('fv3_d2_bg_k1', limits=[0, 0.2], nsamples = 3)
    #namelist_configs.expand('fv3_d2_bg_k2', limits=[0, 0.2], nsamples = 3)

    #lat = namelist_configs.lattice
    #mask = lat['d2_bg_k1'] > lat['d2_bg_k2'] 
    #namelist_configs.filter(mask)
    namelist_configs.create_clones(root_case = '/home/hollowed/CESM/cesm2.2_cases/cesm2.2.fv3.C48.L64.fhs94', cloned_top_dir='/home/hollowed/CESM/cesm2.2_cases/fhs94_L64_clones', clone_prefix='cam')



build_lattice()
    
