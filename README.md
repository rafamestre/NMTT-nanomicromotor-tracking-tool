# NMTT: Nano-micromotor tracking tool

 Tool to track nano- and micromotors' motion from bright-field or fluorescent microscopy imaging.

(More information to come)


### Installing dependencies

pip install -r requirements.txt

### Instructions to run

First, you'll be asked to adapt the contrast settings of the image. This is especially useful for fluorescent images with low exposition times. If you're using bright-field imaging or contrast adjustments are not necessary because the image is displayed correctly, simply press ESC. If you need to adjust the contrast, move the slider and press ESC when you're happy with your selection.

Then, you'll be asked to select the particles you want to track by creating a region of interest (ROI) around them:

1. Select the ROI by pressing and dragging the left button of your mouse. You can retry this as many times as you want to select the particle. It is recommended that the ROI is not too big (especially if there are many particles) or too small, barely covering the particle size. Most likely, trial and error will be required as each tracked object will behave differently. Once you're happy with your ROI, press SPACEBAR to confirm. 

2. If you want to select the ROI for another particle in the same frame, press SPACEBAR again. You'll be asked to select another ROI in the same way as before. 

3. If you're done with selecting your particles, press ESC to exit.
