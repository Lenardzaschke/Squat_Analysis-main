import cv2, time

cap = cv2.VideoCapture(1, cv2.CAP_AVFOUNDATION)
print("opened:", cap.isOpened())

time.sleep(0.2)  # kurz warten

ok = False
for i in range(30):  # ein paar Frames "warm laufen" lassen
    ret, frame = cap.read()
    if ret and frame is not None:
        print("read: True", "shape:", frame.shape, "after tries:", i+1)
        ok = True
        break
    time.sleep(0.05)

if not ok:
    print("read: False (no frames)")

cap.release()