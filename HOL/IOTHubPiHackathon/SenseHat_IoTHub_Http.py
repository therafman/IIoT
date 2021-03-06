"""
Sample code demonstrating Sense HAT running on Raspian and Raspberry Pi 3 sending sensor data to Azure IoT Hub using Azure IoT Hub REST API.

Azure IoT Hub REST API reference https://docs.microsoft.com/en-us/rest/api/iothub/

Sense HAT API reference https://pythonhosted.org/sense-hat/api/

Adapted from https://github.com/Azure-Samples/iot-hub-python-get-started
"""

import base64
import hmac
import hashlib
import time
import requests
import urllib
import time
import sys

#If using emulator, uncomment 'from sense_emu import SenseHat ' and comment out 'from sense_hat import SenseHat'
#from sense_hat import SenseHat #if using a physical SenseHat attached to Raspi
from sense_emu import SenseHat #if using a Sense HAT Emulator (Linux only)

class IoTHub:
    
    API_VERSION = '2016-02-03'
    TOKEN_VALID_SECS = 10
    TOKEN_FORMAT = 'SharedAccessSignature sig=%s&se=%s&skn=%s&sr=%s'
    
    def __init__(self, connectionString=None):
        if connectionString != None:
            iotHost, keyName, keyValue = [sub[sub.index('=') + 1:] for sub in connectionString.split(";")]
            self.iotHost = iotHost
            self.keyName = keyName
            self.keyValue = keyValue
            
    def _buildExpiryOn(self):
        return '%d' % (time.time() + self.TOKEN_VALID_SECS)
    
    def _buildIoTHubSasToken(self, deviceId):
        resourceUri = '%s/devices/%s' % (self.iotHost, deviceId)
        targetUri = resourceUri.lower()
        expiryTime = self._buildExpiryOn()
        toSign = '%s\n%s' % (targetUri, expiryTime)
        key = base64.b64decode(self.keyValue.encode('utf-8'))

        if sys.version_info[0] < 3:
            signature = urllib.quote(
                base64.b64encode(
                    hmac.HMAC(key, toSign.encode('utf-8'), hashlib.sha256).digest()
                )
            ).replace('/', '%2F')
        else:
            signature = urllib.parse.quote(
                base64.b64encode(
                    hmac.HMAC(key, toSign.encode('utf-8'), hashlib.sha256).digest()
                )
            ).replace('/', '%2F')

        return self.TOKEN_FORMAT % (signature, expiryTime, self.keyName, targetUri)
    
    def registerDevice(self, deviceId):
        sasToken = self._buildIoTHubSasToken(deviceId)
        url = 'https://%s/devices/%s?api-version=%s' % (self.iotHost, deviceId, self.API_VERSION)
        body = '{deviceId: "%s"}' % deviceId
        r = requests.put(url, headers={'Content-Type': 'application/json', 'Authorization': sasToken}, data=body)
        return r.text, r.status_code

    def sendD2CMsg(self, deviceId, message):
        sasToken = self._buildIoTHubSasToken(deviceId)
        url = 'https://%s/devices/%s/messages/events?api-version=%s' % (self.iotHost, deviceId, self.API_VERSION)
        r = requests.post(url, headers={'Authorization': sasToken}, data=message)
        return r.text, r.status_code
    
if __name__ == '__main__':

    #You can obtain the connection string from portal.azure.com -> IoT Hub -> <IoT_Hub_Name> -> Shared Access Policies
    #To send messages, ensure you use a shared access policy with at least 'device connect' permissions.
    #To register a new device, ensure you use a shared access policy with at least 'registry write' permissions.
    #The connection string will resemble:
    #   'HostName=myiothub.azure-devices.net;SharedAccessKeyName=iothubowner;SharedAccessKey=sdilhjlEDPvgcc1kIAW5bDlNQG6/Y7zJSoi6qSiNpcio='
    connectionString = ''
    
    #This is the device name that will be registered in the IoT Hub. 
    #If it is already registered, it will error and continue on.
    deviceId = 'Device100'
    
    iotHubConn = IoTHub(connectionString)
    sense = SenseHat()
    
    while True:

        try:
            #Uncomment this code if you want the device to self-register with IoT Hub. Otherwise use Device Explorer to register device.
            #print('Registering device... ' + deviceId)
            #print(iotHubConn.registerDevice(deviceId))

            #Send current temperature from the Sense HAT temp sensor
            #Refer to Sense HAT API to send other Sense HAT sensor data https://pythonhosted.org/sense-hat/api/
            message = str(sense.temp) 
            print('Sending message... ' + message)
            print(iotHubConn.sendD2CMsg(deviceId, message))
            time.sleep(5) # 5 second delay
        except OSError as e:
            print('Error: ' + str(e))
            break
