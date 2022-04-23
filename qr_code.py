import cv2
def my_scanner():
    cap = cv2.VideoCapture(0)
    detector = cv2.QRCodeDetector()
    while True:
        _,img = cap.read()
        data, bbox, _ = detector.detectAndDecode(img)
        if data:
            a=data
            break
    print(data)
    cap.release()
    return data
