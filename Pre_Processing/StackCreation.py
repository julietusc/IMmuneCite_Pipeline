
import os
from pathlib import Path
from tifffile import imread, imwrite
import numpy as np
import pandas as pd

wd = os.getcwd()
print(str('This is your main folder: '+wd))

# Path where pre-processed output files are located
output_file_path = str(wd+"/Preprocessing_Outputs")

# Define path
stack_path = str(wd+'/Stack')

# Create subfolder to save files
Path(stack_path).mkdir(parents=True, exist_ok=True)

# Get list of all ROIs in the Preprocessing_Outputs folder
processed_files = []
for file in os.listdir(output_file_path):
    if file.endswith(".DS_Store"):
        continue
    else:
        processed_files.append(file)

# Read in file with metal tag to channel dictionary
dict_file = pd.read_csv('channels.csv')
markers = dict(dict_file.values)

# List of channels
channels = list(markers.values())

# Loop through each ROI to create stack with pre-processed outputs
for f in processed_files:
    
    # Read in TIF files with pre-processed output
    outputs = {}
    for channel in channels:
        output_tiff_path = str(output_file_path+'/'+f+'/'+channel+'.tiff')
        outputs.update({channel: imread(output_tiff_path)})
        
    # Create Stack and save
    stack = np.zeros((len(channels),outputs.get(channels[0]).shape[0],outputs.get(channels[0]).shape[1]),np.uint16)
    n=0
    for channel in channels:
        stack[n,:,:] = outputs.get(channel)
        n+=1
    fn_out = str(stack_path+'/'+f+'.tiff') 
    imwrite(fn_out, stack)

print("Order of tiff images in stack file: ")
print(channels)
print("TIFF stacks have been created")