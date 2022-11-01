import os
import pdb
import sys
import glob
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

    def add_members(self, ic_dir, globstr=None, regex=None):
        '''

        Parameters
        ----------
        ic_root : string
            path to directory containing initial condition files (netcdf). All files present
            in this directory will be assumed to be intial conditions for ensemble members, 
            regardless of exrtension. Subdirectories will be ignored.
        globstr : str
            glob string to apply to files in the ic_root directory; only files matching this
            pattern will be included to generate members for the ensemble. Pattern is applied 
            to file names only, not full path. Defaults to None, in which case no filtering is
            applied.
        '''
        if globstr is not None: 
            globstr = '{}/{}'.format(ic_dir, globstr)
        globstr = '{}/*'.format(ic_dir)
        ic_files = glob.glob(globstr)
        ic_files = ['\"{}\"'.format(f) for f in ic_files if not os.path.isdir(f)]
        ic_files = sorted(ic_files)
        
        self.lattice.expand('NCDATA', values=ic_files)
        self.N = len(ic_files)

    # ------------------------------------------------------------------------------

    def create_members(self, root_case, top_clone_dir, top_output_dir, cime_dir,
                       clone_prefix=None, overwrite=False, clean_all=False, 
                       stdout=None, resubmits=0, read_existing_clones=False):
        '''        
        Parameters
        ----------
        root_case : string
            Location of the root case to be cloned
        top_clone_dir : string
            Top directory for all clones to be created in
        top_output_dir : string
            The top directory in which all clones will output to after being run
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
        read_existing_clones : bool, optional
            If True, then instead of throwing an error or overwriting currently existing cases, 
            simply add them to self.clone_dirs, and continue. Useful if needing to call a method
            of this class that requires self.clone_dirs to be populated, when clones have already
            been created, and do not need to be made again (e.g. resubmit_hung_clone_runs). 
            Defaults to False.
            If True, then overwrite and clean_all must both be False. This is enforced.
        '''
        ens_sfx = ['ens{:02d}'.format(i+1) for i in range(self.N)]
        self.lattice.create_clones(root_case, top_clone_dir, top_output_dir, cime_dir, clone_prefix, 
                                   ens_sfx, overwrite, clean_all, stdout, resubmits, read_existing_clones)
    
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


    def resubmit_hung_members(self, dry=False): 
        '''
        Resubmit runs of the cloned cases created by self.clone_members() for which the 
        resbumission process was inturrupted by a job scheduler problem. See docstrings
        in namelist_lattice.resubmit_hung_clone_runs() for more info.

        Parameters
        ----------
        dry : boolean, optional
            Whether or not to do a dry run, which just prints the location of each
            submission script which is about to be called. Defaults to False.
        '''
        self.lattice.resubmit_hung_clone_runs(dry)


# =============================================================================
# =============================================================================


