import cv2
import numpy as np
from numpy.lib import type_check
import tensorflow.keras
from PIL import Image, ImageOps
import threading

cap = cv2.VideoCapture(0)

size = (224, 224)

# model = tensorflow.keras.models.load_model('keras_model.h5') # 모델 가져오기(소방차, 사이렌도 학습시켜야 할듯)
# classes = ['Fire', 'none', 'none', 'none', 'none', 'none', 'none']

ret, frame2 = cap.read()
while cap.isOpened:
    ret, frame1 = cap.read() #이거 앞에 프레임 가져오는 애인데 while 문 밖에 나가면 영상재생 안됨 ㅋㅋ
    ret, frame2 = cap.read() 

    diff = cv2.absdiff(frame1, frame2) # 앞에 프레임에서 뒤에 프레임을 빼고 diff에 저장
    small = cv2.resize(diff, dsize=(0, 0), fx=0.05, fy=0.05)
    blur = cv2.GaussianBlur(small, (5,5), 0) # 화면내 블러 효과를 줌으로써 움직일 때 플리커링(깜빡임)이 줄어듦, (5,5)는 커널 크기
    gray = cv2.cvtColor(blur, cv2.COLOR_BGR2GRAY) # 움직임 감지 프레임을 BGR 변수에서 각각 행렬 ([숫자1, 숫자2, 숫자3])을 ([숫자1])로 줄여줬기 때문에 연산량과 메모리를 줄임
    _, thresh = cv2.threshold(gray, 20, 255, cv2.THRESH_BINARY) # 역치 20(어두운 회색)을 넘어가는 애들만 255(화이트)로 표현
    dilated = cv2.dilate(thresh, None, iterations=3) #잡힌 움직임 영역을 조금 더 키워줌(팽창기법) 그래서 인식되는 부위보다 살짝 더 여유있게 만들어줌(구멍도 매꿈)
    #result = cv2.morphologyEx(dilated, cv2.MORPH_CLOSE, (11, 11))
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        c = np.nonzero(dilated)
        if cv2.contourArea(contour) < 70:
            continue
        cv2.rectangle(frame1, (min(c[1])*20, min(c[0])*20),(max(c[1])*20, max(c[0])*20), (0,255,0),2)
        ROI = frame1[min(c[0])*20:max(c[0])*20, min(c[1])*20: max(c[1])*20]
    

    # x좌표 차이
    mtX = int(max(c[1]) - min(c[1]))*20
    # y좌표 차이
    mtY = int(max(c[0]) - min(c[0]))*20
    # 해상도 설정 contV
    constV = 224

    # 바운딩박스 x좌표 vs y좌표 길이 검사 -> 둘중에 긴 값이 constV = 254보다 크고, 작고, 같을 때 별로 padding 값 설정
    if mtX > mtY:
        long = mtX
        short = mtY
        if long > constV:
            short = int(short*constV/long)
            long = constV
            xpad = 0
        elif long < constV:
            xpad = int((constV-long)/2)
        ypad = int((constV - (constV * short) / long) / 2)
    elif mtX < mtY: 
        long = mtY
        short = mtX
        if long > constV:
            short = int(short*constV/long)
            long = constV
            ypad = 0
        elif long < constV:
            ypad = int((constV-long)/2)
        xpad = int((constV - (constV * short) / long) / 2)
    else: 
        xpad = 0
        ypad = 0
    
    # padding 값 적용하여 원하는 contV를 유지하며 해상도 설정
    ROI = cv2.resize(ROI,(constV-(xpad*2),constV-(ypad*2)))
    constraint = cv2.copyMakeBorder(ROI,ypad,ypad,xpad,xpad,cv2.BORDER_CONSTANT,value=[0,0,0])
    cv2.imshow('ROI', constraint)
    cv2.imshow('frame', frame1)
    cv2.imshow('mask', dilated)

    if cv2.waitKey(30) == 27: #키보드에 esc키를 누르면 정지하기
        break
    
cap.release()
cv2.destroyAllWindows #윈도우에 있는 cv2창 모두 끄기