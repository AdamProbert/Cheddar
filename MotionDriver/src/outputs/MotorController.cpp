#include "MotorController.h"

namespace outputs
{

    namespace
    {
        constexpr int kMotorIn1Pins[MotorController::kMotorCount] = {
            PIN_M1_IN1, PIN_M2_IN1, PIN_M3_IN1,
            PIN_M4_IN1, PIN_M5_IN1, PIN_M6_IN1};

        constexpr int kMotorIn2Pins[MotorController::kMotorCount] = {
            PIN_M1_IN2, PIN_M2_IN2, PIN_M3_IN2,
            PIN_M4_IN2, PIN_M5_IN2, PIN_M6_IN2};
    }

    MotorController::MotorController(int standbyPin)
        : m_standbyPin(standbyPin),
          m_initialized(false),
          m_driverEnabled(false)
    {
        for (uint8_t index = 0; index < kMotorCount; ++index)
        {
            auto &motor = m_motors[index];
            motor.in1Pin = kMotorIn1Pins[index];
            motor.in2Pin = kMotorIn2Pins[index];
            motor.channelA = index * kChannelsPerMotor;
            motor.channelB = motor.channelA + 1;
            motor.direction = Direction::Forward;
            motor.targetSpeed = 0.0f;
            motor.outputEnabled = false;
        }
    }

    bool MotorController::begin()
    {
        pinMode(m_standbyPin, OUTPUT);
        digitalWrite(m_standbyPin, LOW);

        for (uint8_t index = 0; index < kMotorCount; ++index)
        {
            auto &motor = m_motors[index];

            pinMode(motor.in1Pin, OUTPUT);
            pinMode(motor.in2Pin, OUTPUT);
            digitalWrite(motor.in1Pin, LOW);
            digitalWrite(motor.in2Pin, LOW);

            ledcSetup(motor.channelA, kPwmFrequencyHz, kPwmResolutionBits);
            ledcSetup(motor.channelB, kPwmFrequencyHz, kPwmResolutionBits);

            ledcAttachPin(motor.in1Pin, motor.channelA);
            ledcAttachPin(motor.in2Pin, motor.channelB);

            ledcWrite(motor.channelA, 0);
            ledcWrite(motor.channelB, 0);
        }

        m_initialized = true;
        m_driverEnabled = false;

        return true;
    }

    void MotorController::run(uint8_t motorIndex, Direction direction, float speed, bool autoEnable)
    {
        if (!m_initialized || !validIndex(motorIndex))
        {
            return;
        }

        auto &motor = m_motors[motorIndex];
        motor.direction = direction;
        motor.targetSpeed = clampSpeed(speed);

        if (motor.targetSpeed == 0.0f)
        {
            motor.outputEnabled = false;
        }
        else if (autoEnable)
        {
            motor.outputEnabled = true;
        }

        applyOutput(motorIndex);
        updateStandby();
    }

    void MotorController::runAll(Direction direction, float speed, bool autoEnable)
    {
        if (!m_initialized)
        {
            return;
        }

        const float clamped = clampSpeed(speed);

        for (uint8_t index = 0; index < kMotorCount; ++index)
        {
            auto &motor = m_motors[index];
            motor.direction = direction;
            motor.targetSpeed = clamped;
            if (motor.targetSpeed == 0.0f)
            {
                motor.outputEnabled = false;
            }
            else if (autoEnable)
            {
                motor.outputEnabled = true;
            }
            applyOutput(index);
        }

        updateStandby();
    }

    void MotorController::start(uint8_t motorIndex)
    {
        if (!m_initialized || !validIndex(motorIndex))
        {
            return;
        }

        auto &motor = m_motors[motorIndex];
        motor.outputEnabled = motor.targetSpeed > 0.0f;
        applyOutput(motorIndex);
        updateStandby();
    }

    void MotorController::startAll()
    {
        if (!m_initialized)
        {
            return;
        }

        for (uint8_t index = 0; index < kMotorCount; ++index)
        {
            auto &motor = m_motors[index];
            motor.outputEnabled = motor.targetSpeed > 0.0f;
            applyOutput(index);
        }

        updateStandby();
    }

    void MotorController::stop(uint8_t motorIndex)
    {
        if (!m_initialized || !validIndex(motorIndex))
        {
            return;
        }

        auto &motor = m_motors[motorIndex];
        motor.outputEnabled = false;
        applyOutput(motorIndex);
        updateStandby();
    }

    void MotorController::stopAll()
    {
        if (!m_initialized)
        {
            return;
        }

        for (uint8_t index = 0; index < kMotorCount; ++index)
        {
            m_motors[index].outputEnabled = false;
            applyOutput(index);
        }

        updateStandby();
    }

    MotorController::Direction MotorController::direction(uint8_t motorIndex) const
    {
        if (!validIndex(motorIndex))
        {
            return Direction::Forward;
        }
        return m_motors[motorIndex].direction;
    }

    float MotorController::targetSpeed(uint8_t motorIndex) const
    {
        if (!validIndex(motorIndex))
        {
            return 0.0f;
        }
        return m_motors[motorIndex].targetSpeed;
    }

    bool MotorController::motorEnabled(uint8_t motorIndex) const
    {
        if (!validIndex(motorIndex))
        {
            return false;
        }
        return m_motors[motorIndex].outputEnabled;
    }

    bool MotorController::validIndex(uint8_t motorIndex) const
    {
        return motorIndex < kMotorCount;
    }

    float MotorController::clampSpeed(float speed) const
    {
        if (speed < 0.0f)
        {
            return 0.0f;
        }
        if (speed > 1.0f)
        {
            return 1.0f;
        }
        return speed;
    }

    void MotorController::applyOutput(uint8_t motorIndex)
    {
        if (!validIndex(motorIndex))
        {
            return;
        }

        const auto &motor = m_motors[motorIndex];
        const uint32_t maxDuty = (1u << kPwmResolutionBits) - 1u;
        const uint32_t duty = static_cast<uint32_t>(motor.targetSpeed * static_cast<float>(maxDuty) + 0.5f);

        if (!motor.outputEnabled || duty == 0)
        {
            ledcWrite(motor.channelA, 0);
            ledcWrite(motor.channelB, 0);
            return;
        }

        if (motor.direction == Direction::Forward)
        {
            ledcWrite(motor.channelA, duty);
            ledcWrite(motor.channelB, 0);
        }
        else
        {
            ledcWrite(motor.channelA, 0);
            ledcWrite(motor.channelB, duty);
        }
    }

    void MotorController::updateStandby()
    {
        bool anyActive = false;
        for (uint8_t index = 0; index < kMotorCount; ++index)
        {
            const auto &motor = m_motors[index];
            if (motor.outputEnabled && motor.targetSpeed > 0.0f)
            {
                anyActive = true;
                break;
            }
        }

        if (anyActive)
        {
            if (!m_driverEnabled)
            {
                digitalWrite(m_standbyPin, HIGH);
                m_driverEnabled = true;
            }
        }
        else
        {
            if (m_driverEnabled)
            {
                digitalWrite(m_standbyPin, LOW);
                m_driverEnabled = false;
            }
        }
    }

    void MotorController::disableOutputs()
    {
        for (uint8_t index = 0; index < kMotorCount; ++index)
        {
            const auto &motor = m_motors[index];
            ledcWrite(motor.channelA, 0);
            ledcWrite(motor.channelB, 0);
        }

        digitalWrite(m_standbyPin, LOW);
        m_driverEnabled = false;
    }
} // namespace outputs
