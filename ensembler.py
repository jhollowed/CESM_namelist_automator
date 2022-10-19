import os
import pdb
import sys
import pathlib

sys.path.append('{}/.'.format(pathlib.Path(__file__).parent.absolute()))
from namelist_lattice import namelist_lattice


# =============================================================================
# =============================================================================


class ensembler:
    def __init__(self, component='eam'):
        '''
        This class...

        Parameters
        ----------
        component : string, optional
            The component that the namelists on this lattice are meant to apply to. If
            self.clone_case is called, the namelist changes will be made to 
            user_nl_{component}. Defaults to 'eam'.
        ''' 
        self.N = 0
        self.lattice = namelist_lattice(component)
    
    # ------------------------------------------------------------------------------

    def add_members(self, ic_dir):
        '''

        Parameters
        ----------
        ic_root : string
            path to directory containing initial condition files (netcdf). All files present
            in this directory will be assumed to be intial conditions for ensemble members, 
            regardless of exrtension. subdirectories willbe ignored.
        '''
        
        ic_files = [os.path.join(ic_root, f) for f in \
                    os.listdir(ic_root) if os.path.isfile(os.path.join(ic_root, f))]
        self.lattice.expand('NCDATA', values=ic_files)
        self.N = len(ic_files)

    # ------------------------------------------------------------------------------

    def clone_members(self, root_case, top_clone_dir, cime_dir,
                      clone_prefix=None, clone_sfx=None, overwrite=False, clean_all=False, 
                      stdout=None, resubmits=0):
        '''
        
        Parameters
        ----------
        root_case : string
            Location of the root case to be cloned
        top_clone_dir : string
            Top directory for all clones to be created in. Default is None, in which case
            clones are all created at the same location as root_case
        top_output_dir : string
            The top directory in which all clones will output to after being run. Default is 
            None, in which case the output directory of the root case is used.
        cime_dir : string
            Location of the cime/scripts directory
        clone_prefix : string, optional
            prefix of each clone case. Default is None, in which case the name of the 
            root case will be used. The full cloned case location is then
            {top_clone_dir}/{clone_prefix}_ens{V}, where V is a unique integer per-clone
        overwrite : bool, optional
            Whether or not to overwrite preexisting clone cases found in top_clone_dir with 
            name conflicts. Default is False, in which case an error will be thrown in this 
            event. Leave as Default to be safe unless you know you need it to be otherwise.
        clean_all : bool, optional
            Whether or not to completely remove content of top_clone_dir and top_output_dir
            before creating clones. This is useful if the previous run of this function was known
            to contain mistakes. Default is False, which it probably should be, and you porobably
            shouldn't change it. Definitely don't change it if top_clone_dir and top_output_dir 
            were not passed (unless you enjoy rebuilding your CESM cases, or you know exactly what
            you're doing).
        stdout : string, optional
            File at which to send stdout for calls to CIME utilities. Defaults to None, in which 
            case all output is sent to the terminal.
        resubmits : int, optional
            Number of resubmits for clones. Unfortunately, this currently may not be inherited from
            the root case, and should be set manually here. Default is 0.
        '''
        ens_sfx = ['ens{}'.format(i+1) for i in range(self.N)]
        self.nl.create_clones(root_case, top_clone_dir, top_output_dir, cime_dir, clone_prefix, 
                              ens_sfx, overwrite, clean_all, stdout, resubmits)
    
    # ------------------------------------------------------------------------------
    
    def submit_members(self, dry=False):
        '''
        Submit runs of the cloned cases created by self.clone_members()

        Parameters
        ----------
        dry : boolean, optional
            Whether or not to do a dry run, which just prints the location of each
            submission script which is about to be called. Defaults to False.
        '''
        self.lattice.submit_clone_runs(dry)


# =============================================================================
# =============================================================================


