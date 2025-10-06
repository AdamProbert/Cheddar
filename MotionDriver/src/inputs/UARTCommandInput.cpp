#include "UARTCommandInput.h"

#include <cstring>
#include <cstdlib>
#include <strings.h>

namespace inputs
{

    UARTCommandInput::UARTCommandInput(HardwareSerial &serial, outputs::ServoController &servoController)
        : m_serial(serial),
          m_servoController(servoController),
          m_buffer{0},
          m_bufferLength(0)
    {
    }

    void UARTCommandInput::begin(unsigned long baudRate)
    {
        m_serial.begin(baudRate);
        resetBuffer();
    }

    void UARTCommandInput::poll()
    {
        while (m_serial.available())
        {
            const char incoming = static_cast<char>(m_serial.read());

            if (incoming == '\r')
            {
                continue;
            }

            if (incoming == '\n')
            {
                if (m_bufferLength > 0)
                {
                    m_buffer[m_bufferLength] = '\0';
                    handleLine();
                }
                resetBuffer();
                continue;
            }

            if (m_bufferLength >= kBufferSize - 1)
            {
                reportError("Line too long");
                resetBuffer();
                continue;
            }

            m_buffer[m_bufferLength++] = incoming;
        }
    }

    void UARTCommandInput::resetBuffer()
    {
        memset(m_buffer, 0, sizeof(m_buffer));
        m_bufferLength = 0;
    }

    void UARTCommandInput::handleLine()
    {
        char *savePtr = nullptr;
        char *token = strtok_r(m_buffer, " \t", &savePtr);
        if (token == nullptr)
        {
            return;
        }

        if (strcasecmp(token, "PING") == 0)
        {
            m_serial.println("PONG");
            return;
        }

        if (strcasecmp(token, "S") == 0)
        {
            char *channelToken = strtok_r(nullptr, " \t", &savePtr);
            char *pulseToken = strtok_r(nullptr, " \t", &savePtr);
            if (channelToken == nullptr || pulseToken == nullptr)
            {
                reportError("S cmd syntax");
                return;
            }
            handleServoCommand(channelToken, pulseToken);
            return;
        }

        if (strcasecmp(token, "SWEEP") == 0)
        {
            char *stateToken = strtok_r(nullptr, " \t", &savePtr);
            if (stateToken == nullptr)
            {
                reportError("SWEEP cmd syntax");
                return;
            }
            handleSweepCommand(stateToken);
            return;
        }

        if (strcasecmp(token, "LOG") == 0)
        {
            char *stateToken = strtok_r(nullptr, " \t", &savePtr);
            if (stateToken == nullptr)
            {
                reportError("LOG cmd syntax");
                return;
            }
            handleTelemetryCommand(stateToken);
            return;
        }

        reportError("Unknown command");
    }

    void UARTCommandInput::handleServoCommand(char *channelToken, char *pulseToken)
    {
        char *endChannel = nullptr;
        long channel = strtol(channelToken, &endChannel, 10);
        if (endChannel == nullptr || *endChannel != '\0' || channel < 0 || channel > 15)
        {
            reportError("Servo channel");
            return;
        }

        char *endPulse = nullptr;
        long pulse = strtol(pulseToken, &endPulse, 10);
        if (endPulse == nullptr || *endPulse != '\0')
        {
            reportError("Servo pulse");
            return;
        }

        m_servoController.setTargetMicroseconds(static_cast<uint8_t>(channel), static_cast<uint16_t>(pulse));
        m_serial.println("OK");
    }

    void UARTCommandInput::handleSweepCommand(char *stateToken)
    {
        if (strcasecmp(stateToken, "ON") == 0)
        {
            m_servoController.enableSweep(true);
            m_serial.println("OK");
            return;
        }

        if (strcasecmp(stateToken, "OFF") == 0)
        {
            m_servoController.enableSweep(false);
            m_serial.println("OK");
            return;
        }

        reportError("SWEEP arg");
    }

    void UARTCommandInput::handleTelemetryCommand(char *stateToken)
    {
        if (strcasecmp(stateToken, "ON") == 0)
        {
            m_servoController.enableTelemetry(true);
            m_serial.println("OK");
            return;
        }

        if (strcasecmp(stateToken, "OFF") == 0)
        {
            m_servoController.enableTelemetry(false);
            m_serial.println("OK");
            return;
        }

        reportError("LOG arg");
    }

    void UARTCommandInput::reportError(const char *message)
    {
        m_serial.print("ERR ");
        m_serial.println(message);
    }

} // namespace inputs
