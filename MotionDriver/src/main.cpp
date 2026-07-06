#include <Arduino.h>
#include <Wire.h>

#include "inputs/UARTCommandInput.h"
#include "outputs/MotorController.h"
#include "outputs/ServoController.h"
#include "pins.h"

namespace
{
    constexpr unsigned long kSerialBaudRate = 115200;
}

outputs::ServoController g_servoController;
outputs::MotorController g_motorController;
// Command input runs over USB Serial (UART0) - the Raspberry Pi connects via USB.
inputs::UARTCommandInput g_uartInput(Serial, g_servoController, g_motorController);

void setup()
{
    // USB Serial (UART0) carries commands to/from the Raspberry Pi.
    Serial.begin(kSerialBaudRate);
    while (!Serial && millis() < 3000)
    {
    } // Wait up to 3s for USB serial

    g_uartInput.begin(kSerialBaudRate);

    Serial.println("Cheddar bring-up");
    Serial.println("USB Serial (UART0) ready for Pi communication");

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
    g_uartInput.update(millis());
    g_servoController.update(millis());
}
