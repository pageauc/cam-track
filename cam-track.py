#!/usr/bin/env python

progname = "cam-track.py"
version = "version 1.1"

"""
cam-track.py written by Claude Pageau pageauc@gmail.com
python opencv2 camera pan/tilt tracking
Runs on Windows, Unix using a Web Cam or RPI with picamera or Web Cam
Uses opencv template match to stabilize using high value rectangles.  Can be
used for stabilization or simple line of sight navigation base on
position deviation values of Camera Position.

This is a python opencv2 camera tracking demonstration program.
It takes a sample search rectangle from center of video stream image
and tracks its position based on a percent accuracy maxLoc
using opencv template matching. As the camera pans and tilts.
The cumulative position is displayed.

I will work on converting position based on 360 degree camera movement.
This is still very much a work in progress but I thought it would be
useful for others who might want a simple way to track camera movement.
Note the program can get confused by plain surroundings or some
other movements in the frame although this can be tuned out somewhat
using cam_move_x and cam_move_y global variables

This runs under python2 and openCV2
Github Repo https://github.com/pageauc/cam-track

Installation
-------------
Easy Install of cam-track onto a Raspbian (RPI) Debian Computer.
Cut and Paste line below into an SSH or console terminal session

curl -L https://raw.github.com/pageauc/cam-track/master/cam-track-install.sh | bash

To Run
------

cd ~/cam-track
./cam-track.py

To Change Variables Use nano or text editor to edit config.py

Good Luck  Claude ...

"""
print("%s %s using python2 and OpenCV2" % (progname, version))
print("Camera movement (pan/tilt) Tracker using openCV2 template match searching")
print("Loading Please Wait ....")

import os
mypath=os.path.abspath(__file__)       # Find the full path of this python script
baseDir=mypath[0:mypath.rfind("/")+1]  # get the path location only (excluding script name)
baseFileName=mypath[mypath.rfind("/")+1:mypath.rfind(".")]
progName = os.path.basename(__file__)
logFilePath = baseDir + baseFileName + ".log"
configFilePath = baseDir + "config.py"

# Check for variable file to import and error out if not found.
if not os.path.exists(configFilePath):
    print("ERROR - Missing config.py file - Could not find Configuration file %s" % (configFilePath))
    import urllib2
    config_url = "https://raw.github.com/pageauc/cam-track/master/config.py"
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

# Now that variables are imported from config.py Setup Logging
import logging
if loggingToFile:
    logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)-8s %(funcName)-10s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filename=logFilePath,
                    filemode='w')
elif verbose:
    print("Logging to Console per Variable verbose=True")
    logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)-8s %(funcName)-10s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
else:
    print("Logging Disabled per Variable verbose=False")
    logging.basicConfig(level=logging.CRITICAL,
                    format='%(asctime)s %(levelname)-8s %(funcName)-10s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

try:   # Check to see if opencv is installed
    import cv2
except:
    print("------------------------------------")
    print("Error - Could not import cv2 library")
    print("")
    if (sys.version_info > (2, 9)):
        print("python3 failed to import cv2")
        print("Try installing opencv for python3")
        print("For RPI See https://github.com/pageauc/opencv3-setup")
    else:
        print("python2 failed to import cv2")
        print("Try RPI Install per command")
        print("sudo apt-get install python-opencv")
    print("")
    print("Exiting %s Due to Error" % progName)
    quit()

# import the necessary packages
# -----------------------------
try:  # Add this check in case running on non RPI platform using web cam
    from picamera.array import PiRGBArray
    from picamera import PiCamera
except:
    WEBCAM = True
    pass

# import the necessary packages
import time
import datetime
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
class WebcamVideoStream:
    def __init__(self, CAM_SRC=WEBCAM_SRC, CAM_WIDTH=WEBCAM_WIDTH, CAM_HEIGHT=WEBCAM_HEIGHT):
        # initialize the video camera stream and read the first frame
        # from the stream
        self.stream = CAM_SRC
        self.stream = cv2.VideoCapture(CAM_SRC)
        self.stream.set(3,CAM_WIDTH)
        self.stream.set(4,CAM_HEIGHT)
        (self.grabbed, self.frame) = self.stream.read()

        # initialize the variable used to indicate if the thread should
        # be stopped
        self.stopped = False

    def start(self):
        # start the thread to read frames from the video stream
        t = Thread(target=self.update, args=())
        t.daemon = True
        t.start()
        return self

    def update(self):
        # keep looping infinitely until the thread is stopped
        while True:
            # if the thread indicator variable is set, stop the thread
            if self.stopped:
                    return

            # otherwise, read the next frame from the stream
            (self.grabbed, self.frame) = self.stream.read()

    def read(self):
        # return the frame most recently read
        return self.frame

    def stop(self):
        # indicate that the thread should be stopped
        self.stopped = True

#-----------------------------------------------------------------------------------------------
# Currently not used but included in case you want to check speed
def show_FPS(start_time,frame_count):
    if verbose:
        if frame_count >= FRAME_COUNTER:
            duration = float(time.time() - start_time)
            FPS = float(frame_count / duration)
            logging.info("Processing at %.2f fps last %i frames" %( FPS, frame_count))
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
        logging.info("xy(%i, %i) xyBuf(%i,%i)" %
                    ( xy_loc[0], xy_loc[1], sw_buf_x, sw_buf_y))
    return near_edge

#-----------------------------------------------------------------------------------------------
def xy_low_val(cur_val, val_setting):
    # Check if maxVal is below MAX_SEARCH_THRESHOLD value
    bad_match = False
    if cur_val < val_setting:
        bad_match = True
        logging.info("maxVal=%0.5f  threshold=%0.4f" % (cur_val, val_setting))
    return bad_match

#-----------------------------------------------------------------------------------------------
def xy_moved(xy_prev, xy_loc):
    # Check if x or y location has changed
    moved = False
    if (xy_loc[0] <> xy_prev[0] or
        xy_loc[1] <> xy_prev[1]):
        moved = True
        logging.info("dx=%i dy=%i "
                     %( xy_loc[0] - xy_prev[0], xy_loc[1] - xy_prev[1]))
    return moved

#-----------------------------------------------------------------------------------------------
def xy_big_move(xy_prev, xy_new):
    big_move = False
    if (abs( xy_new[0] - xy_prev[0] ) > cam_move_x or
        abs( xy_new[1] - xy_prev[1] ) > cam_move_y):
            big_move = True
            logging.info("xy(%i,%i) move exceeded %i or %i"
                              % ( xy_new[0], xy_new[1], cam_move_x, cam_move_y))
    return big_move

#-----------------------------------------------------------------------------------------------
def xy_update(xy_cam, xy_prev, xy_new):
    dx = 0
    dy = 0
    if abs(xy_prev[0] - xy_new[0]) > 0:
        dx = xy_prev[0] - xy_new[0]
    if abs(xy_prev[1] - xy_new[1]) > 0:
        dy = xy_prev[1] - xy_new[1]
    xy_cam = ((xy_cam[0] + dx, xy_cam[1] + dy))
    logging.info("cam xy (%i,%i) dxy(%i,%i)"
                         % (xy_cam[0], xy_cam[1], dx, dy))
    return xy_cam

#-----------------------------------------------------------------------------------------------
def cam_track():
    # Process steam images to find camera movement
    # using an extracted search rectangle in the middle of one frame
    # and find location in subsequent images.  Grab a new search rect
    # as needed based on nearness to edge of image or percent probability
    # of image search result Etc.

    if WINDOW_BIGGER > 1:  # Note setting a bigger window will slow the FPS
        big_w = int(CAMERA_WIDTH * WINDOW_BIGGER)
        big_h = int(CAMERA_HEIGHT * WINDOW_BIGGER)

    sw_maxVal = MAX_SEARCH_THRESHOLD  # Threshold Accuracy of search in image
    xy_cam = (0,0)    # xy of Cam Overall Position
    xy_new = sw_xy    # xy of current search_rect
    xy_prev = xy_new  # xy of prev search_rect
    search_reset = False  # Reset search window back to center

    image1 = vs.read()    # Grab image from video stream thread
    if WEBCAM:
        if ( WEBCAM_HFLIP and WEBCAM_VFLIP ):
            image1 = cv2.flip( image1, -1 )
        elif WEBCAM_HFLIP:
            image1 = cv2.flip( image1, 1 )
        elif WEBCAM_VFLIP:
            image1 = cv2.flip( image1, 0 )
    search_rect = image1[sw_y:sw_y+sw_h, sw_x:sw_x+sw_w]  # Init centre search rectangle

    while True:
        if vid_from_file:
            flag, image1 = vs.read()
            if not flag:
                cv2.waitKey(1000)
        else:
            image1 = vs.read()    # Grab image from video stream thread
             # Adjust image of WebCam
            if WEBCAM:
                if ( WEBCAM_HFLIP and WEBCAM_VFLIP ):
                    image1 = cv2.flip( image1, -1 )
                elif WEBCAM_HFLIP:
                    image1 = cv2.flip( image1, 1 )
                elif WEBCAM_VFLIP:
                    image1 = cv2.flip( image1, 0 )
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
            if verbose and not log_only_moves:
                logging.info("Reset search_rect img_xy(%i,%i) CamPos(%i,%i)"
                                % (xy_new[0], xy_new[1], xy_cam[0], xy_cam[1]))
            search_rect = image1[sw_y:sw_y+sw_h, sw_x:sw_x+sw_w]
            xy_new = sw_xy
            xy_prev = xy_new
            search_reset = False

        if verbose and not log_only_moves :
            logging.info("Cam Pos(%i,%i) %0.5f  img_xy(%i,%i)"
                     % ( xy_cam[0], xy_cam[1], xy_val, xy_new[0], xy_new[1] ))

        if window_on:
            image2 = image1
            # Display openCV window information on RPI desktop if required
            if show_circle:
               cv2.circle(image2,(image_cx, image_cy), CIRCLE_SIZE, red, 1)
            if show_search_rect:
                cv2.rectangle(image2,( xy_new[0], xy_new[1] ),
                                     ( xy_new[0] + sw_w, xy_new[1] + sw_h ),
                                     green, LINE_THICKNESS)  # show search rect
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
                logging.info("End Cam Tracking")
                break

#-----------------------------------------------------------------------------------------------
if __name__ == '__main__':
    try:
        while True:
            # Save images to an in-program stream
            # Setup video stream on a processor Thread for faster speed

            if vid_from_file:   # Setup Video Stream Thread
                vs = cv2.VideoCapture(vid_path)
                while not vs.isOpened():
                    image1 = cv2.VideoCapture(vid_path)
                    cv2.waitKey(1000)
                    logging.info("Wait for the header")
            elif WEBCAM:   #  Start Web Cam stream (Note USB webcam must be plugged in)
                logging.info("Initializing USB Web Camera ....")
                vs = WebcamVideoStream().start()
                vs.CAM_SRC = WEBCAM_SRC
                vs.CAM_WIDTH = WEBCAM_WIDTH
                vs.CAM_HEIGHT = WEBCAM_HEIGHT
                time.sleep(4.0)  # Allow WebCam to initialize
            else:  # Raspberry Pi Camera
                logging.info("Initializing Pi Camera ....")
                vs = PiVideoStream().start()
                vs.camera.rotation = CAMERA_ROTATION
                vs.camera.hflip = CAMERA_HFLIP
                vs.camera.vflip = CAMERA_VFLIP
                time.sleep(2.0)  # Allow PiCamera to initialize
            cam_track()
    except KeyboardInterrupt:
        vs.stop()
        print("")
        print("+++++++++++++++++++++++++++++++++++")
        print("User Pressed Keyboard ctrl-c")
        print("%s %s - Exiting" % (progName, version))
        print("+++++++++++++++++++++++++++++++++++")
        print("")
        quit(0)



