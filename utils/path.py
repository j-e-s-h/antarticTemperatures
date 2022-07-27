import os
import re
import shutil
import netCDF4 as nc
import numpy as np


class Path():


    '''
    Initialize the class with the following parameters:
     - Paths of the father directory, raw data directory and interim data directory
     - The extension of the downloaded files
     - The regular expression that is going to be used later
    '''
    def __init__(self):
        self._origin_folder = os.getcwd()
        self._data_folder = os.path.join(self._origin_folder, 'data/raw/')
        #self._data_folder = os.path.join(self._origin_folder, os.pardir, 'data/raw/')
        self._interim_data_folder = os.path.join(self._origin_folder, 'data/interim/')
        self.__extension = 'nc'
        self.__regex = '(.*' + self.__extension + '$)'


    '''
    This method presents a way to move the selected files with extension "nc"
    from the actual path ("/utils") to the "/data/raw" directory, and delete 
    the ones with "xml" extension.
    '''
    def move_to_directory(self, origin_path, destination_path):

        for file_name in os.listdir(origin_path):
            source = origin_path + str(file_name)
            destination = destination_path + file_name

            '''
            Move the .nc files and eliminate duplicates from destination folder 
            and remove the .xml files by using regex
            '''
            if re.search(self.__regex, source):
                if os.path.exists(destination):
                    print('{} is already in this directory'.format(file_name))
                    os.remove(source)
                else:
                    shutil.move(source, destination)
                    print('Moved:', file_name)
            elif re.search('(.*xml$)', source):
                os.remove(source)
        print('Files are in the "data/raw" directory')


    '''Shortcut to list the files within a folder'''
    def directory_content(self, path):
        return os.listdir(path)

    '''Shortcut to change directories'''
    def change_path(self, path):
        return os.chdir(path)

    '''Shortcut to see the root of the actual directory'''
    def get_path(self):
        return os.getcwd()

    '''Utils folder path'''
    def _utils_directory(self):
        return os.path.join(self._origin_folder, 'utils/')
        #return os.path.join(self._origin_folder, os.pardir, 'utils/')




class Dataset(Path):

    '''
    Since a time period of two hours exists, it is necessary to have
    only one dataset per day
    '''
    def __init__(self):
        super().__init__()

        '''Create a list with a unique dataset per day'''
        datasets = []
        for file_name in os.listdir(self._data_folder):
            if re.search('(.*nc$)', file_name):
                file_path = self._data_folder + file_name
                ds = nc.Dataset(file_path)
                datasets.append(ds.__dict__['ProductionTime'][:10])
            else: continue

        '''Filter the unique dates with their rerspective index'''
        _, idx = np.unique(datasets, return_index=True)
        self.idx = idx


    '''
    Method that calculates the mean of N-group of datasets and their outliers.
    
    Output.
     - numpy array of mean values
     - list of the number of outliers per day
    '''
    def mean_time_series(self, return_outliers_per_day=False):
        temperature_per_day = []
        outliers_per_day = []

        '''
        Per file the "/data/raw" directory, with netCDF4 to read the path file,
        then call the temperature method and save the respective values
        '''
        for i in range(len(os.listdir(self._data_folder))):
            if i in self.idx:
                file_path = self._data_folder + os.listdir(self._data_folder)[i+1]
                ds = nc.Dataset(file_path)
                '''Use conditionals about the parameters to get the respective outputs'''
                if return_outliers_per_day==True:
                    T, outliers_idx= self._mean_temperature(ds, return_outliers_index=True)
                    temperature_per_day.append(T)
                    outliers_per_day.append(np.array(outliers_idx).shape[-1])
                else:
                    T = self._mean_temperature(ds)
                    temperature_per_day.append(T)

        '''Save the temperature data in "data/interim" folder'''
        name_of_file = '{}days_temperature'.format(len(temperature_per_day))
        self._save_data(temperature_per_day, name_of_file)

        if return_outliers_per_day==True: 
            return np.round(np.array(temperature_per_day), decimals=2), outliers_per_day
        else: return np.round(np.array(temperature_per_day), decimals=2)


    '''
    Method that calculates the mean of N-group of datasets and returns an array
    with the variations of temperature per day
    '''
    def variation_time_series(self):
        temperatures = []

        '''
        The following part of the code is the same as in "mean_time_series"
        method
        '''
        for i in range(len(os.listdir(self._data_folder))):
            if i in self.idx:
                file_path = self._data_folder + os.listdir(self._data_folder)[i+1]
                ds = nc.Dataset(file_path)
                T = self._mean_temperature(ds)
                temperatures.append(T)

        '''Calculate the differences per day'''
        diff = [temperatures[i+1] - temperatures[i] for i in range(len(temperatures)-1)]

        '''Save file'''
        name_of_file = '{}days_temperature_var'.format(len(diff)+1)
        self._save_data(diff, name_of_file)
        return np.round(diff, decimals=2)


    '''
    A method that gives the format of array to the data mask and creates
    boundaries to do the calculation of the mean.

    Output. 
     - mean of the dataset
     - list of arrays with the outliers index - if return_outliers_index=True
    '''
    def _mean_temperature(self, dataset, return_outliers_index=False):
        '''
         - Create list with common values - check earthdata user guide
         - Create an outlier list to count the quantity of them in each day
        '''
        common_values = [0,100,1100,2500,3700,3900,65533]
        outliers_index = []

        '''
        The following commands are used to get into the data matrix by 
        using netCDF4 library
        '''
        grp = dataset.createGroup('IST_Data')
        ist = grp['IST']
        array = ist[:].data
        cleaned_array = array
        
        '''
        Make a filter to eliminate values that are not useful.
        Eliminate common values and create an upper limit to get rid of the
        values above 300K, append those index values in the oultiers list

        Note. These outlier index correspond to the final 
        '''
        for val in common_values:
            cleaned_array = cleaned_array[~(cleaned_array==val)]
        if np.any(cleaned_array > 300):
            if return_outliers_index==True:
                [outliers_index.append(i) for i in np.where(cleaned_array > 300)]
            cleaned_array = cleaned_array[~(cleaned_array > 300)] 
        if return_outliers_index==True: 
            return cleaned_array.mean(), np.squeeze(outliers_index) 
        else: return cleaned_array.mean()


    '''Save the data numpy array in "data/interim" folder'''
    def _save_data(self, array, name_of_file=str):
        try: 
            np.savetxt(self._interim_data_folder + name_of_file + '.csv',
                        array, delimiter=',')
        except:
            raise ValueError('The name of the new file must be a string.')



    def _check_missing_data(self):
        #for i in range(len(os.listdir(data_path))):
        #    if i in idx:
        #        file_path = data_path + os.listdir(data_path)[i+1]
        #print(file_path[58:])
        #print(file_path[86:89])
        pass