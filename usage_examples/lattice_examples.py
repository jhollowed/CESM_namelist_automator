import pdb
import sys
import pathlib

sys.path.append('{}/..'.format(pathlib.Path(__file__).parent.absolute()))
from namelist_lattice import namelist_lattice

# =============================================================================
# =============================================================================

def lattice_submission_example():
    '''
    This example creates a 2-dimensional lattice with 6 total samples (3 after masking),
    where the dimensions are the second-order FV3 diffusion strengths d2_bg_k1,2 for CAM.
    The case clones are then made, and jobs are submitted to Slurm on GreatLakes. 
    
    See docstrings at ../namelist_lattice.py for arg descriptions and more info
    '''

    lattice = namelist_lattice('cam')

    lattice.expand('fv3_d2_bg_k1', limits=[0, 0.2], nsamples = 3)
    lattice.expand('fv3_d2_bg_k2', limits=[0, 0.2], nsamples = 3)

    lat = lattice.lattice
    mask = lat['fv3_d2_bg_k1'] > lat['fv3_d2_bg_k2'] 
    lattice.filter(mask)

    root_case = '/home/hollowed/CESM/cesm2.2_cases/cesm2.2.fv3.C48.L64.fhs94'
    cloned_top_dir = '/home/hollowed/CESM/cesm2.2_cases/fhs94_L64_clones'
    top_output_dir = '/scratch/cjablono_root/cjablono1/hollowed/tmp'
    cime_dir = '/home/hollowed/CESM/cesm2.2/cime/scripts'
    clone_prefix = 'cam'

    lattice.create_clones(root_case, cloned_top_dir, clone_prefix, top_output_dir, cime_dir)
    lattice.submit_clone_runs()


# -------------------------------------------------------------------------------


def lattice_large_example():
    '''
    This example creates a 5-dimensional lattice with 54 total samples (after masking).
    The simulation configrations are then visualized on each projected parameter pair plane
    in the space (no cases are cloned or jobs submitted).
    
    See docstrings at ../namelist_lattice.py for arg descriptions and more info
    '''

    lattice = namelist_lattice('cam')

    lattice.expand('fv3_d2_bg_k1', limits=[0, 0.2], nsamples = 3)
    lattice.expand('fv3_d2_bg_k2', limits=[0, 0.2], nsamples = 3)
    lattice.expand('fv3_d2_bg', limits=[0, 0.02], nsamples = 3)
    lattice.expand('fv3_kord_tm', values=[-9, 9])
    lattice.expand('fv3_n_sponge', values=[5, 10, 15])

    lat = lattice.lattice
    mask = lat['fv3_d2_bg_k1'] > lat['fv3_d2_bg_k2'] 
    lattice.filter(mask)

    print('{} total lattice points'.format(sum(mask)))
    lattice.vis_planes()


# -------------------------------------------------------------------------------
    
