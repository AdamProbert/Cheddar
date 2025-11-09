#include <Arduino.h>
#include <Wire.h>

#include "inputs/UARTCommandInput.h"
#include "outputs/MotorController.h"
#include "outputs/ServoController.h"
#include "pins.h"

namespace
{
    constexpr unsigned long kSerialBaudRate = 115200;
    constexpr unsigned long kSerial2BaudRate = 115200;
}

outputs::ServoController g_servoController;
outputs::MotorController g_motorController;
inputs::UARTCommandInput g_uartInput(Serial2, g_servoController, g_motorController);

void setup()
{
    // USB Serial for debug/monitoring
    Serial.begin(kSerialBaudRate);
    while (!Serial && millis() < 3000)
    {
    } // Wait up to 3s for USB serial

    // UART2 for Raspberry Pi communication
    Serial2.begin(kSerial2BaudRate, SERIAL_8N1, PIN_UART2_RX, PIN_UART2_TX);
    g_uartInput.begin(kSerial2BaudRate);

    Serial.println("Cheddar bring-up");
    Serial.println("USB Serial (UART0) ready for monitoring");
    Serial.println("UART2 (GPIO16/17) ready for Pi communication");

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
