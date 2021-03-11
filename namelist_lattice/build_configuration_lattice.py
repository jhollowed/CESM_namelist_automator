import pdb
import numpy as np

class configuration_lattice:
    def __init__(self):
        '''
        This class constructs a configuration lattice object, which organizes a lattice of
        positions in paramter space, intended for automating the running of several 
        simulation runs with varying namelist settings.
        '''
        self.param_vectors = []
        self.param_names = []
        self._lattice = None

    @property
    def lattice(self):
        if(len(self.param_names) < 2): 
            raise RuntimeError('must add at least 2 dimensions to build lattice')
        else:
            return self._lattice


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
        multiple_dims = hasattr(names, '__len__') and (not isinstance(names, str))
       
        if(values is None):
            assert limits is not None and nsamples is not None, err
            
            self.param_names.extend(names)
            if multiple_dims:
                assert len(names) == len(limits) and len(names) == len(nsamples),\
                       'args \'names\', \'limits\', and \'nsamples\' must all be of equal length'
               
                # build new dimensions
                for i in range(len(names)):
                    vals = np.linspace(limits[i][0], limits[i][1], nsamples[i])
                    self.param_vectors.append(vals)
            
            else:    
                # the case that only one dimension is being added
                vals = np.linspace(limits[0], limits[1], nsamples)
                self.param_vectors.append(vals)
                
        else:
            assert limits is None and nsamples is None, err
            self.param_names.extend(names)
            if multiple_dims:
                assert len(names) == len(values),\
                       'args \'names\'  and \'values\' must be of equal length'

                # build new dimensions
                self.param_vectors.extend(values)
            
            else:    
                # the case that only one dimension is being added
                self.param_vectors.append(values)

        if(len(self.param_names) > 1):
            self._build_lattice()
        

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

        
        
        
    

