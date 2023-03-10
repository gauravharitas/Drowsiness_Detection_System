from scipy.spatial import distance
from imutils import face_utils
import imutils
import dlib
import cv2
from pygame import mixer 


import mysql.connector 

host = "localhost"
user  = "root"
pswd = "12345678"
db = "Drowsiness_Detection"

MyDB = mysql.connector.connect(host = host, user = user, password = pswd, database = db)

MyCursor = MyDB.cursor()

MyCursor.execute("CREATE TABLE IF NOT EXISTS Images (id int(45) NOT NULL PRIMARY KEY AUTO_INCREMENT, Photo LONGBLOB NOT NULL)")


def retrieveImage(ID):
    SQLStatement2 = "SELECT * FROM Images WHERE id = '{0}'"
    MyCursor.execute(SQLStatement2.format(str(ID)))
    MyResult = MyCursor.fetchone()[1]

    StoreFilePath = "ImageOutput/img{0}.jpg".format(str(ID))

    with open(StoreFilePath, "wb") as File:
        File.write(MyResult)
        File.close()

mixer.init()
sound = mixer.Sound('alarm.wav')

def eye_aspect_ratio(eye):
	A = distance.euclidean(eye[1], eye[5])
	B = distance.euclidean(eye[2], eye[4])
	C = distance.euclidean(eye[0], eye[3])
	ear = (A + B) / (2.0 * C)
	return ear
	
thresh = 0.25
frame_check = 20
detect = dlib.get_frontal_face_detector()
predict = dlib.shape_predictor("models/shape_predictor_68_face_landmarks.dat")# Dat file is the crux of the code

(lStart, lEnd) = face_utils.FACIAL_LANDMARKS_68_IDXS["left_eye"]
(rStart, rEnd) = face_utils.FACIAL_LANDMARKS_68_IDXS["right_eye"]
cap=cv2.VideoCapture(0)
flag=0
print("Program Starting")

photoClicked = False

while True:
	ret, frame=cap.read()
	frame = imutils.resize(frame, width=450)
	gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
	subjects = detect(gray, 0)
	for subject in subjects:
		shape = predict(gray, subject)
		shape = face_utils.shape_to_np(shape)#converting to NumPy Array
		leftEye = shape[lStart:lEnd]
		rightEye = shape[rStart:rEnd]
		leftEAR = eye_aspect_ratio(leftEye)
		rightEAR = eye_aspect_ratio(rightEye)
		ear = (leftEAR + rightEAR) / 2.0
		leftEyeHull = cv2.convexHull(leftEye)							
		rightEyeHull = cv2.convexHull(rightEye)
		cv2.drawContours(frame, [leftEyeHull], -1, (0, 255, 0), 1)
		cv2.drawContours(frame, [rightEyeHull], -1, (0, 255, 0), 1)
		if ear < thresh:
			flag += 1
			# print (flag)
			if flag >= frame_check:

				cv2.putText(frame, "****************ALERT!****************", (10, 30), 
					cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2), sound.play()
				cv2.putText(frame, "****************ALERT!****************", (10,325),
					cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2), sound.play()


				# Photo saving into backend of the driver who is feeling sleepy
				if(photoClicked == False):

					try:
						retval, buffer = cv2.imencode('.jpg', frame)
						image_data = buffer.tobytes()
						SQLStatement = "INSERT INTO Images (Photo) VALUES (%s)"
						MyCursor.execute(SQLStatement, (image_data, ))
						MyDB.commit()
						print("Photo Clicked")
					
						photoClicked = True
					except Exception as e:
						print(e)
						print("Photo is not saved into the backend due to some issue")
					
							
        
		else:
			flag = 0
	cv2.imshow("Drowsiness Detection System", frame)
	key = cv2.waitKey(1) & 0xFF
	if key == ord("q"):
		break
cv2.destroyAllWindows()
cap.release() 
print("Program ended...")
