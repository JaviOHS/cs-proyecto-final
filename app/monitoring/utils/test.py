import cv2

def test_function(frame, session):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return gray
