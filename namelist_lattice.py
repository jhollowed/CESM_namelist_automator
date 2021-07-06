import os
import pdb
import glob
import shutil
import subprocess
import numpy as np
from pathlib import Path
from os.path import expanduser
import matplotlib.pyplot as plt
import matplotlib as mpl
import warnings

mpl.rcParams['axes.xmargin'] = 0.1
mpl.rcParams['axes.ymargin'] = 0.1
cime = '{}/CESM/cesm2.2/cime/scripts'.format(expanduser('~'))

# ==========================================================================================
# ==========================================================================================



class namelist_lattice:
    def __init__(self, component, nofill=False):
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
        nofill : boolean
            If True, the lattice will not fill, but only create points in parameter space 
            as explicitly passed by the user. For example, if the expanded dimensions for
            parameters 'a' and 'b' are [0, 1], [10, 20], then nofill=False will yeild clones
            created for [(0, 10), (1, 10), (0, 20), (1, 20)], while nofill=True will yeild 
            only [(0, 10), (1, 20)]. Thus, this option affects to number of total lattice 
            points, though the dimension is unchanged. Defaults to False.
        '''
        self.component = component
        self.nofill = nofill
        self.param_vectors = []
        self.param_names = []
        self.xml_mask = []
        self.paramgroup_mask = []
        self.paramgroup_labels = []
        self.clone_dirs = []
        self._lattice = None
    
    @property
    def lattice(self):
        if(len(self.param_names) < 2): 
            raise RuntimeError('must add at least 2 dimensions to build lattice')
        else:
            return self._lattice


    # ------------------------------------------------------------------------------


    def expand(self, names, limits=None, nsamples=None, values=None, 
               xmlchange=False, group=False, group_labels=None):
        '''
        Adds N dimensions to the lattice, and popultes each with parameter samples

        Parameters
        ----------
        names : string or (N,) string array
            Name of the parameters
        limits : (2,) or (N,2) float array, optional
            Upper and lower limits for each paramter
        nsamples : int or (N,) int array, optional
            number of samples to insert between the stated limits for each parameter
        values : (N,) float array, or list of float lists, optional
            number of samples to insert between the stated limits for each parameter
        xmlchange : boolean
            whether or not to flag this dimension as a parameter that must be changed
            in a CIME case by xmlchange (i.e. the parameter is stored in env_run.xml). 
            Defaults to False, in which case it is assumed that the parameter is stored
            in user_nl_{self.component}
        group : boolean
            Whether or not to interpret the pased dimensions as lists of namelist settings 
            which should be treated as a sinle point in the lattice. For example, if the call
            is
            
            expand(names='p1,p2,p3', values=['2,2,2', '4,4,4'], group=True, group_labels='group1')

            then the three parameters p1, p2, and p3 are treated as occupying a single dimension
            in the lattice as a trio, with only two possibilities for their values, all equaling 5, 
            or all equaling 6. Alternatively, think of this as a constraint that points on the 
            lattice can only exist if they intersect (5,5,5) or (6,6,6) in the p1,p2,p3 plane. This
            is useful in the case that, e.g., a set of diffusion parameters are desired to be set 
            in unison to an 2nd order and a 4th order method.

            If this is True, the input name must be a single string, containing multiple namelist 
            settings, separated by commas, e.g. 'p1,p2,p3'. Each input value must similarly be a
            string, with values separated by commas. When split on commas, the number of elements 
            in the values string must match the number elements in the names string. Whitespaces 
            will be stripped from the strings in any case.
            If True, group_labels must be passed.
        group_labels : string or (N,) string array
            Label to give the group, so that automatically-generated clone directory names do not 
            become obnoxious. Required if group is True.
        '''
     
        # ---------- check user input ----------

        names = np.atleast_1d(names)
        group_labels = np.atleast_1d(group_labels)
        for i in range(len(names)):
            name = names[i]
            
            assert name not in self.param_names, \
            'parameter with name {} already exists in lattice'.format(name)
            
            if ',' in name and not group:
                warnings.warn('comma detected in name {}; maybe expand should have received \
                               group=True?'.format(name))
            
            if(group):
                # remove whitespace
                name = ''.join(name.split())
                names[i] = name
                values[i] = ''.join(values[i].split())
                
                assert group_labels[i] is not None, 'group_label must be passed if group is True'
                assert group_labels[i] not in self.paramgroup_labels, \
                       'group_label with name {} already exists in the lattice'.format(group_labels[i])
                
                all_groupparams = np.ravel([s.split(',') for s in 
                                  np.array(self.param_names)[np.where(self.paramgroup_mask)]]).tolist()
                for groupparam in name.split(','):
                    assert groupparam not in all_groupparams, \
                           'parameter with name {} aleady exists in the lattice'.format(groupparam)

                assert len(np.unique(name.split(','))) == len(name.split(',')), \
                       'parameter group {} contains duplicates'.format(name) 
        
        call_err = 'either (\'values\') or (\'limits\' and \'nsamples\') must be passed, not both'
       

        # ---------- insert parameter into lattice ----------

        if(values is None):
            assert limits is not None and nsamples is not None, call_err
            assert group is False, 'auto-generation of values from limits can\
                                    not be used if group=True; use values'

            # ----- values beign generated by limits
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
            assert limits is None and nsamples is None, call_err
            
            # ----- values explicitly defined by user
            values = np.atleast_2d(values)
            
            assert len(names) == len(values),\
                   'args \'names\'  and \'values\' must be of equal length'
            if(group):
                for i in range(len(names)):
                    for j in range(len(values[i])):
                        assert len(names[i].split(',')) == len(values[i][j].split(',')), \
                        'mismatch in number of group parameters ({}) and values ({})'.format(
                        names[i], values[i][j])

            # build new dimensions
            self.param_names.extend(names)
            self.param_vectors.extend(values)

        # flag any parameters to be updated via xmlchange
        if(xmlchange):
            self.xml_mask.extend([1]*len(names))
        else:
            self.xml_mask.extend([0]*len(names))
        
        # flag any parameter groups
        if(group):
            self.paramgroup_mask.extend([1]*len(names))
            self.paramgroup_labels.extend(group_labels)
        else:
            self.paramgroup_mask.extend([0]*len(names))
        
        # build the lattice
        self._build_lattice()
    
    
    # ------------------------------------------------------------------------------


    def filter(self, mask):
        '''
        Filters out undesired run configurations from the lattice

        Parameters
        ----------
        mask : bool array with length matching the number of lattice points
        '''
        
        mask = np.array(mask, dtype=bool)
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
        
        if(not self.nofill):
            grid = np.meshgrid(*self.param_vectors)
            points = np.vstack(list(map(np.ravel, grid)))
            self._lattice = np.core.records.fromarrays(points, names=self.param_names)
        else:
            points = np.vstack(self.param_vectors)
            self._lattice = np.core.records.fromarrays(points, names=self.param_names)

    # ------------------------------------------------------------------------------


    def create_clones(self, root_case, top_clone_dir=None, top_output_dir=None, 
                      clone_prefix=None, clone_sfx=None, cime_dir=cime, overwrite=False, clean_all=False):
        '''
        clone the root_case CESM CIME case per each point on the lattice, and edit the
        namelist file at cloned_case/user_nl_{self.component} with the content of that 
        point.

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
        clone_prefix : string
            prefix of each clone case. Default is None, in which case the name of the 
            root case will be used. The full cloned case location is then
            {top_clone_dir}/{clone_prex}_{P1}{V1}_{P2}{V2}_....
            where P are the names of the namelist settings on the lattice (constant for all
            clones), and v are their values (unique for each clone)
        clone_sfx : string array
            list of strings containing content to append to end of each clone directory. Must
            be same length as number of points in lattice. Default is None, in which case, each 
            string will be a concatenation of each parameter value of each clone's position in 
            the lattice parameter space, separated by '__'.
        cime_dir : string
            Location of the cime/scripts directory within cesm2.2
        overwrite : bool
            Whether or not to overwrite preexisting clone cases found in top_clone_dir with 
            name conflicts. Default is False, in which case an error will be thrown in this 
            event. Leave as Default to be safe unless you know you need it to be otherwise.
        clean_all : bool
            Whether or not to completely remove content of top_clone_dir and top_output_dir
            before creating clones. This is useful if the previous run of this function was known
            to contain mistakes. Default is False, which it probably should be, and you porobably
            shouldn't change it. Definitely don't change it if top_clone_dir and top_output_dir 
            were not passed (unless you enjoy rebuilding your CESM cases, or you know exactly what
            you're doing).
        '''

        if(self._lattice is None):
            raise RuntimeError('Lattice must first be built by calling expand()')
        if(not os.path.isdir(root_case)):
            raise RuntimeError('Root case {} does not exist'.format(root_case))
        
        params = self._lattice.dtype.names
        
        # enforce defaults
        if(top_clone_dir is None):
            top_clone_dir = '/'.join(root_case.split('/')[:-1])
        if(clone_prefix is None):
            clone_prefix = root_case.split('/')[-1]

        # clean clone and output dirs if user specified
        if(clean_all):
            clonedir_exist = os.path.isdir(top_clone_dir)
            outdir_exist = os.path.isdir(top_output_dir)
            if(clonedir_exist or outdir_exist):
                print('\n\n ========== REMOVING {} and {} =========='.format(
                       top_clone_dir, top_output_dir))
                input('Press Enter to continue with deletion...')
                if(clonedir_exist): shutil.rmtree(top_clone_dir)
                if(outdir_exist): shutil.rmtree(top_output_dir)
            else:
                print('Nothing to clean')
            
        # create directories if not exist 
        if(not os.path.isdir(top_clone_dir)):
            print('creating {}'.format(top_clone_dir))
            Path(top_clone_dir).mkdir(parents=True)
        if(top_output_dir is not None):
            if(not os.path.isdir(top_output_dir)):
                print('creating {}'.format(top_output_dir))
                Path(top_output_dir).mkdir(parents=True) 
             
        print('\n\n =============== CREATING {} CLONES ===============\n'.format(len(self._lattice)))

        # clone the root case per lattice point
        for i in range(len(self._lattice)):
            
            values = self._lattice[i]
            print('\n --------------- creating clone with {} = {} ---------------\n'.format(
                   params, values))
            
            # set clone directory suffix
            if clone_sfx is None:
                sfx = '__'.join(['{}_{}'.format(params[j], values[j]) for j in range(len(values))])
            else: 
                clone_sfx = np.atleast_1d(clone_sfx)
                if(len(clone_sfx) != 1 and len(clone_sfx) != len(self._lattice)):
                    raise RuntimeError('clone_sfx must be a single string, or length of'\
                                       'clone_sfx must match number of lattice points')
                if(len(clone_sfx) > 1):
                    sfx = clone_sfx[i]
                else:
                    sfx = clone_sfx[0]

            new_case = '{}/{}__{}'.format(top_clone_dir, clone_prefix, sfx)
            new_case_out = '{}/{}__{}'.format(top_output_dir, clone_prefix, sfx)
            
            # check that this clone does not already exist; if so, handle
            if(os.path.isdir(new_case) and overwrite == False):
                raise RuntimeError('clone at {} already exists!'.format(new_case)) 
            if(os.path.isdir(new_case_out) and overwrite == False):
                raise RuntimeError('output at {} already exists!'.format(new_case_out)) 
            if(os.path.isdir(new_case) and overwrite == True):
                print('overwrite option set to True; overwriting existing case at {}'.format(new_case))
                shutil.rmtree(new_case)
            if(os.path.isdir(new_case_out) and overwrite == True):
                print('overwrite option set to True; overwriting existing output at {}'.format(
                                                                                        new_case_out))
                shutil.rmtree(new_case_out)

            # call the cloning script
            if(top_output_dir is not None):
                cmd = '{}/create_clone --case {} --clone {} --cime-output-root {} --keepexe'.format(
                       cime_dir, new_case, root_case, top_output_dir)
            else:
                cmd = '{}/create_clone --case {} --clone {} --keepexe'.format(
                       cime_dir, new_case, root_case)
            subprocess.run(cmd.split(' '))
            self.clone_dirs.append(new_case)
            
            # --- edit the user_nl_{component} file ---
            
            # purge current occurences of the parameters present in the lattice
            with open('{}/user_nl_{}'.format(new_case, self.component), 'r+') as f:
                
                entries = f.readlines()
                f.seek(0)
                for e in entries:
                    param = ''.join(e.split()).split('=')[0]
                    if(param not in params): 
                        f.write(e)
                f.truncate()
                nl = f.read()
            
            # write new parameter choices
            with open('{}/user_nl_{}'.format(new_case, self.component), 'a') as f:
                if not nl.endswith('\n'):
                    f.write('\n')
                
                for j in range(len(params)):
                    
                    if(self.paramgroup_mask[j] == 1):
                        # write all parameter choices in this group to user_nl_{self.component}
                        group_params = params[j].split(',')
                        group_values = values[j].split(',')
                        for k in range(len(group_params)):
                            f.write('{} = {}\n'.format(group_params[k], group_values[k]))
                    
                    if(self.xml_mask[j] == 1):
                        # write parameter choice to env_run.xml via xmlchange
                        os.chdir(new_case)
                        xmlcmd = '{}/xmlchange {}={}'.format(new_case, params[j], values[j])
                        subprocess.run(xmlcmd.split(' '))
                    
                    else:
                        # write parameter choice to user_nl_{self.component}
                        f.write('{} = {}\n'.format(params[j], values[j]))


    # ------------------------------------------------------------------------------


    def submit_clone_runs(self, dry=False):
        '''
        Submit runs of the cloned cases created by self.create_clones()

        Parameters
        ----------
        dry : boolean
            Whether or not to do a dry run, which just prints the location of each
            submission script which is about to be called. Defaults to False.
        '''
        
        if(len(self.clone_dirs) == 0):
            raise RuntimeError('Clone cases must first be created by calling expand()')
            
        for clone in self.clone_dirs:
            
            os.chdir(clone)
            submit = '{}/case.submit'.format(clone)
            
            print('\n\n=============== submitting job from {} ===============\n'.format(submit))
            if(dry):
                print(submit)
            else:
                subprocess.run(submit)


    # ------------------------------------------------------------------------------


    def vis_planes(self):
        '''
        Visualizes the lattice as a GTC, with a subplot per parameter pair
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
