# NMTT: Nano-micromotor tracking tool

 Tool to track nano- and micromotors' motion from bright-field or fluorescent microscopy imaging.

(More information to come)


### Installing dependencies

It is recommended to use [Anaconda](https://www.anaconda.com/products/individual) and a specific enviorenment to run this code, to avoid clashes between packages versions. It's recommended to use Python 3.6 or higher.

After installing Anaconda, open your Anaconda prompt and write:

```
conda create --name NMTT python=3.6
```


Once the environment has been created, activate it by:

```
conda activate NMTT
```

Then install the dependencies by writing (Note: it is assumed the requirements.txt file is in the home directory, otherwise you should write "[pathtofile]/requirements.txt"

```
pip install -r requirements.txt
```

ffmpeg is needed to deal with video reading and writing. It should come installed with OpenCV using the previous command, but if any errors are raised when reading or writing the videos, you should attempt to installing yourself in http://ffmpeg.org/.

It's recommended to run this program with an Integrated Development Environment (IED) like Spyder, since a couple of paramters from the code might need to be manually adjusted (see Global Variables section). To install it, once you have activated your conda environment, write in the prompt:

```
conda install spyder
```

Once it's been installed, you can open it by simply writing in the prompt:

```
spyder
```

Once opened, you can drag the *.py* file into the window or open it in File\Open. Clicking F5 or the button "Run file" will launch the script.

### Instructions to run

First, you'll be asked to select a video that you want to analyse. This can be a video from fluorescent or bright-field imaging. **Note**: The pop-up window to select the video file uses the package [easygui](https://pypi.org/project/easygui/). This pop-up window doesn't show in the taskbar and sometimes appears hidden behind your windows. If you run the script and nothing happens, minimse your windows one by one and you might find the browse window at the back.

Then, when the video has been opened, you'll be asked to adapt the contrast settings of the image. This is especially useful for fluorescent images with low exposition times. If you're using bright-field imaging or contrast adjustments are not necessary because the image is displayed correctly, simply press **ESC**. If you need to adjust the contrast, move the slider and press ESC when you're happy with your selection. **Note**: the pixel intensity of the image is multiplied by 1/10 of this value (the trackbar doesn't allow decimals). Therefore, the default of 10 is actually 1, which means no change in the image. 

Default contrast             |  Desirable contrast
:-------------------------:|:-------------------------:
![image](https://user-images.githubusercontent.com/13152269/148553491-39c6acf4-6c25-4552-9ba5-6a2c1f4e8177.png) | ![image](https://user-images.githubusercontent.com/13152269/148553561-12fc8c22-7e49-48e2-9682-7ba4afcd3ddc.png)



Then, you'll be asked to select the particles you want to track by creating a region of interest (ROI) around them:

1. Select the ROI by pressing and dragging the left button of your mouse. You can retry this as many times as you want to select the particle. It is recommended that the ROI is not too big (especially if there are many particles) or too small, barely covering the particle size. Most likely, trial and error will be required as each tracked object will behave differently. Once you're happy with your ROI, press **SPACEBAR** to confirm. 

2. If you want to select the ROI for another particle in the same frame, press **SPACEBAR** again. You'll be asked to select another ROI in the same way as before. 

3. If you're done with selecting your particles, press **ESC** to exit.

<p float="left">
  <img src="https://user-images.githubusercontent.com/13152269/148554913-4974ddf5-652c-4df6-825f-4b438b7ceb0f.png" width="400" />
</p>

Once you press ESC, the tracking will start:

<p float="left">
  <img src="https://user-images.githubusercontent.com/13152269/148555524-89644b84-f4b4-4bc7-be8b-efa9ba62d62c.png" width="400" />
</p>

You don't need to do anything, the tracking will stop by itself and write all the results in file. 


### Results

This script writes several results in file. Assuming your file was named *myfile*, the script will create a folder in the same destination called *myfile*. Inside, for each particle, it creates:

File name             |  Contents
:-------------------------:|:-------------------------:
*myfile*\_contrastCorrection.txt | An error log with information about if and when the objects were lost
*myfile*\_errorLog.txt | The value applied for contrast correction
*myfile*\_p*X*\_boundingBox.txt | The position of the bounding box in time for particle *X*
*myfile*\_p*X*\_motion.txt | The total distance in micrometers vs time for particle *X*
*myfile*\_p*X*\_trackingCV2pixels.txt | The position of the particle in OpenCV pixels in time for particle *X*
*myfile*\_p*X*\_tracking\_um\_norm.txt | The position of the particle in micrometers in time normalised to 0 for particle *X*
*myfile*\_TRACKING\_*trackername*.avi | The video with the trackings using tracker *trackername*
 
Each of these files (except the first two and the video) will appear for as many particles as were tracked.

Finally, a summary file *myfile*\_trackingResults.csv is created in the same folder as the original video, with the time, X position and Y position (in micrometers) for each particle.

### Global variables

There are several variables that need to be manually adjusted by the user. 

Variable name             |  Explanation    | Default value
:-------------------------:|:-------------------------: | :--------:
f | Scaling factor of the video. If the resolution of the video is too large, parts of it might be hidden and the user might not be able to select a bounding box. To account for this, the resolution of the video might be scaled down by *f*, ranging from 0 to 1, where 1 is the same size as before. This only affects the visualisation of the video, the tracking will still be performed with the full resolution video. | 1
DISPLAY_FPS | Flag to display the FPS of the video on the top left corner | True
DISPLAY_TIME | Flag to display the time of the video on the top left corner | True
DISPLAY_TRACKER | Flag to display the name of the tracker of the video on the top left corner | False
DISPLAY_BOX | Flag to display the bounding box of the tracked object during the video | True
DISPLAY_TRACKING | Flag to display the tracking of the object during the video with a heatmap trail. The first positions will start with a red color, which will turn to blue in time, showing the passing of time in the tracking | True
DISPLAY_TRACKING | Flag to display the tracking of the object during the video with a heatmap trail. The first positions will start with a red color, which will turn to blue in time, showing the passing of time in the tracking | True
