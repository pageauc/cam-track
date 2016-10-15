# cam-track-py configuration file

#-----------------------------------------------------------------------------------------------  
# Global Variable Settings
debug = True      # Set to False for no data display
window_on = True  # False=terminal only True-opencv windows (GUI desktop reqd)
fps_on = False    # Display fps (not implemented)

# Sets the maximum x y pixels that are allowed to reduce effect of objects moving in frame
cam_move_x = 12    # Max number of x pixels in one move
cam_move_y = 8    # Max number of y pixels in one move 

# Camera Settings
CAMERA_WIDTH = 320
CAMERA_HEIGHT = 240
CAMERA_HFLIP = False
CAMERA_VFLIP = True
CAMERA_ROTATION=0
CAMERA_FRAMERATE = 35  # framerate of video stream.  Can be 100+ with new R2 RPI camera module
FRAME_COUNTER = 1000   # used by fps

# OpenCV Settings
show_search_rect = True # show outline of current search box on main window
show_search_wind = False # show rectangle search_rect_1 window
show_circle = True      # show a circle otherwise show bounding rectangle on window
CIRCLE_SIZE = 3         # diameter of circle to show motion location in window
WINDOW_BIGGER = 2.0     # increase the display window size
MAX_SEARCH_THRESHOLD = .96 # default=.97 Accuracy for best search result of search_rect in stream images
LINE_THICKNESS = 1      # thickness of bounding line in pixels
CV_FONT_SIZE = .25      # size of font on opencv window default .5
red = (0,0,255)         # opencv line colours
green = (0,255,0)
blue = (255,0,0)

# search rectangle variables 
image_cx = int(CAMERA_WIDTH/2)   # x center of image
image_cy = int(CAMERA_HEIGHT/2)  # y center of image       
sw_w = int(CAMERA_WIDTH/4)    # search window width
sw_h = int(CAMERA_HEIGHT/4)   # search window height
sw_buf_x = int(sw_w/4)        # buffer to left/right of image
sw_buf_y = int(sw_h/4)        # buffer to top/bot of image
sw_x = (image_cx - sw_w/2)    # top x corner of search rect
sw_y = (image_cy - sw_h/2)    # top y corner of search rect
sw_xy = (sw_x,sw_y)          # initialize cam position tracker
