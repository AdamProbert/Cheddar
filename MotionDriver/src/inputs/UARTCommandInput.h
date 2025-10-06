#pragma once

#include <Arduino.h>

#include "outputs/ServoController.h"

namespace inputs
{

    class UARTCommandInput
    {
    public:
        UARTCommandInput(HardwareSerial &serial, outputs::ServoController &servoController);

        void begin(unsigned long baudRate);
        void poll();

    private:
        void resetBuffer();
        void handleLine();
        void handleServoCommand(char *channelToken, char *pulseToken);
        void handleSweepCommand(char *stateToken, char *rangeToken);
        void handleTelemetryCommand(char *stateToken);
        void handleHelpCommand();
        bool parseSweepRangeToken(char *token, uint8_t &startChannel, uint8_t &endChannel, bool &isAllRequest);
        void reportError(const char *message);

        static constexpr size_t kBufferSize = 64;

        HardwareSerial &m_serial;
        outputs::ServoController &m_servoController;
        char m_buffer[kBufferSize];
        size_t m_bufferLength;
    };

} // namespace inputs
