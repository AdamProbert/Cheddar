#pragma once

#include <Arduino.h>

#include "outputs/ServoController.h"
#include "outputs/MotorController.h"

namespace inputs
{

    class UARTCommandInput
    {
    public:
        UARTCommandInput(HardwareSerial &serial, outputs::ServoController &servoController, outputs::MotorController &motorController);

        void begin(unsigned long baudRate);
        void poll();

        // Deadman failsafe: call every loop with the current millis(). If no
        // command has arrived within the deadman window, all motors are stopped
        // (servos are left holding their position).
        void update(unsigned long nowMillis);

    private:
        void resetBuffer();
        void handleLine();
        void handleServoCommand(char *channelToken, char *pulseToken);
        void handleSweepCommand(char *stateToken, char *rangeToken);
        void handleTelemetryCommand(char *stateToken);
        void handleMotorCommand(char *targetToken, char *modeToken, char *valueToken, char *extraToken);
        void handleHelpCommand();
        bool parseSweepRangeToken(char *token, uint8_t &startChannel, uint8_t &endChannel, bool &isAllRequest);
        bool parseMotorTargetToken(char *token, uint8_t &motorIndex, bool &isAllRequest);
        void reportError(const char *message);

        static constexpr size_t kBufferSize = 64;
        static constexpr unsigned long kDeadmanTimeoutMs = 1000;

        HardwareSerial &m_serial;
        outputs::ServoController &m_servoController;
        outputs::MotorController &m_motorController;
        char m_buffer[kBufferSize];
        size_t m_bufferLength;
        unsigned long m_lastCommandMillis;
        bool m_hasReceivedCommand;
        bool m_failsafeActive;
    };

} // namespace inputs
