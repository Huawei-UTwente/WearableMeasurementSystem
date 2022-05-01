# README #

### What is this repository for? ###

* This repo contains the wireless communication setup of the wearable measurement system. 
* 1.0

### What are required before using this setup? ###

* Xsens Suit (link or Awinda)
* Xsens MVN software and corresponding license key
* Moticon pressure insoles
* Moticon OpenGo mobile App (only works for Android system)
* Moticon EndPoint SDK

### How to set up? ###
* Set up the Xsens Suit inside the MVN software
* Turn on the remote control (and the remote data streaming feature if frame by frame data streaming is needed)
* Set up the Moticon insoles inside hte OpenGo mobile App
* Set up the python environment for remote control, link the EndPoint SDK and install required packages
* Connect the Mobile phone (for OpenGo app) and the computer host (for python env) into the same sub-network. It is not recommend to use the University network, which may have issue of the UDP connnection.
* Check the IP address of the mobile phone (in the setting of OpenGo app) and the computer host. Change them in the python.
* Run the python code, which will stay in idel mode.
* Start and stop recording using the OpenGo app. 
* Python code will lisening the data flow of the Insoles. Once it detected the data flow, all recording will be started.

### Two modes ###
* XsensMotion_RemoteControl_SychronizedRecording.py : for synchronized recording in each system (Moticon pressure insoles and Xsens MVN software)
* XsensMoticon_FrameByFrameStream_UDP.py: for frame by frame data streaming

### Contribution guidelines ###

* push corrections
* push new modules

### Citation ###
* To be added

### Who do I talk to? ###

* Repo owner or admin
* Huawei Wang: h.wang-2@utwente.nl



