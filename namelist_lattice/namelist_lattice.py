import os
import pdb
import glob
import subprocess
import numpy as np
from os.path import expanduser
import matplotlib.pyplot as plt
import matplotlib as mpl

mpl.rcParams['axes.xmargin'] = 0.1
mpl.rcParams['axes.ymargin'] = 0.1
cime = '{}/CESM/cesm2.2/cime/scripts'.format(expanduser('~'))

# ==========================================================================================
# ==========================================================================================

class namelist_lattice:
    def __init__(self, component):
        '''
        This class constructs a configuration lattice object, which organizes a lattice of
        positions in paramter space, intended for automating the running of several 
        simulation runs with varying namelist settings.

        Parameters
        ----------
        component : string
            The component that the namelists on this lattice are meant to apply to. If
            self.clone_case is called, the namelist changes will be made to 
            user_nl_{component}.
        '''
        self.component = component
        self.param_vectors = []
        self.param_names = []
        self._lattice = None
        self.clone_dir = None
    
    @property
    def lattice(self):
        if(len(self.param_names) < 2): 
            raise RuntimeError('must add at least 2 dimensions to build lattice')
        else:
            return self._lattice

    # ------------------------------------------------------------------------------

    def expand(self, names, limits=None, nsamples=None, values=None):
        '''
        Adds N dimensions to the lattice, and popultes each with parameter samples

        Parameters
        ----------
        name : string or (N,) string array
            Name of the parameters
        limits : (2,) or (N,2) float array, optional
            Upper and lower limits for each paramter
        nsamples : int or (N,) int array, optional
            number of samples to insert between the stated limits for each parameter
        values : (N,) float array, or list of float lists, optional
            number of samples to insert between the stated limits for each parameter
        '''
      
        errstr = 'either (\'values\') or (\'limits\' and \'nsamples\') must be passed, not both'
       
        if(values is None):
            assert limits is not None and nsamples is not None, err
            
            names = np.atleast_1d(names)
            limits = np.atleast_2d(limits)
            nsamples = np.atleast_1d(nsamples)
            
            assert len(names) == len(limits) and len(names) == len(nsamples),\
                   'args \'names\', \'limits\', and \'nsamples\' must all be of equal length'
           
            # build new dimensions
            self.param_names.extend(names)
            for i in range(len(names)):
                vals = np.linspace(limits[i][0], limits[i][1], nsamples[i])
                self.param_vectors.append(vals)
                
        else:
            assert limits is None and nsamples is None, err
            
            names = np.atleast_1d(names)
            values = np.atleast_2d(values)
            
            assert len(names) == len(values),\
                   'args \'names\'  and \'values\' must be of equal length'

            # build new dimensions
            self.param_names.extend(names)
            self.param_vectors.extend(values)
            
        if(len(self.param_names) > 1):
            self._build_lattice()
    
    # ------------------------------------------------------------------------------

    def filter(self, mask):
        '''
        Filters out undesired run configurations from the lattice

        Parameters
        ----------
        mask : bool array with dimensions matching lattice
        '''

        self._lattice = self._lattice[mask]
        
    # ------------------------------------------------------------------------------

    def _build_lattice(self):
        '''
        Builds the lattice and returns it as a set of M-dimensional points, where M is 
        the total number of dimensions added with expand()

        Returns
        -------
        lattice : (T, M) float array
            a array of T total M-dimensional points on the lattice
        '''
        grid = np.meshgrid(*self.param_vectors)
        points = np.vstack(list(map(np.ravel, grid)))
        self._lattice = np.core.records.fromarrays(points, names=self.param_names)
 
    # ------------------------------------------------------------------------------

    def create_clones(self, root_case, cloned_top_dir=None, clone_prefix=None, 
                      top_output_dir=None, cime_dir=cime):
        '''
        clone the root_case CESM CIME case per each point on the lattice, and edit the
        namelist file at cloned_case/user_nl_{self.component} with the content of that 
        point.

        Parameters
        ----------
        root_case : string
            Location of the root case to be cloned
        cloned_top_dir : string
            Top directory for all clones to be created in. Default is None, in which case
            clones are all created at the same location as root_case
        clone_prefix : string
            prefix of each clone case. Default is None, in which case the name of the 
            root case will be used. The full cloned case location is then
            {cloned_top_dir}/{clone_prex}_{P1}{V1}_{P2}{V2}_....
            where P are the names of the namelist settings on the lattice (constant for all
            clones), and v are their values (unique for each clone)
        top_output_dir : string
            The top directory in which all clones will output to after being run. Default is 
            None, in which case the output directory of the root case is used.
        cime_dir : string
            Location of the cime/scripts directory within cesm2.2
        '''

        if(self._lattice is None):
            raise RuntimeError('Lattice must first be built by calling expand()')
        
        namelists = self._lattice.dtype.names
        if(cloned_top_dir is None):
            cloned_top_dir = '/'.join(root_case.split('/')[:-1])
        if(clone_prefix is None):
            clone_prefix = root_case.split('/')[-1]
        self.clone_dir = cloned_top_dir
        
        print('\n\n =============== CREATING {} CLONES ===============\n'.format(
               len(self._lattice)))

        # clone the root case per lattice point
        for i in range(len(self._lattice)):
            
            params = self._lattice[i]
            print('\n =============== creating clone with {} = {} ===============\n'.format(
                   namelists, params))
            
            sfx = '_'.join(['{}{}'.format(namelists[i], params[i]) for i in range(len(params))])
            new_case = '{}/{}__{}'.format(cloned_top_dir, clone_prefix, sfx)

            cmd = '{}/create_clone --case {} --clone {} --cime-output-root {} --keepexe'.format(
                   cime_dir, new_case, root_case, top_output_dir)
            subprocess.run(cmd.split(' '))
            
            # --- edit the user_nl_{component} file ---
            
            # purge current occurences of the parameters present in the lattice
            with open('{}/user_nl_{}'.format(new_case, self.component), 'r+') as f:
                
                entries = f.readlines()
                f.seek(0)
                for e in entries:
                    param = ''.join(e.split()).split('=')[0]
                    if(param not in namelists): 
                        f.write(e)
                f.truncate()
                nl = f.read()
            
            # write new parameter choices
            with open('{}/user_nl_{}'.format(new_case, self.component), 'a') as f:
                if not nl.endswith('\n'):
                    f.write('\n')
                for j in range(len(params)):
                    f.write('{} = {}\n'.format(namelists[j], params[j]))
    
    # ------------------------------------------------------------------------------

    def submit_clone_runs(self):
        '''
        Submit runs of the cloned cases created by self.create_clones()
        '''
        
        if(self.clone_dir is None):
            raise RuntimeError('Clone cases must first be created by calling expand()')
            
        clones = glob.glob('{}/*'.format(self.clone_dir))
        for clone in clones:
            os.chdir(clone)
            subprocess.run('{}/case.submit'.format(clone))
    
    # ------------------------------------------------------------------------------

    def vis_planes(self):
        '''
        Visualizes the lattice as a triangle plot, with a subplot per parameter pair
        '''

        N = len(self.param_names)
        f, ax = plt.subplots(N, N, figsize=(10,10))
        
        # remove diagonal and upper traingle
        for i in range(N):
            remove_right = N-i
            for j in range(remove_right):
                ax[i, N-(j+1)].axis('off')

        # populate lower triangle
        for i in range(N):
            num_plots = i
            for j in range(num_plots):
                v1 = self.lattice[self.param_names[j]]
                v2 = self._lattice[self.param_names[i]]
                ax[i, j].plot(v1, v2, '.r', ms=10)
                #ax[i, j].set_xlim([min(v1) - min(v1)*0.1, max(v1)*1.1])
                #ax[i, j].set_ylim([min(v2)*0.9, max(v2)*1.1])
                ax[i, j].grid(True)
                if(j == 0):
                    ax[i,j].set_ylabel(self.param_names[i])
                else:
                    ax[i, j].set_yticklabels([])
                if(i == N-1):
                    ax[i,j].set_xlabel(self.param_names[j])
                else:
                    ax[i, j].set_xticklabels([])
                    
        plt.tight_layout()
        plt.show()


            
                
                

            










