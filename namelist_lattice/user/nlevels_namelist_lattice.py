import pdb
import sys
import pathlib

sys.path.append('{}/..'.format(pathlib.Path(__file__).parent.absolute()))
from namelist_lattice import namelist_lattice

def build_lattice():

    lattice = namelist_lattice('cam')

    lattice.expand('fv3_d2_bg_k1', limits=[0, 0.2], nsamples = 3)
    lattice.expand('fv3_d2_bg_k2', limits=[0, 0.2], nsamples = 3)
    #lattice.expand('fv3_kord_tm', values=[-9, 9])
    #lattice.expand('fv3_n_sponge', values=[5, 10, 15])
    #lattice.expand('fv3_d2_bg', limits=[0, 0.02], nsamples = 3)

    lat = lattice.lattice
    mask = lat['fv3_d2_bg_k1'] > lat['fv3_d2_bg_k2'] 
    lattice.filter(mask)

    root_case = '/home/hollowed/CESM/cesm2.2_cases/cesm2.2.fv3.C48.L64.fhs94'
    cloned_top_dir = '/home/hollowed/CESM/cesm2.2_cases/fhs94_L64_clones'
    top_output_dir = '/scratch/cjablono_root/cjablono1/hollowed/test'
    cime_dir = '/home/hollowed/CESM/cesm2.2/cime/scripts'
    clone_prefix = 'cam'


    lattice.create_clones(root_case, cloned_top_dir, clone_prefix, top_output_dir, cime_dir)
    lattice.submit_clone_runs()
    



build_lattice()
    
