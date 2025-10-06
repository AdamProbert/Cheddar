#include "MotorController.h"

namespace outputs
{

    MotorController::MotorController(int in1Pin, int in2Pin, int standbyPin)
        : m_in1Pin(in1Pin),
          m_in2Pin(in2Pin),
          m_standbyPin(standbyPin),
          m_direction(Direction::Forward),
          m_targetSpeed(0.0f),
          m_initialized(false),
          m_enabled(false)
    {
    }

    bool MotorController::begin()
    {
        pinMode(m_standbyPin, OUTPUT);
        digitalWrite(m_standbyPin, LOW);

        ledcSetup(kPwmChannelA, kPwmFrequencyHz, kPwmResolutionBits);
        ledcSetup(kPwmChannelB, kPwmFrequencyHz, kPwmResolutionBits);

        ledcAttachPin(m_in1Pin, kPwmChannelA);
        ledcAttachPin(m_in2Pin, kPwmChannelB);

        disableOutputs();

        m_initialized = true;
        m_enabled = false;
        m_direction = Direction::Forward;
        m_targetSpeed = 0.0f;
        return true;
    }

    void MotorController::run(Direction direction, float speed, bool autoEnable)
    {
        if (!m_initialized)
        {
            return;
        }

        m_direction = direction;
        m_targetSpeed = clampSpeed(speed);

        if (autoEnable && m_targetSpeed > 0.0f)
        {
            if (!m_enabled)
            {
                digitalWrite(m_standbyPin, HIGH);
                m_enabled = true;
            }
        }

        applyOutput();
    }

    void MotorController::start()
    {
        if (!m_initialized)
        {
            return;
        }

        if (!m_enabled)
        {
            digitalWrite(m_standbyPin, HIGH);
            m_enabled = true;
        }

        applyOutput();
    }

    void MotorController::stop()
    {
        if (!m_initialized)
        {
            return;
        }

        disableOutputs();
        digitalWrite(m_standbyPin, LOW);
        m_enabled = false;
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

    void MotorController::applyOutput()
    {
        const uint32_t maxDuty = (1u << kPwmResolutionBits) - 1u;
        const uint32_t duty = static_cast<uint32_t>(m_targetSpeed * static_cast<float>(maxDuty) + 0.5f);

        if (!m_enabled || duty == 0)
        {
            ledcWrite(kPwmChannelA, 0);
            ledcWrite(kPwmChannelB, 0);
            return;
        }

        if (m_direction == Direction::Forward)
        {
            ledcWrite(kPwmChannelA, duty);
            ledcWrite(kPwmChannelB, 0);
        }
        else
        {
            ledcWrite(kPwmChannelA, 0);
            ledcWrite(kPwmChannelB, duty);
        }
    }

    void MotorController::disableOutputs()
    {
        ledcWrite(kPwmChannelA, 0);
        ledcWrite(kPwmChannelB, 0);
    }

} // namespace outputs
