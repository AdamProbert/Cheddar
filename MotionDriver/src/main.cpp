#include <Arduino.h>
#include <Wire.h>

#include "inputs/UARTCommandInput.h"
#include "outputs/ServoController.h"

namespace
{
    constexpr unsigned long kSerialBaudRate = 115200;
}

outputs::ServoController g_servoController;
inputs::UARTCommandInput g_uartInput(Serial, g_servoController);

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

    Serial.println("Servo controller ready. Sweep disabled (use 'SWEEP ON').");
}

void loop()
{
    g_uartInput.poll();
    g_servoController.update(millis());
}
