import cv2

def test_function(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return gray




# import cv2
# cam = cv2.VideoCapture(0)
# while cam.isOpened():
#     ret, frame = cam.read()
#     if ret == False:
#         break
#     cv2.imshow('WebCam', frame)
#     if cv2.waitKey(1) == ord('q'):
#         break