# cam-track.py  - Camera Movement Tracker Demo
#### A Raspberry Pi Camera Pan-Tilt Tracker using openCV2 & Video Stream

### Quick Install   
Easy Install of cam-track onto a Raspberry Pi Computer with latest Raspbian. 

    curl -L https://raw.github.com/pageauc/rpi-cam-track/master/cam-track-install.sh | bash

From a computer logged into the RPI via ssh(Putty) session use mouse to highlight command above, right click, copy.  
Then select ssh(Putty) window, mouse right click, paste.  The command should 
download and execute the github cam-track-install.sh for the raspberry pi camera pan-tilt tracker.  
This install can also be done directly on an Internet connected Raspberry Pi via a terminal session and web browser.      
Note - a raspbian apt-get update and upgrade will be performed as part of install 
so it may take some time if these are not up-to-date

#### or Manual Install   
From logged in RPI SSH session or console terminal perform the following.

    wget https://raw.github.com/pageauc/rpi-cam-track/master/cam-track-install.sh
    chmod +x can-track-install.sh
    ./cam-track-install.sh
    cd rpi-cam-track
    ./cam-track.py

### Reference Links
YouTube Video Demo https://youtu.be/yjA3UtwbD80   
YouTube Video Code Walkthrough https://youtu.be/lkh3YbbNdYg   
RPI Forum Post https://www.raspberrypi.org/forums/viewtopic.php?p=1027463#p1027463  
Github Repo https://github.com/pageauc/rpi-cam-track   
    
### Program Description
This is a raspberry pi computer openCV2 program that tracks camera (pan/tilt)
 movements. It requires a RPI camera module installed and working. The program is 
written in python2 and uses openCV2.  

It captures a search rectangle from the center of a video stream tread image. 
It then locates the rectangle in subsequent images based on a score value and
returns the x y location in the image based on a threshold accuracy.  
If movement gets too close to the sides of the image or
a suitable image search match cannot be found, then another search rectangle
is selected. This data is processed to track a cumulative pixel location based on
an initial camera image center value of 0,0.    
This code could be used for a simple robotics application, movement stabilization, 
searching for an object image in the video stream rather than taking a search
rectangle from the stream itself.  Eg look for a dog.
where the camera is mounted on a moving platform or object, Etc. 
I will be working to implement Robot (without wheel encoders) Navigation
Test using this camera tracking.

### Project - Accurate Robot Navigation without wheel encoders using camera tracking
I am looking at saving high value search rectangles that
are spaced out around the full xy range of the camera movement and use those
to correct any tracking errors. These check point rectangles will also need to
be updated if a better check point rectangle (higher maxVal) is found in the same region. 
I was thinking approx every half image spacing in xy cam position. 
This would allow it to self correct position drift (self calibrating). 
I am hoping to test this on a robot that does not have wheel encoders. 
Camera tracking could allow the robot to more accurately navigate and rotate.
I am pleased with the current FPS with ver 0.85. The multi version is not very
stable due to segment faults so I will stick with only the video stream being
threaded. 
If you decide to try this as well, let me know.
Claude ...

Note: This application is a demo and is currently still in development, but I 
thought it could still be useful, since I was not able to find a similar
RPI application that does this.  Will try to implement an object searcher based
on this demo.
                         
### Tuning
You may have to experiment with some settings to optimize performance. See comments in
config.py regarding MATCH_METHOD values.     
For more information regarding match
methods see http://docs.opencv.org/3.1.0/d4/dc6/tutorial_py_template_matching.html

Possible match methods are below (passed via config.py MATCH_METHOD variable as integer)    

* cv2.TM_SQDIFF = 0    
* cv2.TM_SQDIFF_NORMED = 1    
* cv2.TM_CCORR = 2    
* cv2.TM_CCORR_NORMED = 3  (default)  
* cv2.TM_CCOEFF = 4    
* cv2.TM_CCOEFF_NORMED = 5    

If there are plain backgrounds or random motions in camera view then the
tracking coordinate values may drift out of sync.
Edit the config.py file per variable comments using the nano editor or similar.
I personally like to use filezilla configured with SFTP-SSH Protocol to transfer files to/from my
various Raspberry Pi computers and then edit on my PC using NotePad ++.

The main variables are

#### MAX_SEARCH_THRESHOLD - default is .97
This variable sets the value for the highest accuracy for maintaining a 
lock on the search rectangle found in the stream images.  Otherwise another similar block will be returned.  
Setting this higher will force a closer match to the original search rectangle. 
If you have a unique background features then set this higher eg .98, .99 
or for a background with fewer unique features set it lower since the match criteria
will not be able to be met.  Review debug data for your environment.

#### cam_move_x and cam_move_y - defaults 10 and 8
These variables set the maximum x and y pixel movement allowed in one loop cycle.
This reduces unexpected cam position changes when objects move through the 
camera image view quickly.  The search_rect can lock onto the moving objects
pixel pattern and track it. When this happens, the cam position
will get out of sync since it is not tracking the image background properly.
Balance the setting with the normal expected cam movement speed.  
defaults are 10 and 8


Use a text editor to review config.py file for other variable settings.  Eg. 

    nano cam-track.py
    
nano editor is just a suggestion.  You can use whatever editor you are
comfortable with

### Developement Ideas

* Save high value search rectangles and position data so when the camera
view is later in the same zone or vicinity it can use the reference to correct
camera position.
* Have a library of preset images of objects or things that can be recognized.
this could be used for finding something in the camera view.
* Change or add feature to have camera position tracked in degrees so left
would start at 360 and right 0 rather than left starting negative and right positive.
* Add feature to remember a course via larger search rectangles that can be played back
to repeat course or retrace backwards
* Add feature to remember camera position data changes (only save changed values within a
specific +- range) This could include since last reading.  This might be useful for
repeating actions based on camera tracking.
* Add passing of video file path and/or other information via command line parameter(s)

### Credits

Thanks to Adrian Rosebrock jrosebr1 at http://www.pyimagesearch.com 
for the PiVideoStream Class code available on github at
https://github.com/jrosebr1/imutils/blob/master/imutils/video/pivideostream.py

Have Fun Claude Pageau

YouTube Channel https://www.youtube.com/user/pageaucp     
GitHub https://github.com/pageauc   


