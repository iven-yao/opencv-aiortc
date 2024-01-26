from client import find_center
import cv2
import numpy

def test_find_center():
    # black background
    img = numpy.zeros((100, 100, 3), dtype='uint8')
    # draw ball
    cv2.circle(img, (50,50), 10, (255,255,255), -1)

    assert(find_center(img) == (50,50))