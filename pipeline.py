import utils.path as path

import subprocess


'''Download data'''
def download_data():
    '''12-1AM 8 days'''
    download_file = 'nsidc-download_VNP30.001_2022-07-05.py'
    '''12-1PM 8 days'''
    #download_file =
    '''12-1AM 2 years'''
    #download_file =
    '''12-1PM 2 years'''
    #download_file =

    '''Run the python script to download the data'''
    subprocess.run(['python', download_file], cwd='./utils')


'''Move the nc files to the raw data directory'''
def get_raw_data():
    '''Call the main class'''
    my_path = path.Path()
    '''Name the different paths as variables'''
    utils_path = my_path._utils_directory()
    data_path = my_path._data_folder

    '''Call the method to move .nc files and remove .mxl files'''
    my_path.move_to_directory(utils_path, data_path)


'''Get the time series of mean tempearture values per day in a '''
def get_time_series():
    '''Call the super-class'''
    datasets = path.Dataset()
    '''Calculate and save the temperature-per-day time series'''
    temperature_day = datasets.mean_time_series()
    '''Calculate and save the temperature day-by-day variations time series'''
    temperature_variation = datasets.variation_time_series()

    return temperature_day, temperature_variation


def main():
    download_data()
    get_raw_data()
    get_time_series()




if __name__ == '__main__':
    main()