# Cheddar  

Cheddar is an experimental robotics platform designed for exploration, stair climbing, and general terrain traversal. It serves as a **test bed for future additions** such as autonomous navigation, robotic arms, and even fun extras like a dog treat dispenser. The project combines low-level motor/servo control with high-level navigation and control logic, split across microcontrollers and a Raspberry Pi.  

## Hardware Overview  

- **Arduino Mega** – main controller (chosen for GPIO pin availability)  
- **ESP32-C3 SuperMini** – initial prototype MCU (being phased out)  
- **DRV8833 motor drivers** – 3× dual H-bridge drivers for DC motors  
- **PCA9685** – 16-channel servo controller for steering/actuation  
- **Raspberry Pi 3** – high-level control, video streaming, and web interface  
- **11.1V LiPo battery** with buck converters (step-down to 6V for motors/servos)  

## Software Overview  

- Arduino firmware for motor, servo, and encoder handling  
- High-level commands (e.g. "left", "forward") issued from Raspberry Pi to MCU over serial  
- Libraries used: Adafruit PCA9685 driver, standard Arduino motor/servo control libraries  
- Modular design for expansion into autonomy, manipulation, and other experimental features  

## Current Status  

- Basic motor driver and servo control functional  
- Serial communication between Pi and Mega in testing  
- Perfboard layout and wiring in progress  
