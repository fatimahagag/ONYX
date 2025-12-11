# **ONYX**

ONYX is a custom-built quadruped robot designed and programmed for Columbia University’s Robotics Studio. This repository contains all the core scripts used to test servos, initialize the robot, and develop the walking gaits from the earliest diagonal-step tests to the final gait.

## Hardware

- Raspberry Pi
- 8 LX-16A Servos
- LewanSoul Serial Bus Controller
- Step-down Converter
- Battery
- -Custom 3D-printed frame [CAD Files for ONYX – (https://drive.google.com/file/d/1L9M18c2Gnh_JQXFSmAxKhAChd47cc2qR/view?usp=sharing)]

## Software

### 1. servo-test.py

- Credit to Ethan Lipson for this code. (https://github.com/ethanlipson/PyLX-16A)
- Verify LX-16A servo connections
- Check IDs, limits, and movement ranges
- Diagnose servo issues before running full walking cycles
This file was essential for early debugging and ensuring each servo responded correctly.

### 2. initialize_ONYX.py

A central setup file that:
- Sets all servos to their calibrated starting angles
- Applies min/max limits
- Ensures ONYX begins in a safe, neutral pose
This file is imported and called in every other script to guarantee consistent startup behavior.

### 3. 8cms.py
   
The first functional walking gait.
- Uses diagonal stepping
- Knee moves first, then the hip
- Achieved ~8 cm/s walking speed
- Helped identify timing, delay, and balance issues
This file marks the first time ONYX successfully walked.

### 4. 15cms.py (final walking code)
The most stable and fastest gait.
- Hip and knee move together for smoother motion
- Improved timing and offset control
- Achieved ~15 cm/s walking speed
- Represents ONYX’s final, optimized walking performance
This is the recommended script for demonstrations.

## Video Demo
[YouTube (https://youtu.be/cBjL58LRfhA?si=ny_RqOkD6PvlI4Si)]

## Author

Developed by Fatima Hagag
Columbia University – Robotics Studio
