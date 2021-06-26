#!/usr/bin/python3
import requests, urllib.parse, urllib.error, base64, json, re
import picamera
import os
import sys
from gpiozero import Button, LED
from time import sleep
from subprocess import check_call
import time

# camera button setup (it's the BCM number, not pin number)
camera_start_button = Button(27)    # blue button
camera_stop_button = Button(22)     # red button

# set up Raspberry Pi Camera
camera = picamera.PiCamera()
camera.resolution = (640, 480)
print(camera.resolution)
camera.start_preview()


# microsoft vision api key requirement for microsoft computer vision service
api_key = "ef85b3f9ae6c4793a7f9684dbbaa18ab"
endpoint = "http://eastasia.api.cognitive.microsoft.com/vision/v3.0/analyze"

# set up microsoft computer vision service API
headers = {'Ocp-Apim-Subscription-Key': api_key ,
 "Content-Type": "application/octet-stream" }
params = {'visualFeatures': 'Categories, Description, Color'}


# function - for red lED blink
def led_blink(seconds):
        red = LED(12)       # set pin number
        red.on()
        sleep(seconds)
        red.off()

# function - make raspberry pi speak! (through bluetooth speaker/bluetooth earphone)
def espeak(text):
    lang = ''
    rl = re.compile((r'^[а-яё].+$'), re.I)
    if rl.search(text): lang = '-ven+f4 -a 300 -s 150 -p100'    # some options to determine wanted voice
    command = 'espeak '+lang+'"'+text+'" --stdout |aplay'       # text is the sentence we want it to say
    os.system(command)

# function - excute when camera_start_button is pressed(camera on and start to shot)
def camera_on():
    camera.start_preview()
    led_blink(0.5)      # call preview led_blink function
    camera.capture('/home/pi/image.jpg')            # store captured image
    body = open('/home/pi/image.jpg', "rb").read()  # read same image again from file
    try:
        # call microsoft computer vision service
        response = requests.post(endpoint, headers=headers, params=params, data=body )  
        response.raise_for_status()

        analysis = response.json()  # get the result .json file from microsoft computer vision service

        # get model output sentence from .json file
        image_caption = analysis["description"]["captions"][0]["text"].capitalize()  
        print(image_caption)

        f = open('/home/pi/predict_output.txt', 'a+')
        f.write(image_caption)      # write result sentences in  "predict_output.txt"
        f.write('\n')
        f.close()

        # validate text before system() call; if pass, speak out the sentence
        if re.match("^[a-zA-z ]+$", image_caption):
            espeak(image_caption)
        else :
            espeak("i do not know what i saw!")

    except Exception as e:
        print (e.args)

# function - excute when camera_stop_button is pressed
def camera_stop():
    led_blink(1)
    print("Button is pressed")
    camera.stop_preview()

    localtime = time.asctime(time.localtime(time.time( )))
    f = open('/home/pi/predict_output.txt', 'a+')
    f.write(localtime)
    f.write('\n')
    f.close()

# main 
while True:
    if camera_stop_button.is_pressed:
        camera_stop()
        break
    else:
        camera_start_button.when_pressed = camera_on
