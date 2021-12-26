# -*- coding: utf-8 -*-
"""
NMAT: Nano-micromotor Analysis Tool

v0.1

26/12/2021
    
TO DO:
    
    -) Make the part of a lost particle more robust.
    -) Eliminate MSD calculation (or not?) when NMAT is updated.

@author: Rafael Mestre; r.mestre@soton.ac.uk;

This code was written to be compatible Python 3.6+, as well
as both Windows, Linux and Mac OS.

"""


import os
import numpy as np
import cv2
import easygui
import seaborn as sns
import csv
from tqdm import tqdm
from itertools import compress
from pathlib import Path




'''
#####################
Parameter definition
#####################
These parameters let us select certain options of the code, such
as the scaling factor of the image or what is shown in the video
'''

f = 1 #Scaling factor of the video
#Change only if the image is too big for the display.
#It accepts a value from 0 to 1, the size of the video will be multiplied
#by f. This doesn't affect the quality of the trakcing, it's only for displaying
#purposes.

#Display options:
    #select the ones you want depending on what you want shown in the video
displayFPS = True
displayTime = True
displayTracker = False
displayBox = True
displayTracking = True
displayScaleBar = True
displayScaleBarText = True
displayParticleNumber = True
displayVideo = True
generalOffset = 0 #This is to apply a general offset to the information on the top left, to be moved down


#The jumpt threshold specified how much is the particle moved from one frame to 
#the other, to consider that the tracker has lost it and it has found a different
#particle. During tracking, the average dimension of the bounding box (the mean
#value of its width and height) is multiplied by the jump threshold.
#If it's set to 0.5, the center of the bounding box must have moved more than
#half its size, to consider that we've lost it.
#Recommended value is 0.5, but can be larger if the particles generally move
#very fast, or smaller if they are moving slowly.
jumpThreshold = 0.5 


# Set up tracker.
tracker_types = ['BOOSTING', 'MIL','KCF', 'TLD', 'MEDIANFLOW', 'GOTURN', 'MOSSE', 'CSRT']
tracker_type = tracker_types[7] #Best performing one is CSRT

####IMPORTANT:
####The "scale" settings below are from a specifici microscope
####with a specific magnification. The scale in pixel/micron should
####be changed for each microscope. The scaleNumber variable is the scale bar
####maginute that will appear in the video

scaleNumber = 10 #scale number to be shown in um
scale = 9.6 #in pixel/micron


def on_trackbar(dummy):
    #Doesn't do anything, it's necessary for the trackbar
    pass



def autocorrFFT(x):
    '''Calculates the autocorrelation FFT of a list of numbers.
    It's needed by the method MSD_fft'''
    
    N=len(x)
    F = np.fft.fft(x, n=2*N)  #2*N because of zero-padding
    PSD = F * F.conjugate()
    res = np.fft.ifft(PSD)
    res = (res[:N]).real   #now we have the autocorrelation in convention B
    n=np.arange(N, 0, -1) #divide res(m) by (N-m)
    return res/n #Normalized auto-correlation


def MSD_fft(xvector,yvector,dt=1):
    r'''Performs the MSD very efficiently using FFT. The result is time averaged.    
    The discrete MSD is separated in S1 and 2*S2.
    Based on https://www.neutron-sciences.org/articles/sfn/abs/2011/01/sfn201112010/sfn201112010.html
    Code adapted from https://stackoverflow.com/questions/34222272/computing-mean-square-displacement-using-python-and-fft
    Scales with O(NlogN).
    '''
    
    pos = np.array([xvector, yvector]).T
    N=len(pos)
    
    time_list = np.arange(0,N)*dt
    
    
    D=np.square(pos).sum(axis=1) #x(i)**2 + y(i)**2
    D=np.append(D,0) #To make S1[0] equal to D[0]
    Q=2*D.sum()
    S1=np.zeros(N)
    
    for m in range(N):
        Q=Q-D[m-1]-D[N-m]
        S1[m]=Q/(N-m)
        
#    print 's1', time.time() - s1t

    S2=sum([autocorrFFT(pos[:, i]) for i in range(pos.shape[1])])
    
#    print 's2', time.time()-s2t
    
    msd = S1 - 2*S2
    return time_list, msd[0:]





def generate_tracker(type_of_tracker):
    """
    Create object tracker.
       
    :param type_of_tracker string: OpenCV tracking algorithm 
    """
    if type_of_tracker == tracker_types[0]:
        tracker = cv2.TrackerBoosting_create()
    elif type_of_tracker == tracker_types[1]:
        tracker = cv2.TrackerMIL_create()
    elif type_of_tracker == tracker_types[2]:
        tracker = cv2.TrackerKCF_create()
    elif type_of_tracker == tracker_types[3]:
        tracker = cv2.TrackerTLD_create()
    elif type_of_tracker == tracker_types[4]:
        tracker = cv2.TrackerMedianFlow_create()
    elif type_of_tracker == tracker_types[5]:
        tracker = cv2.TrackerGOTURN_create()
    elif type_of_tracker == tracker_types[6]:
        tracker = cv2.TrackerMOSSE_create()
    elif type_of_tracker == tracker_types[7]:
        tracker = cv2.TrackerCSRT_create()
    else:
        tracker = None
        print('The name of the tracker is incorrect')
        print('Here are the possible trackers:')
        for track_type in tracker_types:
            print(track_type)
    return tracker



def main():

    global f
    global initialPath
    # global displayFPS,displayTime,displayTracker,displayBox,displayTracking
    # global displayScaleBar,displayScaleBarText,displayParticleNumber,displayVideo
    # global generalOffset
    # global jumpThreshold
    
    
    # Generate a MultiTracker object    
    multi_tracker = cv2.MultiTracker_create()
    
    dn = os.path.dirname(os.path.realpath(__file__))
    
    try:
        fileName = Path(easygui.fileopenbox(default=dn))
    except:
        raise Exception('File not selected.')

        
    initialPath = fileName.parents[0]
    
    # Read video
    video = cv2.VideoCapture(str(fileName))
    
    # Exit if video not opened.
    if not video.isOpened():
        raise Exception('Could not open video.')

    # Get some parameters of the videofile
    length = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = round(video.get(cv2.CAP_PROP_FPS))
    seconds = length/fps
    
    
    #Create the current and save directories, and file names
    currentDir = fileName.parents[0]
    file = fileName.stem
    saveDir = Path(currentDir,file)
    newVideoName = file+'_TRACKING_'+tracker_type+'.avi'
    newVideo = Path(saveDir,newVideoName)
    
    #If the file folder doesn't exist, it creates it
    if not os.path.exists(saveDir):
        os.makedirs(saveDir)
    
    
    
    
    # Read first frame.
    ok, initialFrame = video.read()
    if not ok:
        raise Exception('Cannot read video file.')
    
    
    
    '''
    #####################
    Contrast setting code
    #####################
    This part of the code allows the user to manually modify the contrast
    of the video. This is useful for fluorescent imaging when the fluorescent
    signal is very low.
    '''
    
    
    #Frame is resized if f is different from 1
    frameResized = cv2.resize(initialFrame,(0,0),fx=f,fy=f)    
    
    #Creates window
    title_window = 'Contrast adjustment'
    cv2.namedWindow(title_window,cv2.WINDOW_AUTOSIZE )
    
    #Creates trackbar
    trackbar_name = 'Alpha (x10)'
    cv2.createTrackbar(trackbar_name, title_window , 10, 100, on_trackbar)
    
    # beta = 1
    # on_trackbar(1)
    # beta = cv2.getTrackbarPos(trackbar_name,title_window)
    # sys.exit()
    
    #Infinite loop stopping if the letter q is pressed
    while True:
    
        #The alpha value is by default 10. It is divided by 10 because
        #the tracking bar doesn't allow decimals. Alpha = 1 means image is unchanged.
        alpha = cv2.getTrackbarPos(trackbar_name,title_window)/10    
        
        #The scale is trasnformed with the specified alpha value
        frameBeta = cv2.convertScaleAbs(frameResized, alpha=alpha, beta=0)
    
        cv2.imshow(title_window,frameBeta)
        
        # Wait for keypress
        k = cv2.waitKey(1) & 0xff
         
        # Stop if 'q' is pressed            
        if k == 27:
            break
    
    cv2.destroyAllWindows()
    
    #Error handling
    if alpha < 0:
        raise Exception('Something went wrong with the contrast setting...\n Do not close the window with the "x", but pressing "q".')
    
    #Changes are applied
    frameResized = cv2.convertScaleAbs(frameResized, alpha=alpha, beta=0)
    initialFrame = cv2.convertScaleAbs(initialFrame, alpha=alpha, beta=0)
    
    
    
    '''
    #####################
    Tracking code
    #####################
    This part of the code starts the tracking.
    Firstly, the first frame is shown to the user to select with bounding boxes
    the particles that want to be tracked. 
    One bounding box can be re-done as many times as one wishes, and it will only be
    finalised if SPACEBAR is pressed. To finish selecting particles, ESC must be pressed.
    '''
    
    #Bounding box for tracking initialised
    bounding_box_list = list()
    bbox_aux = list()
    
    while True:
        # Draw a bounding box over all the objects that you want to track_type
        # Press ENTER or SPACE after you've drawn the bounding box
        bbox = cv2.selectROI('Multi-Object Tracker', frameResized) 
         
        # Add a bounding box
        bbox_aux.append(bbox)
        
        # Press 'q' (make sure you click on the video frame so that it is the
        # active window) to start object tracking. You can press another key
        # if you want to draw another bounding box.           
        print("\nPress q to begin tracking objects or press " +
          "another key to draw the next bounding box\n")
         
        # Wait for keypress
        k = cv2.waitKey(0) & 0xff
         
        # Start tracking objects if 'q' is pressed            
        if k == 27:
            break
            
    
    ###bbox has four components (x,y,w,h):
    #The first one is the x-coordinate of the upper left corner
    #The second one is the y-coordinate of the upper left corner
    #The third one is the width
    #The four one is the height
    
    
    cv2.destroyAllWindows()
    
    
    #This part removes the instances of bounding box with 0's
    #This happens sometimes if a double press is made by mistake
    while True:
        try:
            bbox_aux.remove((0,0,0,0))
        except:
            break
        
    #Bounding boxes are added to the list, after being resized with the f scaling factor
    bounding_box_list.append(list([np.asarray([int(z/f) for z in bbox]) for bbox in bbox_aux]))
    
    
    print("\nTracking objects. Please wait...")
    
    #Trackers generated
    for bbox in bounding_box_list[0]:
     
        # Add tracker to the multi-object tracker
        multi_tracker.add(generate_tracker(tracker_type), initialFrame, tuple(bbox))
    
    #ID's are generated for each particle
    ids = [i+1 for i in range(len(bounding_box_list[0]))]
    
    
    count = 0 #First frame is already read
    
    #Initialisation of time and center lists
    timeList = list([0])
    centerList = list()
    centerList.append([(int(bbox[0] + bbox[2]/2.),int(bbox[1] + bbox[3]/2.)) for bbox in bounding_box_list[0]])
    
    
    
    #Necessary to write videos        
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    out = cv2.VideoWriter(str(newVideo), fourcc, fps, (int(width),int(height)))
    
    
    #Get colormap for trajectory
    cmap = sns.color_palette("RdYlBu",int(seconds*fps))
    
    
    pbar = tqdm(total=length-1) #For progress bar
    
    #Other useful lists
    #KeepDict tells you which IDs are kept in the next frame, i.e. which particles
    #where not lost.
    
    ID_array = [ids.copy()]
    keepDict = dict([(ID, True) for ID in ids])
    errorLog = list()
    
    #Tracking starts, press ESC if you want to finish early
    while True:
        
        # Read a new frame
        ok, frame = video.read()
    
        #Frame contrast is adjusted according to alpha before
        frame = cv2.convertScaleAbs(frame, alpha=alpha, beta=0)
    
        count += 1
        # pbar.updtate()
        
        #If no values are in the Keep list, that means all trackings were lost
        if not True in keepDict.values(): 
            print('All trackings were lost')
            break
        
        if not ok:
            #Most likely, the video has ended
            break
        
        #Resize only if f is less than 1
        if f != 1:
            frameResized = cv2.resize(frame,(0,0),fx=f,fy=f)        
    
        # Update tracker
        ok, bboxes = multi_tracker.update(frame)
        bounding_box_list.append(bboxes)
            
        if not ok:
            print('Tracker error')
            
        #Time elapsed
        elapsed = count/fps
        timeList.append(elapsed)
        
        #This piece of code tells you if one of the particles was lost in the
        #previous frame, according to the keepDict.
        nb_Trues = len(ID_array[-1])
        ID_array.append(list(compress(ids, keepDict.values())))
        
        if nb_Trues != sum(keepDict.values()):
            missing_ids = list(set(ID_array[-1]).symmetric_difference(set(ID_array[-2])))
            print('Tracker lost')
            # print(keepDict)
            [errorLog.append('Object {} lost at time {} s.'.format(p, timeList[-1])) for p in missing_ids]
    
    
        #Calculate the central position of the bounding boxes/particle
        centers = list()

        for index in ids:
            if not index in ID_array[-1]:
                #If the particle ID is not in the ID_array list, then that means it
                #got lost. Centres are updated to (-1,-1)
                centers.append((-1,-1))
                continue
            else:
                #Otherwise, the center is calculated according to the boundinb box dimensions
                bbox = bboxes[index-1]
                centers.append((int(bbox[0] + bbox[2]/2.),int(bbox[1] + bbox[3]/2.)))
                if len(centerList) > 10:
                    #If the following happens, we consider it hasn't moved,
                    #meaning it has lost the object
                    #This is just a very simple way of considering the center of the particle
                    #has barely changed in 10 frames, which means the particle has been lost
                    #and the tracker is not following anything.
                    #TODO: do this better
                    if centerList[-1][index-1] == centerList[-10][index-1]:
                        if centerList[-3][index-1] == centerList[-5][index-1]:
                            #If the particle has disappeared, we set its index in the
                            #keepDict as False.
                            keepDict[index] = False
                            continue
                #if the center of the tracked object has moved too much
                #(a distance specified by the jump threshold)
                #we consider it has moved to another particle and it stops
                distance_x = (centerList[-1][index-1][0]-centers[-1][0])**2
                distance_y = (centerList[-1][index-1][1]-centers[-1][1])**2
                distance = np.sqrt(distance_x + distance_y)
    
                if distance > np.mean([bbox[2],bbox[3]])*jumpThreshold:
                    #if the distance is more than the average dimension
                    #times the jump threshold, the trakcing has moved to another particle
                    keepDict[index] = False
                    print('Tracking went away')
                    errorLog.append('Object {} went more than {} px away at time {} s.'.format(index,
                                                                                               np.mean([bbox[2],bbox[3]])*jumpThreshold,
                                                                                               timeList[-1]))
                    centers[-1] = (-1,-1)
                    continue
    
        
            # Draw bounding box
            # only if the particle was not lost
            if displayBox:
                if f != 1:
                    bboxScaled = tuple([b*f for b in bbox])
                    p1Scaled = (int(bboxScaled[0]), int(bboxScaled[1]))
                    p2Scaled = (int(bboxScaled[0] + bboxScaled[2]), int(bboxScaled[1] + bboxScaled[3]))
                    cv2.rectangle(frameResized, p1Scaled, p2Scaled, (255,102,102),thickness=2)
                p1 = (int(bbox[0]), int(bbox[1]))
                p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
                cv2.rectangle(frame, p1, p2, (255,102,102),thickness=2)
        
        #All the calculated centeres are appended to the list
        centerList.append(centers)        
        
        #Loop through the CURRENT PARTICLES only
        if displayParticleNumber:
            for k in range(len(ID_array[-1])):
                label = ID_array[-1][k]
                bbox = bboxes[label-1]
                #This part adds the particle label next to the bounding box
                if f != 1:
                    bboxScaled = tuple([b*f for b in bbox])
                    cv2.putText(frameResized, str(label), 
                                (int(bboxScaled[0]+bboxScaled[2]),int(bboxScaled[1])), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255,255,255),2)
                cv2.putText(frame, str(label), 
                            (int(bbox[0]+bbox[2]),int(bbox[1])), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255,255,255),2)
        
        #If we want to display the tracking with colors
        if displayTracking:
            centerList_T = list(zip(*centerList))
            for i, idx in enumerate(ID_array[-1]):
                count2 = 0
                for point1, point2 in zip(centerList_T[idx-1], centerList_T[idx-1][1:]): 
                    if point1 != (-1,-1) and point2 != (-1,-1):
                        color = (int(cmap[count2][2]*255),int(cmap[count2][1]*255),int(cmap[count2][0]*255))
                        if f != 1:
                            p1Scaled = tuple([int(p1*f) for p1 in point1])
                            p2Scaled = tuple([int(p2*f) for p2 in point2])
                            cv2.line(frameResized, p1Scaled, p2Scaled, color, 3)
                        cv2.line(frame, point1, point2, color, 3) 
                        count2 += 1
            
    
        # Display tracker type on frame
        if displayTracker:
            if f != 1:
                cv2.putText(frameResized, tracker_type + " Tracker", (int(f*width*0.15),int(f*height*0.05+generalOffset*f)), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (50,170,50),2)
            cv2.putText(frame, tracker_type + " Tracker", (int(width*0.15),int(height*0.05)+generalOffset), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255,255,255),2)
        
        # Display FPS on frame
        if displayFPS:
            if f != 1:
                cv2.putText(frameResized, "FPS: " + str(fps), (int(f*width*0.15),int(f*height*0.05+generalOffset*f)+30), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (50,170,50), 2)
            cv2.putText(frame, "FPS: " + str(fps), (int(width*0.15),int(height*0.05)+30+generalOffset), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255,255,255), 2)
    
        # Display elapsed time
        if displayTime:
            if f != 1:
                cv2.putText(frameResized, "Time: " + "%.2f s" % elapsed, (int(f*width*0.15),int(f*height*0.05+generalOffset*f)+60), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (50,170,50), 2)     
            cv2.putText(frame, "Time: " + "%.2f s" % elapsed, (int(width*0.15),int(height*0.05)+60+generalOffset), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255,255,255), 2)
        
        # Display scale bar
        if displayScaleBar:
            p1 = (int(width*0.7),int(height*0.07)+generalOffset)
            p2 = (int(width*0.7+scaleNumber*scale),int(height*0.075)+generalOffset)
            cv2.rectangle(frame, p1,p2, (255,255,255), -1)
            if f != 1:
                p1Scaled = (int(p1[0]*f),int(p1[1]*f))
                p2Scaled = (int(p2[0]*f),int(p2[1]*f))
                cv2.rectangle(frameResized, p1Scaled,p2Scaled, (255,255,255), -1)
            if displayScaleBarText:
                if f != 1:
                    cv2.putText(frameResized,str(scaleNumber) + ' um',(int(f*width*0.7),int(f*height*0.06+generalOffset*f)),cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255,255,255), 2)
                cv2.putText(frame,str(scaleNumber) + ' um',(int(width*0.72),int(height*0.06)+generalOffset),cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255,255,255), 2)
    
        
        # Display result
        if displayVideo:
            if f != 1:
                cv2.imshow("Tracking", frameResized)
            else:
                cv2.imshow("Tracking", frame)        
        
        #Writes the frame in the out file
        out.write(frame)
     
        # Exit if ESC pressed
        k = cv2.waitKey(1) & 0xff
        if k == 27 : break
    
    pbar.close() #Close progress bar
    cv2.destroyAllWindows()
    out.release()
    
    video.release()
    
    #Saves the error log
    with open(Path(saveDir,'errorLog.txt'),'w') as f:
        for i in errorLog:
            f.write(i+'\n')
          
    #Saves the contract correction value
    with open(Path(saveDir,file+'_contrastCorrection.txt'),'w') as f:
        f.write('alpha\t{}'.format(alpha))
    
    
    '''
    #####################
    Post-processing code
    #####################
    This part makes post-processing of the particles. 
    Saves the info and calculates MSD.
    '''
    
    #For each tracked particle
    for p in ids:  
        
        #Initial position of the particle in micrometers
        #It uses the scale variable, that's why it's important that it's updated
        #with the correct conversion of pixel/um
        initialCenter = (int(bounding_box_list[0][p-1][0] + bounding_box_list[0][p-1][2]/2.),
                         int(bounding_box_list[0][p-1][1] + bounding_box_list[0][p-1][3]/2.))
        initialCenterx = initialCenter[0]/scale
        initialCentery = initialCenter[1]/scale
        
        #All the centers in um (x, y dimensions and 2D)
        centerx = [centerList[i][p-1][0]/scale for i in range(len(centerList)) if centerList[i][p-1] != (-1,-1)]
        centery = [centerList[i][p-1][1]/scale for i in range(len(centerList)) if centerList[i][p-1] != (-1,-1)]
        center = [np.sqrt((centerx[i]-initialCenterx)**2 + (centery[i]-initialCentery)**2) for i in range(len(centerx))]
                
        
        #Write in file the bounding boxes
        #Only before it got lost
        #For that we use variable "center" to tell us how much we should write
        with open(Path(saveDir, file+'_p'+str(p)+'_boundingBox.txt'), 'w')  as ff:
            ff.write('FPS: \t%.2f\n' % (fps))
            for i in range(len(center)):
                ff.write("%.f\t%.f\t%.f\t%.f\n" % (bounding_box_list[i][p-1][0],bounding_box_list[i][p-1][1],
                                                   bounding_box_list[i][p-1][2],bounding_box_list[i][p-1][3]))
    
        
        #Writes in file the distance the particles traveled vs time
        with open(Path(saveDir, file+'_p'+str(p)+'_motion.txt'), 'w') as ff:
            ff.write('Time (s)\tDistance (um)\n')
            for i in range(len(center)):
                ff.write("%.3f\t%.6f\n" % (timeList[i],center[i]))
            
        
        
        '''
        NOTE:
            
        In CV2, the coordinates are:
            
        0/0---X--->
         |
         |
         Y
         |
         |
         v
        
        Instead of being (like in plots):
        
         ^
         |
         |
         Y
         |
         |
        0/0---X--->
        
        Therefore, to plot the trajectory we need to change the sign of the y coordinate
        '''
        
        #The center is normalised to the initial position, so they all start from 0
        centerx_norm = [centerx[i]-initialCenterx for i in range(len(centerx))]
        centery_norm = [-(centery[i]-initialCentery) for i in range(len(centery))]
        
        # xmax = max(centerx_norm)
        # xmin = min(centerx_norm)
        # ymax = max(centery_norm)
        # ymin = min(centery_norm)
        # lims = (min((xmin,ymin)),max((xmax,ymax)))
        
        
        #Write tracking position in pixels (including the lost particles with -1's)
        with open(Path(saveDir, file+'_p'+str(p)+'_trackingCV2pixels.txt'), 'w')  as ff:
            ff.write('Time (s)\tX (opencv px)\tY (opencv px)\n')
            for i in range(len(centerx_norm)):
                ff.write("%.3f\t%.f\t%.f\n" % (timeList[i],centerList[i][p-1][0],centerList[i][p-1][1]))
    
        #Write tracking position in um (including the lost particles with -1's)
        with open(Path(saveDir, file+'_p'+str(p)+'_trackingPlot_um_norm.txt'), 'w')  as ff:
            ff.write('Time (s)\tX (um)\tY (um)\n')
            for i in range(len(centerx_norm)):
                ff.write("%.3f\t%.6f\t%.6f\n" % (timeList[i],centerx_norm[i],centery_norm[i]))
        
        
        
        #Calculates the MSD
        msd_time, MSD = MSD_fft(xvector=centerx_norm,yvector=centery_norm,dt=1/fps)
        
        # plt.plot(MSD[:int(len(MSD)/10)],timeList[:int(len(MSD)/10)])
        
        #Writes the MSD
        with open(Path(currentDir, file+'_tracking_p'+str(p)+'.csv'), 'w') as ff:
            # ff.write('Particle,'+str(p))
            writer = csv.writer(ff)
            writer.writerow(['Particle',str(p)])
            writer.writerow(['Time (seconds)',*timeList[:len(centerx_norm)]])
            writer.writerow(['X (microm)',*centerx_norm])
            writer.writerow(['Y (microm)',*centery_norm])
            writer.writerow(['MSD (microm**2)',*MSD[1:]])
            writer.writerow(['Time displacement (seconds)',*timeList[1:len(centerx_norm)]])
            # for i in range(len(center)):
            #     ff.write("%.3f\t%.6f\n" % (timeList[i],center[i]))
    
        
        

if __name__ == '__main__':
    main()


