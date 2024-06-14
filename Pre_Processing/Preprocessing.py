
from imctools.io.mcd.mcdparser import McdParser
import os
from pathlib import Path
from tifffile import imread, imwrite, imshow
import numpy as np
from scipy.ndimage import gaussian_filter, minimum_filter, uniform_filter
from skimage import measure
import pandas as pd
import matplotlib.pyplot as plt
import shutil

wd = os.getcwd()
print(str('This is your main folder: '+wd))

tiff_path = "TIFF/"

# Get list of all ROIs
files = []
for file in os.listdir(tiff_path):
    if file.endswith(".DS_Store"):
        continue
    else:
        files.append(file)

# Create output folders
for fi in files:
    output_file_path = str(wd+"/Preprocessing_Outputs/"+fi+"/")
    Path(output_file_path).mkdir(parents=True, exist_ok=True)

# Get list of all channels
dict_file = pd.read_csv('channels.csv')
markers = dict(dict_file.values)
channels = list(markers.values())
    
print("List of all channels: ")
print(channels)


# Pre-processing
for marker in channels:

    for fs in files:
        
        print("ROI being pre-processed: "+fs)

        check_file = os.path.isfile(str(tiff_path+fs+'/'+channels[0]+'.tiff'))
        if check_file == False:
            print(f'ROI {fs} is an empty folder')

        maui = {}
        for channel in channels:
            try:
                maui.update({channel: imread(str(tiff_path+fs+'/'+channel+'.tiff'))})
            except:
                continue

        while True:
            try:
                process_channel = int(input(str("Do you want to pre-process "+marker+"?\n'1' for yes\n'2' for no - take raw signal as is\n'3' for no - already pre-processed\nEnter value: ")))
                if process_channel in (1,2,3):
                    break
                else:
                    print("Oops!  That was not a valid input.  Try again...")
            except ValueError:
                print("Oops!  That was not a valid input.  Try again...")
                
        if process_channel == 3:
            check_file = os.path.isfile(str("Preprocessing_Outputs/"+fs+"/"+marker+".tiff"))
            if check_file == False:
                print(f"Preprocessing_Outputs/{fs}/{marker}.tiff doesn't exist - might not have been pre-processed yet")
                while True:
                    try:
                        process_channel = int(input(str("Do you want to pre-process "+marker+"?\n'1' for yes\n'2' for no - take raw signal as is\n'3' for no - already pre-processed\nEnter value: ")))
                        if process_channel in (1,2,3):
                            break
                        else:
                            print("Oops!  That was not a valid input.  Try again...")
                    except ValueError:
                        print("Oops!  That was not a valid input.  Try again...")
            if check_file == True:
                break

        if process_channel == 2:
            for fe in files:
                raw_tiff = imread(str(tiff_path+fe+'/'+marker+'.tiff'))
                path_save = str("Preprocessing_Outputs/"+fe+"/"+marker+".tiff")
                imwrite(path_save, raw_tiff)
            break

        if process_channel == 1:
            print(str('Currently working on the following channel: '+marker))

            ##################################
            ####### BACKGROUND REMOVAL #######
            ##################################

            while True:
                try:
                    background = input("Enter background channel: ")
                    h = maui.get(background)
                    h.shape
                    break
                except AttributeError:
                    print("Oops!  That was not a valid channel.  Try again...")

            print(str("Background channel chosen: "+background))

            h = maui.get(background)
            f = maui.get(marker)

            while True:
                try:
                    c = float(input("Enter background removal cap value: ")) # 100
                    break
                except ValueError:
                    print("Oops!  That was not a valid input.  Try again...")

            while True:
                try:
                    s1 = float(input("Enter gaussian radius value: ")) # 3
                    break
                except ValueError:
                    print("Oops!  That was not a valid input.  Try again...")

            while True:
                try:
                    t = float(input("Enter threshold value to binarize image array: ")) # 0.5
                    break
                except ValueError:
                    print("Oops!  That was not a valid input.  Try again...")

            while True:
                try:
                    v = float(input("Enter removal value: ")) # 4
                    break
                except ValueError:
                    print("Oops!  That was not a valid input.  Try again...")

            h_capped = np.zeros((h.shape[0],h.shape[1]),np.uint16)
            m=h.shape[0]
            n=h.shape[1]

            for x in range(0,m):
                for y in range(0,n):
                    if h[x,y] <= c:
                        h_capped[x,y] = h[x,y]
                    elif h[x,y] > c:
                        h_capped[x,y] = c

            h_blurred = gaussian_filter(h_capped, sigma=s1)
            h_rescaled = h_blurred/h_blurred.max()

            h_mask = np.zeros((h.shape[0],h.shape[1]),np.uint16)
            m=h.shape[0]
            n=h.shape[1]

            for x in range(0,m):
                for y in range(0,n):
                    if h_rescaled[x,y] >= t:
                        h_mask[x,y] = 1
                    elif h_rescaled[x,y] < t:
                        h_mask[x,y] = 0
                        
            f_removed = np.zeros((f.shape[0],f.shape[1]))
            m=f.shape[0]
            n=f.shape[1]

            for x in range(0,m):
                for y in range(0,n):
                    if h_mask[x,y] == 0:
                        f_removed[x,y] = f[x,y]
                    elif h_mask[x,y] == 1:
                        f_removed[x,y] = f[x,y] - v
                    
            f_clean = np.zeros((f.shape[0],f.shape[1]), np.uint16)
            m=f.shape[0]
            n=f.shape[1]

            for x in range(0,m):
                for y in range(0,n):
                    if f_removed[x,y] >= 0:
                        f_clean[x,y] = f_removed[x,y]
                    elif f_removed[x,y] < 0:
                        f_clean[x,y] = 0
                        
            print("Background removal complete")

            imshow(maui.get(marker), cmap='viridis',vmin=0, vmax=5, title=str("Raw signal: "+marker)) + \
            imshow(f_clean, cmap='viridis',vmin=0, vmax=5, title=str("Background removal: "+marker))
            plt.show()

            while True:
                try:
                    user_input1 = int(input("Next step:\n'1' for background removal re-do\n'2' for background removal with second channel\n'3' for noise removal\nEnter value: "))
                    if user_input1 in (1,2,3):
                        break
                    else:
                        print("Oops!  That was not a valid input.  Try again...")
                except ValueError:
                    print("Oops!  That was not a valid input.  Try again...")
        
            while user_input1 == 1:
                print("Background removal re-do")

                # Re-doing background removal

                while True:
                    try:
                        c = float(input("Enter background removal cap value: ")) # 100
                        break
                    except ValueError:
                        print("Oops!  That was not a valid input.  Try again...")

                while True:
                    try:
                        s1 = float(input("Enter gaussian radius value: ")) # 3
                        break
                    except ValueError:
                        print("Oops!  That was not a valid input.  Try again...")

                while True:
                    try:
                        t = float(input("Enter threshold value to binarize image array: ")) # 0.5
                        break
                    except ValueError:
                        print("Oops!  That was not a valid input.  Try again...")

                while True:
                    try:
                        v = float(input("Enter removal value: ")) # 4
                        break
                    except ValueError:
                        print("Oops!  That was not a valid input.  Try again...")

                h_capped = np.zeros((h.shape[0],h.shape[1]),np.uint16)
                m=h.shape[0]
                n=h.shape[1]

                for x in range(0,m):
                    for y in range(0,n):
                        if h[x,y] <= c:
                            h_capped[x,y] = h[x,y]
                        elif h[x,y] > c:
                            h_capped[x,y] = c

                h_blurred = gaussian_filter(h_capped, sigma=s1)
                h_rescaled = h_blurred/h_blurred.max()

                h_mask = np.zeros((h.shape[0],h.shape[1]),np.uint16)
                m=h.shape[0]
                n=h.shape[1]

                for x in range(0,m):
                    for y in range(0,n):
                        if h_rescaled[x,y] >= t:
                            h_mask[x,y] = 1
                        elif h_rescaled[x,y] < t:
                            h_mask[x,y] = 0
                            
                f_removed = np.zeros((f.shape[0],f.shape[1]))
                m=f.shape[0]
                n=f.shape[1]

                for x in range(0,m):
                    for y in range(0,n):
                        if h_mask[x,y] == 0:
                            f_removed[x,y] = f[x,y]
                        elif h_mask[x,y] == 1:
                            f_removed[x,y] = f[x,y] - v
                        
                f_clean = np.zeros((f.shape[0],f.shape[1]), np.uint16)
                m=f.shape[0]
                n=f.shape[1]

                for x in range(0,m):
                    for y in range(0,n):
                        if f_removed[x,y] >= 0:
                            f_clean[x,y] = f_removed[x,y]
                        elif f_removed[x,y] < 0:
                            f_clean[x,y] = 0
                            
                print("Background removal complete")

                imshow(maui.get(marker), cmap='viridis',vmin=0, vmax=5, title=str("Raw signal: "+marker)) + \
                imshow(f_clean, cmap='viridis',vmin=0, vmax=5, title=str("Background removal: "+marker))
                plt.show()

                while True:
                    try:
                        user_input1 = int(input("Next step:\n'1' for background removal re-do\n'2' for background removal with second channel\n'3' for noise removal\nEnter value: "))
                        if user_input1 in (1,2,3):
                            break
                        else:
                            print("Oops!  That was not a valid input.  Try again...")
                    except ValueError:
                        print("Oops!  That was not a valid input.  Try again...")

            while user_input1 == 2:
                print("Second round of background removal")

                # Second background removal round

                while True:
                    try:
                        background_second = input("Enter background channel for second round removal: ")
                        h = maui.get(background_second)
                        h.shape
                        break
                    except AttributeError:
                        print("Oops!  That was not a valid channel.  Try again...")

                print(str("Background channel chosen for second round removal: "+background_second))

                h = maui.get(background_second)
                f = f_clean

                while True:
                    try:
                        c_bg2 = float(input("Enter background removal cap value: ")) # 100
                        break
                    except ValueError:
                        print("Oops!  That was not a valid input.  Try again...")

                while True:
                    try:
                        s1_bg2 = float(input("Enter gaussian radius value: ")) # 3
                        break
                    except ValueError:
                        print("Oops!  That was not a valid input.  Try again...")

                while True:
                    try:
                        t_bg2 = float(input("Enter threshold value to binarize image array: ")) # 0.5
                        break
                    except ValueError:
                        print("Oops!  That was not a valid input.  Try again...")

                while True:
                    try:
                        v_bg2 = float(input("Enter removal value: ")) # 4
                        break
                    except ValueError:
                        print("Oops!  That was not a valid input.  Try again...")

                h_capped = np.zeros((h.shape[0],h.shape[1]),np.uint16)
                m=h.shape[0]
                n=h.shape[1]

                for x in range(0,m):
                    for y in range(0,n):
                        if h[x,y] <= c_bg2:
                            h_capped[x,y] = h[x,y]
                        elif h[x,y] > c_bg2:
                            h_capped[x,y] = c_bg2

                h_blurred = gaussian_filter(h_capped, sigma=s1_bg2)
                h_rescaled = h_blurred/h_blurred.max()

                h_mask = np.zeros((h.shape[0],h.shape[1]),np.uint16)
                m=h.shape[0]
                n=h.shape[1]

                for x in range(0,m):
                    for y in range(0,n):
                        if h_rescaled[x,y] >= t_bg2:
                            h_mask[x,y] = 1
                        elif h_rescaled[x,y] < t_bg2:
                            h_mask[x,y] = 0
                            
                f_removed = np.zeros((f.shape[0],f.shape[1]))
                m=f.shape[0]
                n=f.shape[1]

                for x in range(0,m):
                    for y in range(0,n):
                        if h_mask[x,y] == 0:
                            f_removed[x,y] = f[x,y]
                        elif h_mask[x,y] == 1:
                            f_removed[x,y] = f[x,y] - v_bg2
                        
                f_clean = np.zeros((f.shape[0],f.shape[1]), np.uint16)
                m=f.shape[0]
                n=f.shape[1]

                for x in range(0,m):
                    for y in range(0,n):
                        if f_removed[x,y] >= 0:
                            f_clean[x,y] = f_removed[x,y]
                        elif f_removed[x,y] < 0:
                            f_clean[x,y] = 0
                            
                print("Background removal complete")

                imshow(maui.get(marker), cmap='viridis',vmin=0, vmax=5, title=str("Raw signal: "+marker)) + \
                imshow(f_clean, cmap='viridis',vmin=0, vmax=5, title=str("Background removal: "+marker))
                plt.show()

                while True:
                    try:
                        user_input1 = int(input("Next step:\n'1'\n'2' for background removal with second channel re-do\n'3' for noise removal\nEnter value: "))
                        if user_input1 in (1,2,3):
                            break
                        else:
                            print("Oops!  That was not a valid input.  Try again...")
                    except ValueError:
                        print("Oops!  That was not a valid input.  Try again...")

            print("Moving on to noise removal")

            ##################################
            ######### NOISE REMOVAL ##########
            ##################################

            while True:
                try:
                    min = float(input("Enter minimum threshold value: ")) # 1
                    break
                except ValueError:
                    print("Oops!  That was not a valid input.  Try again...")

            while True:
                try:
                    un = float(input("Enter uniform threshold value: ")) # 9
                    break
                except ValueError:
                    print("Oops!  That was not a valid input.  Try again...")

            f_clean_noise_temp=minimum_filter(f_clean,size=min)
            f_clean_noise_temp=uniform_filter(f_clean_noise_temp,size=un)

            f_clean_noise = np.zeros((f_clean.shape[0],f_clean.shape[1]), np.uint16)
            m=f_clean.shape[0]
            n=f_clean.shape[1]

            for x in range(0,m):
                for y in range(0,n):
                    if f_clean_noise_temp[x,y] <= 0:
                        f_clean_noise[x,y] = f_clean_noise_temp[x,y]
                    elif f_clean_noise_temp[x,y] > 0:
                        f_clean_noise[x,y] = f_clean[x,y]
                        
            print("Noise removal complete")

            imshow(f_clean, cmap='viridis',vmin=0, vmax=5, title=str("Background removal: "+marker)) + \
            imshow(f_clean_noise, cmap='viridis',vmin=0, vmax=5, title=str("Noise removal: "+marker))
            plt.show()

            while True:
                    try:
                        user_input2 = int(input("Next step:\n'1' for noise removal re-do\n'2' for aggregate removal\nEnter value: "))
                        if user_input2 in (1,2):
                            break
                        else:
                            print("Oops!  That was not a valid input.  Try again...")
                    except ValueError:
                        print("Oops!  That was not a valid input.  Try again...")

            while user_input2 == 1:
                print("Noise removal re-do")

                # Noise removal re-do

                while True:
                    try:
                        min = float(input("Enter minimum threshold value: ")) # 1
                        break
                    except ValueError:
                        print("Oops!  That was not a valid input.  Try again...")

                while True:
                    try:
                        un = float(input("Enter uniform threshold value: ")) # 9
                        break
                    except ValueError:
                        print("Oops!  That was not a valid input.  Try again...")

                f_clean_noise_temp=minimum_filter(f_clean,size=min)
                f_clean_noise_temp=uniform_filter(f_clean_noise_temp,size=un)

                f_clean_noise = np.zeros((f_clean.shape[0],f_clean.shape[1]), np.uint16)
                m=f_clean.shape[0]
                n=f_clean.shape[1]

                for x in range(0,m):
                    for y in range(0,n):
                        if f_clean_noise_temp[x,y] <= 0:
                            f_clean_noise[x,y] = f_clean_noise_temp[x,y]
                        elif f_clean_noise_temp[x,y] > 0:
                            f_clean_noise[x,y] = f_clean[x,y]
                            
                print("Noise removal complete")

                imshow(f_clean, cmap='viridis',vmin=0, vmax=5, title=str("Background removal: "+marker)) + \
                imshow(f_clean_noise, cmap='viridis',vmin=0, vmax=5, title=str("Noise removal: "+marker))
                plt.show()

                while True:
                    try:
                        user_input2 = int(input("Next step:\n'1' for noise removal re-do\n'2' for aggregate removal\nEnter value: "))
                        if user_input2 in (1,2):
                            break
                        else:
                            print("Oops!  That was not a valid input.  Try again...")
                    except ValueError:
                        print("Oops!  That was not a valid input.  Try again...")

            print("Moving on to aggregate removal")

            ##################################
            ####### AGGREGATE REMOVAL ########
            ##################################

            while True:
                    try:
                        s2 = float(input("Enter gaussian radius value: ")) # 0.1
                        break
                    except ValueError:
                        print("Oops!  That was not a valid input.  Try again...")

            while True:
                try:
                    aggr_threshold = int(input("Enter aggregate threshold value: ")) # 10
                    break
                except ValueError:
                    print("Oops!  That was not a valid input.  Try again...")

            f_blurred = gaussian_filter(f_clean_noise, sigma=s2)
            f_mask = np.zeros((f_clean_noise.shape[0],f_clean_noise.shape[1]),np.uint16)
            m=f_clean_noise.shape[0]
            n=f_clean_noise.shape[1]

            for x in range(0,m):
                for y in range(0,n):
                    if f_blurred[x,y] <= 0:
                        f_mask[x,y] = 0
                    elif f_blurred[x,y] > 0:
                        f_mask[x,y] = 1

            labels = measure.label(f_mask)
            props = measure.regionprops_table(labels, properties=['label','area','centroid','bbox','coords'])
            props_table = pd.DataFrame(props)

            to_zero_out = pd.DataFrame(columns=['label','area','row1','row2','col1','col2'])
            for i in props_table.index:
                if props_table.loc[i,'area'] <= aggr_threshold:
                    to_zero_out.loc[i,'label'] = props_table.loc[i,'label']
                    to_zero_out.loc[i,'area'] = props_table.loc[i,'area']
                    to_zero_out.loc[i,'row1'] = props_table.loc[i,'bbox-0']
                    to_zero_out.loc[i,'row2'] = props_table.loc[i,'bbox-2']
                    to_zero_out.loc[i,'col1'] = props_table.loc[i,'bbox-1']
                    to_zero_out.loc[i,'col2'] = props_table.loc[i,'bbox-3']
                    
            f_clean_aggr = f_clean_noise.copy()

            for i in to_zero_out.index:
                r1 = to_zero_out.loc[i,'row1']
                r2 = to_zero_out.loc[i,'row2']
                c1 = to_zero_out.loc[i,'col1']
                c2 = to_zero_out.loc[i,'col2']
                f_clean_aggr[r1:r2+1,c1:c2+1] = 0
                
            print("Aggregate removal complete")

            imshow(f_clean_noise, cmap='viridis',vmin=0, vmax=5, title=str("Noise removal: "+marker)) + \
            imshow(f_clean_aggr, cmap='viridis',vmin=0, vmax=3, title=str("Aggregate removal: "+marker))
            plt.show()

            while True:
                    try:
                        user_input3 = int(input("Next step:\n'1' for aggregate removal re-do\n'2' pre-processing complete\nEnter value: "))
                        if user_input3 in (1,2):
                            break
                        else:
                            print("Oops!  That was not a valid input.  Try again...")
                    except ValueError:
                        print("Oops!  That was not a valid input.  Try again...")

            while user_input3 == 1:
                print("Aggregate removal re-do")

                # Aggregate removal re-do

                while True:
                    try:
                        s2 = float(input("Enter gaussian radius value: ")) # 0.1
                        break
                    except ValueError:
                        print("Oops!  That was not a valid input.  Try again...")

                while True:
                    try:
                        aggr_threshold = int(input("Enter aggregate threshold value: ")) # 10
                        break
                    except ValueError:
                        print("Oops!  That was not a valid input.  Try again...")

                f_blurred = gaussian_filter(f_clean_noise, sigma=s2)
                f_mask = np.zeros((f_clean_noise.shape[0],f_clean_noise.shape[1]),np.uint16)
                m=f_clean_noise.shape[0]
                n=f_clean_noise.shape[1]

                for x in range(0,m):
                    for y in range(0,n):
                        if f_blurred[x,y] <= 0:
                            f_mask[x,y] = 0
                        elif f_blurred[x,y] > 0:
                            f_mask[x,y] = 1

                labels = measure.label(f_mask)
                props = measure.regionprops_table(labels, properties=['label','area','centroid','bbox','coords'])
                props_table = pd.DataFrame(props)

                to_zero_out = pd.DataFrame(columns=['label','area','row1','row2','col1','col2'])
                for i in props_table.index:
                    if props_table.loc[i,'area'] <= aggr_threshold:
                        to_zero_out.loc[i,'label'] = props_table.loc[i,'label']
                        to_zero_out.loc[i,'area'] = props_table.loc[i,'area']
                        to_zero_out.loc[i,'row1'] = props_table.loc[i,'bbox-0']
                        to_zero_out.loc[i,'row2'] = props_table.loc[i,'bbox-2']
                        to_zero_out.loc[i,'col1'] = props_table.loc[i,'bbox-1']
                        to_zero_out.loc[i,'col2'] = props_table.loc[i,'bbox-3']
                        
                f_clean_aggr = f_clean_noise.copy()

                for i in to_zero_out.index:
                    r1 = to_zero_out.loc[i,'row1']
                    r2 = to_zero_out.loc[i,'row2']
                    c1 = to_zero_out.loc[i,'col1']
                    c2 = to_zero_out.loc[i,'col2']
                    f_clean_aggr[r1:r2+1,c1:c2+1] = 0
                    
                print("Aggregate removal complete")

                imshow(f_clean_noise, cmap='viridis',vmin=0, vmax=5, title=str("Noise removal: "+marker)) + \
                imshow(f_clean_aggr, cmap='viridis',vmin=0, vmax=3, title=str("Aggregate removal: "+marker))
                plt.show()

                while True:
                    try:
                        user_input3 = int(input("Next step:\n'1' for aggregate removal re-do\n'2' pre-processing complete\nEnter value: "))
                        if user_input3 in (1,2):
                            break
                        else:
                            print("Oops!  That was not a valid input.  Try again...")
                    except ValueError:
                        print("Oops!  That was not a valid input.  Try again...")

            path = str("Preprocessing_Outputs/"+fs+"/"+marker+".tiff")
            imwrite(path, f_clean_aggr)

            print(str("Output saved for ROI "+fs+" for "+marker))

            ############################
            # ASK ABOUT REMAINING ROIS #
            ############################
            
            if fs != files[-1]:
                while True:
                    try:
                        user_input4 = int(input("Want to use the same parameters for remaining ROIs?\n'1' Yes\n'2' No\nEnter value: "))
                        if user_input4 in (1,2):
                            break
                        else:
                            print("Oops!  That was not a valid input.  Try again...")
                    except ValueError:
                        print("Oops!  That was not a valid input.  Try again...")

                if user_input4 == 1:

                    for fl in files[1:]:

                        print("ROI being pre-processed: "+fl)

                        maui = {}
                        for channel in channels:
                            maui.update({channel: imread(str(tiff_path+fl+'/'+channel+'.tiff'))})
                        
                        h = maui.get(background)
                        f = maui.get(marker)

                        # Background removal
                        h_capped = np.zeros((h.shape[0],h.shape[1]),np.uint16)
                        m=h.shape[0]
                        n=h.shape[1]

                        for x in range(0,m):
                            for y in range(0,n):
                                if h[x,y] <= c:
                                    h_capped[x,y] = h[x,y]
                                elif h[x,y] > c:
                                    h_capped[x,y] = c

                        h_blurred = gaussian_filter(h_capped, sigma=s1)
                        h_rescaled = h_blurred/h_blurred.max()

                        h_mask = np.zeros((h.shape[0],h.shape[1]),np.uint16)
                        m=h.shape[0]
                        n=h.shape[1]

                        for x in range(0,m):
                            for y in range(0,n):
                                if h_rescaled[x,y] >= t:
                                    h_mask[x,y] = 1
                                elif h_rescaled[x,y] < t:
                                    h_mask[x,y] = 0
                                    
                        f_removed = np.zeros((f.shape[0],f.shape[1]))
                        m=f.shape[0]
                        n=f.shape[1]

                        for x in range(0,m):
                            for y in range(0,n):
                                if h_mask[x,y] == 0:
                                    f_removed[x,y] = f[x,y]
                                elif h_mask[x,y] == 1:
                                    f_removed[x,y] = f[x,y] - v
                                
                        f_clean = np.zeros((f.shape[0],f.shape[1]), np.uint16)
                        m=f.shape[0]
                        n=f.shape[1]

                        for x in range(0,m):
                            for y in range(0,n):
                                if f_removed[x,y] >= 0:
                                    f_clean[x,y] = f_removed[x,y]
                                elif f_removed[x,y] < 0:
                                    f_clean[x,y] = 0

                        # Background removal with second marker if available
                        while True:
                            try:
                                if 'background_second' in globals():
                                    h = maui.get(background_second)
                                    f = f_clean

                                    h_capped = np.zeros((h.shape[0],h.shape[1]),np.uint16)
                                    m=h.shape[0]
                                    n=h.shape[1]

                                    for x in range(0,m):
                                        for y in range(0,n):
                                            if h[x,y] <= c_bg2:
                                                h_capped[x,y] = h[x,y]
                                            elif h[x,y] > c_bg2:
                                                h_capped[x,y] = c_bg2

                                    h_blurred = gaussian_filter(h_capped, sigma=s1_bg2)
                                    h_rescaled = h_blurred/h_blurred.max()

                                    h_mask = np.zeros((h.shape[0],h.shape[1]),np.uint16)
                                    m=h.shape[0]
                                    n=h.shape[1]

                                    for x in range(0,m):
                                        for y in range(0,n):
                                            if h_rescaled[x,y] >= t_bg2:
                                                h_mask[x,y] = 1
                                            elif h_rescaled[x,y] < t_bg2:
                                                h_mask[x,y] = 0
                                                
                                    f_removed = np.zeros((f.shape[0],f.shape[1]))
                                    m=f.shape[0]
                                    n=f.shape[1]

                                    for x in range(0,m):
                                        for y in range(0,n):
                                            if h_mask[x,y] == 0:
                                                f_removed[x,y] = f[x,y]
                                            elif h_mask[x,y] == 1:
                                                f_removed[x,y] = f[x,y] - v_bg2
                                            
                                    f_clean = np.zeros((f.shape[0],f.shape[1]), np.uint16)
                                    m=f.shape[0]
                                    n=f.shape[1]

                                    for x in range(0,m):
                                        for y in range(0,n):
                                            if f_removed[x,y] >= 0:
                                                f_clean[x,y] = f_removed[x,y]
                                            elif f_removed[x,y] < 0:
                                                f_clean[x,y] = 0
                                break
                            except NameError:
                                break
                                    
                        print("Background removal complete")

                        # Noise removal

                        f_clean_noise_temp=minimum_filter(f_clean,size=min)
                        f_clean_noise_temp=uniform_filter(f_clean_noise_temp,size=un)

                        f_clean_noise = np.zeros((f_clean.shape[0],f_clean.shape[1]), np.uint16)
                        m=f_clean.shape[0]
                        n=f_clean.shape[1]

                        for x in range(0,m):
                            for y in range(0,n):
                                if f_clean_noise_temp[x,y] <= 0:
                                    f_clean_noise[x,y] = f_clean_noise_temp[x,y]
                                elif f_clean_noise_temp[x,y] > 0:
                                    f_clean_noise[x,y] = f_clean[x,y]
                                    
                        print("Noise removal complete")

                        # Aggregate removal

                        f_blurred = gaussian_filter(f_clean_noise, sigma=s2)
                        f_mask = np.zeros((f_clean_noise.shape[0],f_clean_noise.shape[1]),np.uint16)
                        m=f_clean_noise.shape[0]
                        n=f_clean_noise.shape[1]

                        for x in range(0,m):
                            for y in range(0,n):
                                if f_blurred[x,y] <= 0:
                                    f_mask[x,y] = 0
                                elif f_blurred[x,y] > 0:
                                    f_mask[x,y] = 1

                        labels = measure.label(f_mask)
                        props = measure.regionprops_table(labels, properties=['label','area','centroid','bbox','coords'])
                        props_table = pd.DataFrame(props)

                        to_zero_out = pd.DataFrame(columns=['label','area','row1','row2','col1','col2'])
                        for i in props_table.index:
                            if props_table.loc[i,'area'] <= aggr_threshold:
                                to_zero_out.loc[i,'label'] = props_table.loc[i,'label']
                                to_zero_out.loc[i,'area'] = props_table.loc[i,'area']
                                to_zero_out.loc[i,'row1'] = props_table.loc[i,'bbox-0']
                                to_zero_out.loc[i,'row2'] = props_table.loc[i,'bbox-2']
                                to_zero_out.loc[i,'col1'] = props_table.loc[i,'bbox-1']
                                to_zero_out.loc[i,'col2'] = props_table.loc[i,'bbox-3']
                                
                        f_clean_aggr = f_clean_noise.copy()

                        for i in to_zero_out.index:
                            r1 = to_zero_out.loc[i,'row1']
                            r2 = to_zero_out.loc[i,'row2']
                            c1 = to_zero_out.loc[i,'col1']
                            c2 = to_zero_out.loc[i,'col2']
                            f_clean_aggr[r1:r2+1,c1:c2+1] = 0
                        
                        path = str("Preprocessing_Outputs/"+fl+"/"+marker+".tiff")
                        imwrite(path, f_clean_aggr)

                        print("Aggregate removal complete")

                        print(str("Output saved for ROI "+fl+" for "+marker))
                    break


