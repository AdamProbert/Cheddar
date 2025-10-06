#include "UARTCommandInput.h"

#include <cstring>
#include <cstdlib>
#include <strings.h>

namespace inputs
{

    UARTCommandInput::UARTCommandInput(HardwareSerial &serial, outputs::ServoController &servoController, outputs::MotorController &motorController)
        : m_serial(serial),
          m_servoController(servoController),
          m_motorController(motorController),
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
            char *rangeToken = strtok_r(nullptr, " \t", &savePtr);
            char *extraToken = strtok_r(nullptr, " \t", &savePtr);
            if (extraToken != nullptr)
            {
                reportError("SWEEP extra args");
                return;
            }
            handleSweepCommand(stateToken, rangeToken);
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

        if (strcasecmp(token, "MOTOR") == 0)
        {
            char *modeToken = strtok_r(nullptr, " \t", &savePtr);
            char *valueToken = strtok_r(nullptr, " \t", &savePtr);
            char *extraToken = strtok_r(nullptr, " \t", &savePtr);
            if (modeToken == nullptr)
            {
                reportError("MOTOR cmd syntax");
                return;
            }
            handleMotorCommand(modeToken, valueToken, extraToken);
            return;
        }

        if (strcasecmp(token, "HELP") == 0 || strcmp(token, "?") == 0)
        {
            handleHelpCommand();
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

    void UARTCommandInput::handleSweepCommand(char *stateToken, char *rangeToken)
    {
        if (stateToken == nullptr)
        {
            reportError("SWEEP arg");
            return;
        }

        bool enable = false;
        if (strcasecmp(stateToken, "ON") == 0)
        {
            enable = true;
        }
        else if (strcasecmp(stateToken, "OFF") == 0)
        {
            enable = false;
        }
        else
        {
            reportError("SWEEP arg");
            return;
        }

        if (rangeToken == nullptr)
        {
            m_servoController.enableSweep(enable);
            m_serial.println("OK");
            return;
        }

        uint8_t startChannel = 0;
        uint8_t endChannel = 0;
        bool isAll = false;
        if (!parseSweepRangeToken(rangeToken, startChannel, endChannel, isAll))
        {
            reportError("SWEEP range");
            return;
        }

        if (isAll)
        {
            m_servoController.setSweepEnabledAll(enable);
        }
        else
        {
            m_servoController.setSweepEnabledRange(startChannel, endChannel, enable);
        }

        m_serial.println("OK");
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

    void UARTCommandInput::handleMotorCommand(char *modeToken, char *valueToken, char *extraToken)
    {
        if (modeToken == nullptr)
        {
            reportError("MOTOR arg");
            return;
        }

        if (strcasecmp(modeToken, "STOP") == 0)
        {
            if (valueToken != nullptr || extraToken != nullptr)
            {
                reportError("MOTOR STOP args");
                return;
            }
            m_motorController.stop();
            m_serial.println("OK");
            return;
        }

        if (strcasecmp(modeToken, "START") == 0)
        {
            if (valueToken != nullptr || extraToken != nullptr)
            {
                reportError("MOTOR START args");
                return;
            }
            m_motorController.start();
            m_serial.println("OK");
            return;
        }

        outputs::MotorController::Direction direction;
        if (strcasecmp(modeToken, "FORWARD") == 0)
        {
            direction = outputs::MotorController::Direction::Forward;
        }
        else if (strcasecmp(modeToken, "BACKWARD") == 0)
        {
            direction = outputs::MotorController::Direction::Backward;
        }
        else
        {
            reportError("MOTOR arg");
            return;
        }

        if (extraToken != nullptr)
        {
            reportError("MOTOR extra args");
            return;
        }

        float speed = 1.0f;
        if (valueToken != nullptr)
        {
            char *endPtr = nullptr;
            const float parsed = strtof(valueToken, &endPtr);
            if (endPtr == nullptr || *endPtr != '\0')
            {
                reportError("MOTOR speed");
                return;
            }
            if (parsed < 0.0f || parsed > 1.0f)
            {
                reportError("MOTOR speed");
                return;
            }
            speed = parsed;
        }

        m_motorController.run(direction, speed, true);
        m_serial.println("OK");
    }

    void UARTCommandInput::handleHelpCommand()
    {
        m_serial.println(F("NAME"));
        m_serial.println(F("    cheddar-cli - MotionDriver serial command interface"));
        m_serial.println();

        m_serial.println(F("SYNOPSIS"));
        m_serial.println(F("    PING"));
        m_serial.println(F("    S <channel> <microseconds>"));
        m_serial.println(F("    SWEEP ON|OFF [channel|start-end|ALL]"));
        m_serial.println(F("    MOTOR FORWARD|BACKWARD [speed]"));
        m_serial.println(F("    MOTOR STOP"));
        m_serial.println(F("    MOTOR START"));
        m_serial.println(F("    LOG ON|OFF"));
        m_serial.println(F("    HELP"));
        m_serial.println();

        m_serial.println(F("DESCRIPTION"));
        m_serial.println(F("    Commands control servos and telemetry via UART."));
        m_serial.println();

        m_serial.println(F("COMMANDS"));
        m_serial.println(F("    PING"));
        m_serial.println(F("        Responds with 'PONG' to verify connectivity."));
        m_serial.println();

        m_serial.println(F("    S <channel> <microseconds>"));
        m_serial.println(F("        Sets servo <channel> (0-5) to the specified pulse width."));
        m_serial.println();

        m_serial.println(F("    SWEEP ON [channel|start-end|ALL]"));
        m_serial.println(F("        Enables sweep on a single channel, a range, or all servos."));
        m_serial.println(F("    SWEEP OFF [channel|start-end|ALL]"));
        m_serial.println(F("        Disables sweep on the selected channel(s)."));
        m_serial.println();

        m_serial.println(F("    MOTOR FORWARD|BACKWARD [speed]"));
        m_serial.println(F("        Drives the DC motor via DRV8833 in the selected direction."));
        m_serial.println(F("        Optional speed is 0.0-1.0 (default 1.0)."));
        m_serial.println();

        m_serial.println(F("    MOTOR STOP"));
        m_serial.println(F("        Disables the driver (STBY low) and coasts the motor."));
        m_serial.println();

        m_serial.println(F("    MOTOR START"));
        m_serial.println(F("        Re-enables the driver and resumes the last direction/speed."));
        m_serial.println();

        m_serial.println(F("    LOG ON|OFF"));
        m_serial.println(F("        Enables or disables periodic sweep telemetry output."));
        m_serial.println();

        m_serial.println(F("    HELP"));
        m_serial.println(F("        Displays this command reference."));
        m_serial.println();

        m_serial.println(F("EXAMPLES"));
        m_serial.println(F("    SWEEP ON 0-5"));
        m_serial.println(F("    SWEEP OFF [ALL]"));
        m_serial.println(F("    S 2 1500"));
        m_serial.println();

        m_serial.println(F("NOTES"));
        m_serial.println(F("    • Channel indices beyond 0-5 are rejected."));
        m_serial.println(F("    • Pulse widths are clamped to configured min/max per channel."));
        m_serial.println();

        m_serial.println(F("OK"));
    }

    bool UARTCommandInput::parseSweepRangeToken(char *token, uint8_t &startChannel, uint8_t &endChannel, bool &isAllRequest)
    {
        if (token == nullptr)
        {
            return false;
        }

        isAllRequest = false;

        if (strcasecmp(token, "ALL") == 0 || strcasecmp(token, "[ALL]") == 0)
        {
            startChannel = 0;
            endChannel = outputs::ServoController::kServoCount - 1;
            isAllRequest = true;
            return true;
        }

        char *dash = strchr(token, '-');
        if (dash != nullptr)
        {
            *dash = '\0';
            char *startToken = token;
            char *endToken = dash + 1;

            char *endPtr = nullptr;
            long startValue = strtol(startToken, &endPtr, 10);
            if (endPtr == nullptr || *endPtr != '\0')
            {
                return false;
            }

            endPtr = nullptr;
            long endValue = strtol(endToken, &endPtr, 10);
            if (endPtr == nullptr || *endPtr != '\0')
            {
                return false;
            }

            if (startValue < 0 || endValue < 0)
            {
                return false;
            }

            if (startValue > endValue)
            {
                long temp = startValue;
                startValue = endValue;
                endValue = temp;
            }

            if (endValue >= outputs::ServoController::kServoCount)
            {
                return false;
            }

            startChannel = static_cast<uint8_t>(startValue);
            endChannel = static_cast<uint8_t>(endValue);
            return true;
        }

        char *endPtr = nullptr;
        long channelValue = strtol(token, &endPtr, 10);
        if (endPtr == nullptr || *endPtr != '\0')
        {
            return false;
        }

        if (channelValue < 0 || channelValue >= outputs::ServoController::kServoCount)
        {
            return false;
        }

        startChannel = static_cast<uint8_t>(channelValue);
        endChannel = static_cast<uint8_t>(channelValue);
        return true;
    }

    void UARTCommandInput::reportError(const char *message)
    {
        m_serial.print("ERR ");
        m_serial.println(message);
    }

} // namespace inputs
