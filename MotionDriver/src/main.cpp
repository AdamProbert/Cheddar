#include <Arduino.h>
#include <Wire.h>

#include "inputs/UARTCommandInput.h"
#include "outputs/MotorController.h"
#include "outputs/ServoController.h"

namespace
{
    constexpr unsigned long kSerialBaudRate = 115200;
}

outputs::ServoController g_servoController;
outputs::MotorController g_motorController;
inputs::UARTCommandInput g_uartInput(Serial, g_servoController, g_motorController);

void setup()
{
    g_uartInput.begin(kSerialBaudRate);

    Serial.println("Cheddar bring-up");

    if (!g_servoController.begin(Wire))
    {
        Serial.println("Servo controller init failed. Halting.");
        while (true)
        {
            delay(1000);
        }
    }

    if (!g_motorController.begin())
    {
        Serial.println("Motor controller init failed. Halting.");
        while (true)
        {
            delay(1000);
        }
    }

    Serial.println("Servo controller ready. Sweep disabled (use 'SWEEP ON').");
    Serial.println("Motor controller ready. Use 'MOTOR' commands to drive the motor.");
}

void loop()
{
    g_uartInput.poll();
    g_servoController.update(millis());
}
