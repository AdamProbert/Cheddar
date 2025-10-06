#include "ServoController.h"

#include <algorithm>

namespace outputs
{

    namespace
    {
        constexpr size_t kMotorPinCount = 12;
        const int kMotorPins[kMotorPinCount] = {
            PIN_M1_IN1, PIN_M1_IN2, PIN_M2_IN1, PIN_M2_IN2,
            PIN_M3_IN1, PIN_M3_IN2, PIN_M4_IN1, PIN_M4_IN2,
            PIN_M5_IN1, PIN_M5_IN2, PIN_M6_IN1, PIN_M6_IN2};
    }

    ServoController::ServoController()
        : m_driver(kPCA9685Address),
          m_initialized(false),
          m_outputsEnabled(false),
          m_lastUpdateMs(0),
          m_currentPulseUs(m_sweepConfig.minPulseUs + (m_sweepConfig.maxPulseUs - m_sweepConfig.minPulseUs) / 2),
          m_stepDirection(1),
          m_logDecimator(0)
    {
    }

    bool ServoController::begin(TwoWire &wire)
    {
        initializeMotorOutputs();

        pinMode(PIN_PCA9685_OE, OUTPUT);
        setOutputsEnabled(false);

        wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);
        m_driver.begin();

        wire.beginTransmission(kPCA9685Address);
        const uint8_t i2cError = wire.endTransmission();
        if (i2cError != 0)
        {
            Serial.printf("PCA9685 init failed (I2C error %u).\n", i2cError);
            return false;
        }

        m_driver.setOscillatorFrequency(kOscillatorFrequencyHz);
        m_driver.setPWMFreq(kDefaultFrequencyHz);
        delay(10);

        m_initialized = true;
        m_lastUpdateMs = millis();
        m_sweepConfig.enabled = false;
        m_currentPulseUs = clampPulse(m_currentPulseUs, m_sweepConfig.minPulseUs, m_sweepConfig.maxPulseUs);
        writeMicroseconds(m_sweepConfig.channel, static_cast<uint16_t>(m_currentPulseUs));
        setOutputsEnabled(true);

        return true;
    }

    void ServoController::update(uint32_t nowMs)
    {
        if (!m_initialized || !m_sweepConfig.enabled)
        {
            return;
        }

        if (nowMs - m_lastUpdateMs < m_sweepConfig.intervalMs)
        {
            return;
        }

        m_lastUpdateMs = nowMs;
        m_currentPulseUs += m_stepDirection * static_cast<int32_t>(m_sweepConfig.stepUs);

        if (m_currentPulseUs >= m_sweepConfig.maxPulseUs || m_currentPulseUs <= m_sweepConfig.minPulseUs)
        {
            m_currentPulseUs = clampPulse(static_cast<uint16_t>(m_currentPulseUs), m_sweepConfig.minPulseUs, m_sweepConfig.maxPulseUs);
            m_stepDirection = -m_stepDirection;
        }

        writeMicroseconds(m_sweepConfig.channel, static_cast<uint16_t>(m_currentPulseUs));

        if (m_sweepConfig.logTelemetry)
        {
            if (++m_logDecimator >= 5)
            {
                m_logDecimator = 0;
                Serial.printf("Servo pulse: %ld us\n", m_currentPulseUs);
            }
        }
    }

    void ServoController::setTargetMicroseconds(uint8_t channel, uint16_t pulseUs)
    {
        if (!m_initialized)
        {
            return;
        }

        m_sweepConfig.channel = channel;
        m_sweepConfig.enabled = false;

        const uint16_t clamped = clampPulse(pulseUs, m_sweepConfig.minPulseUs, m_sweepConfig.maxPulseUs);
        m_currentPulseUs = clamped;
        writeMicroseconds(channel, clamped);
    }

    void ServoController::enableSweep(bool enabled)
    {
        m_sweepConfig.enabled = enabled;
        if (enabled)
        {
            m_lastUpdateMs = 0;
        }
    }

    void ServoController::configureSweepChannel(uint8_t channel)
    {
        m_sweepConfig.channel = channel;
    }

    void ServoController::configureSweepRange(uint16_t minPulseUs, uint16_t maxPulseUs)
    {
        m_sweepConfig.minPulseUs = minPulseUs;
        m_sweepConfig.maxPulseUs = maxPulseUs;
        if (m_currentPulseUs < minPulseUs || m_currentPulseUs > maxPulseUs)
        {
            m_currentPulseUs = clampPulse(static_cast<uint16_t>(m_currentPulseUs), minPulseUs, maxPulseUs);
        }
    }

    void ServoController::configureSweepStep(uint16_t stepUs, uint32_t intervalMs)
    {
        m_sweepConfig.stepUs = stepUs;
        m_sweepConfig.intervalMs = intervalMs;
    }

    void ServoController::enableTelemetry(bool enabled)
    {
        m_sweepConfig.logTelemetry = enabled;
    }

    void ServoController::setOutputsEnabled(bool enabled)
    {
        digitalWrite(PIN_PCA9685_OE, enabled ? LOW : HIGH);
        m_outputsEnabled = enabled;
    }

    void ServoController::initializeMotorOutputs()
    {
        pinMode(PIN_DRV_STBY, OUTPUT);
        digitalWrite(PIN_DRV_STBY, LOW);

        for (size_t index = 0; index < kMotorPinCount; ++index)
        {
            pinMode(kMotorPins[index], OUTPUT);
            digitalWrite(kMotorPins[index], LOW);
        }
    }

    void ServoController::writeMicroseconds(uint8_t channel, uint16_t pulseUs)
    {
        const uint16_t ticks = pulseToTicks(clampPulse(pulseUs, m_sweepConfig.minPulseUs, m_sweepConfig.maxPulseUs));
        m_driver.setPWM(channel, 0, ticks);
    }

    uint16_t ServoController::clampPulse(uint16_t pulseUs, uint16_t minUs, uint16_t maxUs)
    {
        if (pulseUs < minUs)
        {
            return minUs;
        }
        if (pulseUs > maxUs)
        {
            return maxUs;
        }
        return pulseUs;
    }

    uint16_t ServoController::pulseToTicks(uint16_t pulseUs)
    {
        const uint32_t ticks = (static_cast<uint32_t>(pulseUs) * kPWMResolution + (kServoPeriodUs / 2)) / kServoPeriodUs;
        return static_cast<uint16_t>(std::min<uint32_t>(ticks, kPWMResolution - 1));
    }

} // namespace outputs
