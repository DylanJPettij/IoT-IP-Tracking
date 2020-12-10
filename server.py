#!/usr/bin/env python3

# This file is part of the Python aiocoap library project.
#
# Copyright (c) 2012-2014 Maciej Wasilak <http://sixpinetrees.blogspot.com/>,
#               2013-2014 Christian Amsüss <c.amsuess@energyharvesting.at>
#
# aiocoap is free software, this file is published under the MIT license as
# described in the accompanying LICENSE file.

"""This is a usage example of aiocoap that demonstrates how to implement a
simple server. See the "Usage Examples" section in the aiocoap documentation
for some more information."""

import datetime
import logging

import asyncio
from time import sleep
import subprocess
from twilio.rest import Client
import aiocoap.resource as resource
import aiocoap
##added libraries
import RPi.GPIO as GPIO
import time
import os
import glob
GPIO.setmode(GPIO.BCM)
os.system('modprobe w1-gpio')
#Get rid of GPIO warnings
GPIO.setwarnings(False)
#setup GPIO ports
GPIO.setup(23, GPIO.OUT)
GPIO.setup(17, GPIO.OUT)
GPIO.setup(27, GPIO.OUT)
GPIO.setup(22, GPIO.OUT)   
green=GPIO.PWM(23,50)
red=GPIO.PWM(17,50)
yellow=GPIO.PWM(27,50)
blue=GPIO.PWM(22,50)
#turn all lights off initially
duty = 0
blue.start(duty)
yellow.start(duty)
red.start(duty)
green.start(duty)

class BlockResource(resource.Resource):
    """Example resource which supports the GET and PUT methods. It sends large
    responses, which trigger blockwise transfer."""

    def __init__(self):
        super().__init__()
        self.set_content(b"This is the resource's default content. It is padded "\
                b"with numbers to be large enough to trigger blockwise "\
                b"transfer.\n")

    def set_content(self, content):
        self.content = content
        while len(self.content) <= 1024:
            self.content = self.content + b"0123456789\n"

    async def render_get(self, request):
        return aiocoap.Message(payload=self.content)

    async def render_put(self, request):
        print('PUT payload: %s' % request.payload)
        self.set_content(request.payload)
        return aiocoap.Message(code=aiocoap.CHANGED, payload=self.content)


class SeparateLargeResource(resource.Resource):
    """Example resource which supports the GET method. It uses asyncio.sleep to
    simulate a long-running operation, and thus forces the protocol to send
    empty ACK first. """

    def get_link_description(self):
        # Publish additional data in .well-known/core
        return dict(**super().get_link_description(), title="A large resource")

    async def render_get(self, request):
        await asyncio.sleep(3)

        payload = "Three rings for the elven kings under the sky, seven rings "\
                "for dwarven lords in their halls of stone, nine rings for "\
                "mortal men doomed to die, one ring for the dark lord on his "\
                "dark throne.".encode('ascii')
        return aiocoap.Message(payload=payload)

class TimeResource(resource.ObservableResource):
    """Example resource that can be observed. The `notify` method keeps
    scheduling itself, and calles `update_state` to trigger sending
    notifications."""

    def __init__(self):
        super().__init__()
        self.handle = None

    def notify(self):
        self.updated_state()
        self.reschedule()

    def reschedule(self):
        self.handle = asyncio.get_event_loop().call_later(5, self.notify)

    def update_observation_count(self, count):
        if count and self.handle is None:
            print("Starting the clock")
            self.reschedule()
        if count == 0 and self.handle:
            print("Stopping the clock")
            self.handle.cancel()
            self.handle = None

    async def render_get(self, request):
        payload = datetime.datetime.now().\
                strftime("%Y-%m-%d %H:%M").encode('ascii')
        return aiocoap.Message(payload=payload)
    
class LookForPhones(resource.ObservableResource):
    def __init__(self):
        super().__init__()
        self.DylanOnline = False
        self.PhoneA=False
        self.PhoneB=False
        self.PhoneC=False
        self.handle = None
    def lookforphones(self):
        account_sid = "" #need to include Twilio credentials
        auth_token = ""
        
        client = Client (account_sid,auth_token) 
        IP=['192.168.86.59','192.168.86.51','192.168.86.37','192.168.86.49']
        print("---------------------------")
        DylanOnline = self.DylanOnline
        PhoneA = self.PhoneA
        PhoneB = self.PhoneB
        PhoneC = self.PhoneC
        for x in IP:
            num = (IP.index(x)+1)
            DylanOnline, PhoneA, PhoneB, PhoneC = self.ping(client,x,num,DylanOnline,PhoneA,PhoneB,PhoneC)
        print("---------------------------")
        arrayTF = [DylanOnline, PhoneA, PhoneB, PhoneC]
        self.DylanOnline = DylanOnline
        self.PhoneA = PhoneA
        self.PhoneB = PhoneB
        self.PhoneC = PhoneC
        i=0
        for x in arrayTF:
            if(x ==True):
                i=i+1
        strings = "Currently online: "
        if(DylanOnline == True):
            strings+="Dylan's Phone,"
        if(PhoneA == True):
            strings+="PhoneA,"
        if(PhoneB == True):
            strings+="PhoneB,"
        if(PhoneC == True):
            strings+="PhoneC,"
        body_ = "{} Phones are online".format(i)
        print(body_)        
        return bytes(strings,"utf-8")
    def ping(self,client,IP,x,DylanOnline,PhoneA,PhoneB,PhoneC):
                response = subprocess.Popen(['ping','-c','1',IP], stdout=subprocess.PIPE)
                stdout, stderr = response.communicate()
                if response.returncode == 0:
                    print("Iphone {} is online".format(x))
                    if(x == 1):
                        green.ChangeDutyCycle(100)
                        if(DylanOnline == False):
                            DylanOnline = True
                            print("text 1")#need to put phone number after the plus that you want to recieve the message at as well as put your Twilio number in the from section
                            client.messages.create(to ="+", from_="+", body="Dylan is Online")
                    if(x == 2):
                        blue.ChangeDutyCycle(100)
                        if(PhoneA == False):
                            PhoneA = True
                            print("text 1")
                            client.messages.create(to ="+", from_="+", body="PhoneA is Online")
                    if(x == 3):
                        yellow.ChangeDutyCycle(100)
                        if(PhoneB == False):
                            PhoneB = True
                            client.messages.create(to ="+", from_="+", body="PhoneB is Online")
                    if(x == 4):
                        red.ChangeDutyCycle(100)
                        if(PhoneC == False):
                            PhoneC = True
                            client.messages.create(to ="+", from_="+", body="PhoneC is Online")
                else:
                    print("Iphone {} is offline".format(x))
                    if(x == 1):
                        green.ChangeDutyCycle(0)
                        if(DylanOnline == True):
                            DylanOnline = False
                            client.messages.create(to ="+", from_="+", body="Dylan is offline")
                    if(x == 2):
                        blue.ChangeDutyCycle(0)
                        if(PhoneA == True):
                            PhoneA = False
                            client.messages.create(to ="+", from_="+", body="PhoneA is offline")
                    if(x == 3):
                        yellow.ChangeDutyCycle(0)
                        if(PhoneB == True):
                            PhoneB = False
                            client.messages.create(to ="+", from_="+", body="PhoneB is offline")
                    if(x == 4):
                        red.ChangeDutyCycle(0)
                        if(PhoneC == True):
                            PhoneC = False
                            client.messages.create(to ="+", from_="+", body="PhoneB is offline")
                return DylanOnline, PhoneA, PhoneB, PhoneC
    
    def notify(self):
        self.updated_state()
        self.reschedule()

    def reschedule(self):
        self.handle = asyncio.get_event_loop().call_later(2, self.notify)
    
    def update_observation_count(self, count):
        if count and self.handle is None:
            print("Starting the clock")
            self.reschedule()
        if count == 0 and self.handle:
            print("Stopping the clock")
            self.handle.cancel()
            self.handle = None
    async def render_get(self, request):
        
        payload = self.lookforphones()
        return aiocoap.Message(payload=payload)

    

# logging setup

logging.basicConfig(level=logging.INFO)
logging.getLogger("coap-server").setLevel(logging.DEBUG)

def main():
    # Resource tree creation
    root = resource.Site()
    root.add_resource(['.well-known', 'core'],
    resource.WKCResource(root.get_resources_as_linkheader))
    root.add_resource(['phone'], LookForPhones())
    root.add_resource(['time'], TimeResource())
    root.add_resource(['other', 'block'], BlockResource())
    root.add_resource(['other', 'separate'], SeparateLargeResource())
    #my code
   
    #####
    asyncio.Task(aiocoap.Context.create_server_context(root))

    asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
    main()
