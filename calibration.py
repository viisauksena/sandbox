#!/usr/bin/python

import ConfigParser as configparser
import cv2
import cv2 as cv
from freenect import sync_get_depth
import frame_convert
import numpy as np
from skimage import exposure
import pickle
import sys

# Various options:
parser = configparser.ConfigParser()
parser.read("config.ini")
try:
    height_shift = float(parser.get("main", "height_shift"))
except configparser.NoOptionError:
    height_shift = 0
height_scale = float(parser.get("main", "height_scale"))
offset=3.5
screen_resolution_x = int(parser.get("main", "screen_resolution_x"))
screen_resolution_y = int(parser.get("main", "screen_resolution_y"))

# Compute proper fullscreen constants for openCV version:
fullscreen_const = None
winnormal_const = None
try:
    fullscreen_const = cv2.cv.CV_WINDOW_FULLSCREEN
    winnormal_const = cv2.cv.CV_WINDOW_NORMAL
except AttributeError:
    fullscreen_const = cv2.WINDOW_FULLSCREEN
    winnormal_const = cv2.WINDOW_NORMAL

# initialize the list of reference points and boolean indicating
# whether cropping is being performed or not
reference_points = []
cropping = False
done_image=None
fontFace = cv2.FONT_HERSHEY_SCRIPT_SIMPLEX;
fontScale = 2;
thickness = 3;
baseline=0;
textSize = cv2.getTextSize("1", fontFace,fontScale, thickness);
baseline += thickness;

offset=50
#  er x dann y
#     640    480
offsetstrup=[(offset,offset), (640-offset,offset), (offset,480-offset), (640-offset,480-offset)]
offsetsarr=[[offset,offset], [640-offset,offset], [offset,480-offset], [640-offset,480-offset]]
savefile='cal.p'

def weirdyze_ratio(points):
    for i in range(0,3):
        point=[]
        point.append(points[i][1])
        point.append(points[i][0])
        points[i]=point
    return points

def offset_points(points):
    for i in range(0,3):
        point=[]
        point.append(offsetsarr[i][0]-points[i][0])
        point.append(offsetsarr[i][1]-points[i][1])
        points[i]=point
    return points

def invert_offsets(offsets):
    for i in range(0,3):
        offset=[]
        offset.append(offsetsarr[i][1])
        offset.append(offsetsarr[i][0])
        offsets[i]=offset
        print "dehhh"
        #print (offset,i)

    return offsets

def contractions(img, points):
    global done_image
    #img.shape = (480, 640)
    #img = offset_points(points)
    print "\nimg.shape:%s\npoints:%s\noffsetsarr:%s\n" %(img.shape,points,offsetsarr)
    y,x = img.shape
    #y -= offset
    #x -= offset
    pts1 = np.float32(points)
    pts2 = np.float32(offsetsarr)
    M = cv2.getPerspectiveTransform(pts1,pts2)
    #print "off %s , point %s" %()
    dst = cv2.warpPerspective(img,M,(x,y))
    print dst
    done_image=dst

test_img = cv2.imread('images/kinect.png', 0)
no_kinect = False
def get_depth():
    global no_kinect
    if no_kinect:
        return test_img
    get_depth_result = sync_get_depth()
    if get_depth_result == None or \
            get_depth_result[0] == None:
        no_kinect = True
        return test_img
    return frame_convert.pretty_depth(get_depth_result[0])

def get_image():
    image = get_depth()
    N = 4
    arr = np.array(image,dtype=np.float) / N
    for i in range(1,N):
        image=get_depth() # - img_avgi
        imarr=np.array(image,dtype=np.float)
        arr=arr+imarr/N
    # Round values in array and cast as 8-bit integer
    arr=np.array(np.round(arr),dtype=np.uint8)
    img=exposure.rescale_intensity(arr, in_range=(160,190))
    return img

done=False
points=None
def click_and_crop(event, x, y, flags, param):
    # grab references to the global variables
    global reference_points, cropping, done, points
 
    # if the left mouse button was clicked, record the starting
    # (x, y) coordinates and indicate that cropping is being
    # performed
    if event == cv2.EVENT_LBUTTONDOWN:
        if cropping == False:
            reference_points.append([x, y])
        else:
            reference_points.append([y, x])
            done=True
 
    # check to see if the left mouse button was released
    elif event == cv2.EVENT_LBUTTONUP:
        # record the ending (x, y) coordinates and indicate that
        # the cropping operation is finished
        if cropping == False:
            reference_points.append([y, x])
        cropping = True
 
        # draw a rectangle around the region of interest
        #cv2.rectangle(image, reference_points[0], reference_points[1], (0, 255, 0), 2)
        #cv2.line(image,reference_points[0],reference_points[1],(255,0,0),5)
        if done == True:
            reference_points.append([x, y])
            points = reference_points
            contractions(image, weirdyze_ratio(points))
            done=False
            cropping=False
        cv2.imshow("image", get_image()) 

image=get_image()
cv2.namedWindow("image", winnormal_const)
cv2.setWindowProperty("image", cv2.WND_PROP_FULLSCREEN,
    fullscreen_const)
cv2.setMouseCallback("image", click_and_crop)
 
# keep looping until the 'q' key is pressed
while True:
    # display the image and wait for a keypress
    if isinstance(done_image, np.ndarray):
        break
    image=get_image()
    #if len(reference_points) >= 2:
    #    cv2.line(image,reference_points[0],reference_points[1],(255,0,0),5)
    #if len(reference_points) >= 4:
    #    cv2.line(image,reference_points[2],reference_points[3],(255,0,0),5)
    cv2.circle(image,offsetstrup[0], 5, (230), -1)
    cv2.putText(image, "1", offsetstrup[0], fontFace, fontScale,(offset,offset), thickness, 8);
    cv2.circle(image,offsetstrup[1], 5, (230), -1)
    cv2.putText(image, "2", offsetstrup[1], fontFace, fontScale,(offset,offset), thickness, 8);
    cv2.circle(image,offsetstrup[2], 5, (230), -1)
    cv2.putText(image, "3", offsetstrup[2], fontFace, fontScale,(offset,offset), thickness, 8);
    cv2.circle(image,offsetstrup[3], 5, (230), -1)
    cv2.putText(image, "4", offsetstrup[3], fontFace, fontScale,(offset,offset), thickness, 8);
    image_float = np.ndarray.astype(image, dtype=np.float64)
    image_float = (255.0 - ((255.0 - image_float) * height_scale + height_shift))
    image_float = image_float.clip(min=0.0, max=255.0)
    image = np.ndarray.astype(image_float, dtype=np.uint8)
    resized = cv2.resize(image, (screen_resolution_x, screen_resolution_y), interpolation = cv2.INTER_AREA)
    cv2.imshow("image", resized)
    key = cv2.waitKey(1) & 0xFF   
 
    # if the 'c' or escape key is pressed, break from the loop
    if key == ord("c") or key == 27:
        cv2.destroyAllWindows()
        sys.exit(0)
    elif key == 255:
        continue
    else:
        print("UNKNOWN KEY: " + str(key))

if len(points) == 4:
    pickle.dump(points, open( savefile, "wb" ))
    print "write!!"
    while 1:
        cv2.imshow("image", done_image)
        cv.waitKey(10)
        #contractions(get_image(), points)
 
# close all open windows
cv2.destroyAllWindows()
