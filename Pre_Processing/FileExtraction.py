
from imctools.io.mcd.mcdparser import McdParser
import os
from pathlib import Path
from tifffile import imread, imwrite
import numpy as np
import pandas as pd
import shutil

wd = os.getcwd()
print(str('This is your main folder: '+wd))

# Define all paths
mcd_path = str(wd+'/MCD')
ome_path = str(wd+'/OME')
tiff_path = str(wd+'/TIFF')
#stack_path = str(wd+'/Stack')

# Create subfolders to save files
Path(ome_path).mkdir(parents=True, exist_ok=True)
Path(tiff_path).mkdir(parents=True, exist_ok=True)
#Path(stack_path).mkdir(parents=True, exist_ok=True)

# Get list of all MCD files in the folder
files = []
for file in os.listdir(mcd_path):
    if file.endswith(".mcd"):
        files.append(file)

# Read in file with metal tag to channel dictionary
print('Reading in channel.csv file - please make sure there are no repeated names or it will overwrite data.\nThis is the list:')
dict_file = pd.read_csv('channels.csv')
markers = dict(dict_file.values)
print(markers)

while True:
    try:
        file_redo = int(input(str("If the list is not accurate and the file has been updated, do you want to read in the updated file?\n'1' for yes - The file has been updated; please read in again\n'2' for no - The file is accurate\nEnter value: ")))
        break
    except ValueError:
        print("Oops!  That was not a valid input.  Try again...")

if file_redo == 1:
    print('Reading in updated channel.csv file')
    dict_file = pd.read_csv('channels.csv')
    markers = dict(dict_file.values)
    print(markers)

print('Moving on to TIFF extraction')

# Loop through all MCD files to get ROIs, save OME.TIFF files, convert/save .TIFF files
for f in files:
    # Get ROI name
    roi = f.rsplit( ".", 1 )[ 0 ]

    # Read MCD file
    fn_mcd = os.path.join(mcd_path, f)
    parser = McdParser(fn_mcd)

    # Get original metadata in XML format
    xml = parser.get_mcd_xml()

    # Get parsed session metadata (i.e. session -> slides -> acquisitions -> channels, panoramas data)
    session = parser.session

    # Get all acquisition IDs
    ids = parser.session.acquisition_ids

    # select channels of interest
    channels = list(markers.keys())

    # Create ROI Subfolder inside OME folder
    # Get acquisition data
    # Save individual .OME.TIFF files by ROI and channel
    ac_data = []
    m=0
    for i in ids:
        try:
            ac_data.append(parser.get_acquisition_data(i))
            #print(ac_data[m])

            Path(str(ome_path+'/'+roi+'_00'+str(i))).mkdir(parents=True, exist_ok=True)

            for channel in channels:
                fn_out = str(ome_path+'/'+roi+'_00'+str(i)+'/'+markers.get(channel)+'.ome.tiff')
                ac_data[m].save_ome_tiff(fn_out, dtype='uint16', names=[channel])  
        except:
            pass

        m+=1
            
    # Create ROI Subfolder inside TIFF folder
    # Read/convert .OME.TIFF to individual .TIFF files by ROI and channel and save them
    for i in ids:
        try:
            Path(str(tiff_path+'/'+roi+'_00'+str(i))).mkdir(parents=True, exist_ok=True)
        except:
            continue

        # Check for empty ROIs and delete folder if necessary to avoid errors during pre-processing    
        check_file = os.path.isfile(str(ome_path+'/'+roi+'_00'+str(i)+'/'+markers.get(channels[0])+'.ome.tiff'))
        if check_file == False:
            shutil.rmtree(Path(str(tiff_path+'/'+roi+'_00'+str(i))))
            print(f"ROI {Path(str(roi+'_00'+str(i)))} is an empty acquisition and does not have TIFFs")

        try:
            image = {}
            for channel in channels:
                ome_tiff_path = str(ome_path+'/'+roi+'_00'+str(i)+'/'+markers.get(channel)+'.ome.tiff')
                image.update({channel: imread(ome_tiff_path)})
                
                fn_out = str(tiff_path+'/'+roi+'_00'+str(i)+'/'+markers.get(channel)+'.tiff')
                imwrite(fn_out, image.get(channel))    
        except:
            continue
    
    # as mcd object is using lazy loading memory maps, it needs to be closed
    parser.close()

shutil.rmtree(ome_path)

print('All TIFFs have been extracted')