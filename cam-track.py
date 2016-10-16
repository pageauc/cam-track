#!/usr/bin/env python

progname = "cam-track.py"
ver = "version 0.91"

"""
cam-track written by Claude Pageau pageauc@gmail.com
Raspberry (Pi) - python opencv2 camera pan/tilt tracking using picamera module

This is a raspberry pi python opencv2 camera tracking demonstration program.
It takes a sample search rectangle from center of video stream image
and tracks its position based on a percent accuracy at maxLoc.
As the camera pans and tilts.  The cumulative position is displayed.

I will work on converting position based on 360 degree camera movement.
This is still very much a work in progress but I thought it would be
useful for others who might want a simple way to track camera movement.
Note the program can get confused by plain surroundings or some
other movements in the frame although this can be tuned out somewhat
using cam_move_x and cam_move_y global variables

This runs under python2 and openCV2 
Github Repo https://github.com/pageauc/rpi-cam-track

Installation
-------------
Easy Install of cam-track onto a Raspberry Pi Computer with latest Raspbian.
Cut and Paste line below into an SSH or console terminal session

curl -L https://raw.github.com/pageauc/rpi-cam-track/master/cam-track-install.sh | bash

To Run
------

cd ~/cam-track
./cam-track.py

To Change Variable Use Nano to edit cam-track.py

Good Luck  Claude ...

"""
print("%s %s using python2 and OpenCV2" % (progname, ver))
print("Camera movement (pan/tilt) Tracker using openCV2 image searching")
print("Loading Please Wait ....")

import os
mypath=os.path.abspath(__file__)       # Find the full path of this python script
baseDir=mypath[0:mypath.rfind("/")+1]  # get the path location only (excluding script name)
baseFileName=mypath[mypath.rfind("/")+1:mypath.rfind(".")]
progName = os.path.basename(__file__)

# Check for variable file to import and error out if not found.
configFilePath = baseDir + "config.py"
if not os.path.exists(configFilePath):
    print("ERROR - Missing config.py file - Could not find Configuration file %s" % (configFilePath))
    import urllib2
    config_url = "https://raw.github.com/pageauc/rpi-cam-track/master/config.py"
    print("   Attempting to Download config.py file from %s" % ( config_url ))
    try:
        wgetfile = urllib2.urlopen(config_url)
    except:
        print("ERROR - Download of config.py Failed")
        print("   Try Rerunning the cam-track-install.sh Again.")
        print("   or")
        print("   Perform GitHub curl install per Readme.md")
        print("   and Try Again")
        print("Exiting %s" % ( progName ))
        quit()
    f = open('config.py','wb')
    f.write(wgetfile.read())
    f.close()   
# Read Configuration variables from config.py file
from config import *

# import the necessary packages
import time
import cv2

from picamera.array import PiRGBArray
from picamera import PiCamera
from threading import Thread
from operator import itemgetter
import numpy as np

#-----------------------------------------------------------------------------------------------  
class PiVideoStream:     # Create a Video Stream Thread
    def __init__(self, resolution=(CAMERA_WIDTH, CAMERA_HEIGHT), framerate=CAMERA_FRAMERATE, rotation=0, hflip=False, vflip=False):
        # initialize the camera and stream
        self.camera = PiCamera()
        self.camera.resolution = resolution
        self.camera.rotation = rotation
        self.camera.framerate = framerate
        self.camera.hflip = hflip
        self.camera.vflip = vflip
        self.rawCapture = PiRGBArray(self.camera, size=resolution)
        self.stream = self.camera.capture_continuous(self.rawCapture,
            format="bgr", use_video_port=True)

        # initialize the frame and the variable used to indicate
        # if the thread should be stopped
        self.frame = None
        self.stopped = False

    def start(self):
        # start the thread to read frames from the video stream
        t = Thread(target=self.update, args=())
        t.daemon = True
        t.start()
        return self

    def update(self):
        # keep looping infinitely until the thread is stopped
        for f in self.stream:
            # grab the frame from the stream and clear the stream in
            # preparation for the next frame
            self.frame = f.array
            self.rawCapture.truncate(0)
            # if the thread indicator variable is set, stop the thread
            # and resource camera resources
            if self.stopped:
                self.stream.close()
                self.rawCapture.close()
                self.camera.close()
                return

    def read(self):
        # return the frame most recently read
        return self.frame

    def stop(self):
        # indicate that the thread should be stopped
        self.stopped = True

#-----------------------------------------------------------------------------------------------  
# Currently not used but included in case you want to check speed
def show_FPS(start_time,frame_count):
    if debug:
        if frame_count >= FRAME_COUNTER:
            duration = float(time.time() - start_time)
            FPS = float(frame_count / duration)
            print("Processing at %.2f fps last %i frames" %( FPS, frame_count))
            frame_count = 0
            start_time = time.time()
        else:
            frame_count += 1
    return start_time, frame_count

#-----------------------------------------------------------------------------------------------  
def check_image_match(full_image, small_image):
    # Look for small_image in full_image and return best and worst results
    # Try other MATCH_METHOD settings per config.py comments
    # For More Info See http://docs.opencv.org/3.1.0/d4/dc6/tutorial_py_template_matching.html
    result = cv2.matchTemplate( full_image, small_image, MATCH_METHOD)  
    # Process result to return probabilities and Location of best and worst image match
    minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(result)  # find search rect match in new image
    return maxLoc, maxVal
    
#-----------------------------------------------------------------------------------------------  
def xy_at_edge(xy_loc):  # check if search rect is near edge plus buffer space
    near_edge = False
    if ( xy_loc[0] < sw_buf_x 
      or xy_loc[0] > CAMERA_WIDTH - (sw_buf_x + sw_w)
      or xy_loc[1] < sw_buf_y 
      or xy_loc[1] > CAMERA_HEIGHT - (sw_buf_y + sw_h)):
        near_edge = True
        if debug:
            print("xy_at_edge - xy(%i, %i) xyBuf(%i,%i)" %( xy_loc[0], xy_loc[1], sw_buf_x, sw_buf_y))
    return near_edge
    
#-----------------------------------------------------------------------------------------------  
def xy_low_val(cur_val, val_setting):
    # Check if maxVal is below MAX_SEARCH_THRESHOLD value
    bad_match = False
    if cur_val < val_setting:
        bad_match = True
        if debug:
            print("xy_low_val - maxVal=%0.5f  threshold=%0.4f" % (cur_val, val_setting))
    return bad_match

#-----------------------------------------------------------------------------------------------  
def xy_moved(xy_prev, xy_loc):
    # Check if x or y location has changed
    moved = False
    if (xy_loc[0] <> xy_prev[0] or
        xy_loc[1] <> xy_prev[1]):
        moved = True
        if debug:
            print("xy_moved   - dx=%i dy=%i " 
                         %( xy_loc[0] - xy_prev[0], xy_loc[1] - xy_prev[1]))
    return moved
        
#-----------------------------------------------------------------------------------------------  
def xy_big_move(xy_prev, xy_new):
    big_move = False        
    if (abs( xy_new[0] - xy_prev[0] ) > cam_move_x or
        abs( xy_new[1] - xy_prev[1] ) > cam_move_y):
            big_move = True
            if debug:
                print("xy_big-move- xy(%i,%i) move exceeded %i or %i"     
                              % ( xy_new[0], xy_new[1], cam_move_x, cam_move_y))       
    return big_move

def xy_update(xy_cam, xy_prev, xy_new):
    dx = 0
    dy = 0
    if abs(xy_prev[0] - xy_new[0]) > 0:
        dx = xy_prev[0] - xy_new[0]
    if abs(xy_prev[1] - xy_new[1]) > 0:
        dy = xy_prev[1] - xy_new[1]       
    xy_cam = ((xy_cam[0] + dx, xy_cam[1] + dy))
    if debug:
        print("xy-update  - cam xy (%i,%i) dxy(%i,%i)" 
                         % (xy_cam[0], xy_cam[1], dx, dy)) 
    return xy_cam
    
#-----------------------------------------------------------------------------------------------  
def cam_track():
    # Process steam images to find camera movement 
    # using an extracted search rectangle in the middle of one frame
    # and find location in subsequent images.  Grab a new search rect
    # as needed based on nearness to edge of image or percent probability
    # of image search result Etc.
    
    # Setup Video Stream Thread
    if vid_from_file:
        vs = cv2.VideoCapture(vid_path)
        while not vs.isOpened():
            image1 = cv2.VideoCapture(vid_path)
            cv2.waitKey(1000)
            print "Wait for the header"        
    else:
        vs = PiVideoStream().start()
        vs.camera.rotation = CAMERA_ROTATION
        vs.camera.hflip = CAMERA_HFLIP
        vs.camera.vflip = CAMERA_VFLIP
        time.sleep(2.0)    # Let camera warm up

    if WINDOW_BIGGER > 1:  # Note setting a bigger window will slow the FPS
        big_w = int(CAMERA_WIDTH * WINDOW_BIGGER)
        big_h = int(CAMERA_HEIGHT * WINDOW_BIGGER) 
    
    sw_maxVal = MAX_SEARCH_THRESHOLD  # Threshold Accuracy of search in image
    xy_cam = (0,0)    # xy of Cam Overall Position
    xy_new = sw_xy    # xy of current search_rect
    xy_prev = xy_new  # xy of prev search_rect
    search_reset = False  # Reset search window back to center 
     
    # Read first image frame from video file or camera 
    if vid_from_file:
        flag, image1 = vs.read() 
        cv2.waitKey(1000)   # Wait a little   
        if flag:
            search_rect = image1[sw_y:sw_y+sw_h,sw_x:sw_x+sw_w]           
        else:
            print "frame is not ready"
            cv2.waitKey(1000)    
    else:
        image1 = vs.read()    # Grab image from video stream thread 
        search_rect = image1[sw_y:sw_y+sw_h, sw_x:sw_x+sw_w]  # Init centre search rectangle 
        
    while True:
        if vid_from_file:
            flag, image1 = vs.read()
            if not flag:
                cv2.waitKey(1000)  
        else:
            image1 = vs.read()    # Grab image from video stream thread 
            
        xy_new, xy_val = check_image_match(image1, search_rect)
        
        # Analyse new xy for issues
        if xy_moved(xy_prev, xy_new):
            if (xy_big_move(xy_prev, xy_new) or
                xy_at_edge(xy_new) or
                xy_low_val(xy_val, sw_maxVal)):
               search_reset = True  # Reset search to center
            else:
                # update new cam position
                xy_cam = xy_update(xy_cam, xy_prev, xy_new)
                xy_prev = xy_new
        
        if search_reset:   # Reset search_rect back to center         
            if debug and not log_only_moves:
                print("cam-track  - Reset search_rect img_xy(%i,%i) CamPos(%i,%i)" 
                                           % (xy_new[0], xy_new[1], xy_cam[0], xy_cam[1]))        
            search_rect = image1[sw_y:sw_y+sw_h, sw_x:sw_x+sw_w]
            xy_new = sw_xy
            xy_prev = xy_new            
            search_reset = False
 
        if debug and not log_only_moves : 
            print("cam-track  - Cam Pos(%i,%i) %0.5f  img_xy(%i,%i)" 
                     % ( xy_cam[0], xy_cam[1], xy_val, xy_new[0], xy_new[1] ))
            
        if window_on:
            image2 = image1
            # Display openCV window information on RPI desktop if required
            if show_circle:            
               cv2.circle(image2,(image_cx, image_cy), CIRCLE_SIZE, red, 1) 
            if show_search_rect:            
                cv2.rectangle(image2,( xy_new[0], xy_new[1] ),
                                     ( xy_new[0] + sw_w, xy_new[1] + sw_h ),
                                     green, LINE_THICKNESS)     # show search rect                                    
            # Show Cam Position text on bottom of opencv window
            m_text = ("CAM POS( %i %i )   " % (xy_cam[0], xy_cam[1]))
            cv2.putText(image2, m_text, 
                       (image_cx - len(m_text) * 3, CAMERA_HEIGHT - 15 ), 
                        cv2.FONT_HERSHEY_SIMPLEX, CV_FONT_SIZE, green, 1)                        
            if WINDOW_BIGGER > 1:
                image2 = cv2.resize( image2,( big_w, big_h ))
            cv2.imshow('Cam-Track  (q in window to quit)',image2) 

            if show_search_wind:
                cv2.imshow( 'search rectangle', search_rect )         

            if cv2.waitKey(1) & 0xFF == ord('q'):
                vs.stop()    # Stop video stream thread
                cv2.destroyAllWindows()
                print("End Cam Tracking")
                break
     
#-----------------------------------------------------------------------------------------------    
if __name__ == '__main__':
    try:
        cam_track()
    finally:
        print("")
        print("+++++++++++++++++++++++++++++++++++")
        print("%s %s - Exiting" % (progname, ver))
        print("+++++++++++++++++++++++++++++++++++")
        print("")                                



