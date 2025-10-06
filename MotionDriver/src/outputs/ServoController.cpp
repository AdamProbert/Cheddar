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
          m_logTelemetry(true),
          m_defaultSweepChannel(0)
    {
        for (uint8_t channel = 0; channel < kServoCount; ++channel)
        {
            auto &state = m_sweepStates[channel];
            state.enabled = false;
            state.channel = channel;
            state.minPulseUs = kDefaultMinPulseUs;
            state.maxPulseUs = kDefaultMaxPulseUs;
            state.stepUs = 10;
            state.intervalMs = 50;
            state.lastUpdateMs = 0;
            state.currentPulseUs = (kDefaultMinPulseUs + kDefaultMaxPulseUs) / 2;
            state.direction = 1;
            state.logDecimator = 0;
        }
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
        m_defaultSweepChannel = 0;

        const uint32_t nowMs = millis();

        for (uint8_t channel = 0; channel < kServoCount; ++channel)
        {
            auto &state = m_sweepStates[channel];
            state.enabled = false;
            state.channel = channel;
            state.lastUpdateMs = nowMs;
            const uint16_t clamped = clampPulse(channel, state.currentPulseUs);
            writeMicroseconds(channel, clamped);
        }

        setOutputsEnabled(true);

        return true;
    }

    void ServoController::update(uint32_t nowMs)
    {
        if (!m_initialized)
        {
            return;
        }

        for (uint8_t channel = 0; channel < kServoCount; ++channel)
        {
            auto &state = m_sweepStates[channel];
            if (!state.enabled)
            {
                continue;
            }

            if ((nowMs - state.lastUpdateMs) < state.intervalMs)
            {
                continue;
            }

            state.lastUpdateMs = nowMs;
            state.currentPulseUs += state.direction * static_cast<int32_t>(state.stepUs);

            if (state.currentPulseUs >= state.maxPulseUs || state.currentPulseUs <= state.minPulseUs)
            {
                state.currentPulseUs = clampPulse(channel, state.currentPulseUs);
                state.direction = static_cast<int8_t>(-state.direction);
            }

            const uint16_t clamped = clampPulse(channel, state.currentPulseUs);
            writeMicroseconds(channel, clamped);

            if (m_logTelemetry)
            {
                if (++state.logDecimator >= 5)
                {
                    state.logDecimator = 0;
                    Serial.printf("Servo %u pulse: %ld us\n", channel, static_cast<long>(state.currentPulseUs));
                }
            }
        }
    }

    void ServoController::setTargetMicroseconds(uint8_t channel, uint16_t pulseUs)
    {
        if (!m_initialized || channel >= kServoCount)
        {
            return;
        }

        auto &state = m_sweepStates[channel];
        state.enabled = false;
        state.direction = 1;
        state.lastUpdateMs = 0;

        const uint16_t clamped = clampPulse(channel, static_cast<int32_t>(pulseUs));
        writeMicroseconds(channel, clamped);
    }

    void ServoController::enableSweep(bool enabled)
    {
        setSweepEnabled(m_defaultSweepChannel, enabled);
    }

    void ServoController::setSweepEnabled(uint8_t channel, bool enabled)
    {
        if (channel >= kServoCount)
        {
            return;
        }

        auto &state = m_sweepStates[channel];
        state.enabled = enabled;
        if (enabled)
        {
            state.lastUpdateMs = 0;
            state.direction = (state.direction >= 0) ? 1 : -1;
            const uint16_t clamped = clampPulse(channel, state.currentPulseUs);
            writeMicroseconds(channel, clamped);
        }
    }

    void ServoController::setSweepEnabledRange(uint8_t startChannel, uint8_t endChannel, bool enabled)
    {
        if (startChannel > endChannel)
        {
            const uint8_t temp = startChannel;
            startChannel = endChannel;
            endChannel = temp;
        }

        if (startChannel >= kServoCount)
        {
            return;
        }

        if (endChannel >= kServoCount)
        {
            endChannel = kServoCount - 1;
        }

        for (uint8_t channel = startChannel; channel <= endChannel; ++channel)
        {
            setSweepEnabled(channel, enabled);
        }
    }

    void ServoController::setSweepEnabledAll(bool enabled)
    {
        setSweepEnabledRange(0, kServoCount - 1, enabled);
    }

    void ServoController::configureSweepChannel(uint8_t channel)
    {
        if (channel >= kServoCount)
        {
            return;
        }

        m_defaultSweepChannel = channel;
    }

    void ServoController::configureSweepRange(uint16_t minPulseUs, uint16_t maxPulseUs)
    {
        if (m_defaultSweepChannel >= kServoCount)
        {
            return;
        }

        if (minPulseUs > maxPulseUs)
        {
            const uint16_t temp = minPulseUs;
            minPulseUs = maxPulseUs;
            maxPulseUs = temp;
        }

        auto &state = m_sweepStates[m_defaultSweepChannel];
        state.minPulseUs = minPulseUs;
        state.maxPulseUs = maxPulseUs;

        const uint16_t clamped = clampPulse(m_defaultSweepChannel, state.currentPulseUs);
        writeMicroseconds(m_defaultSweepChannel, clamped);
    }

    void ServoController::configureSweepStep(uint16_t stepUs, uint32_t intervalMs)
    {
        if (m_defaultSweepChannel >= kServoCount)
        {
            return;
        }

        auto &state = m_sweepStates[m_defaultSweepChannel];
        state.stepUs = stepUs;
        state.intervalMs = intervalMs;
    }

    void ServoController::enableTelemetry(bool enabled)
    {
        m_logTelemetry = enabled;
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
        if (channel >= kServoCount)
        {
            return;
        }

        const uint16_t clamped = clampPulse(channel, static_cast<int32_t>(pulseUs));
        const uint16_t ticks = pulseToTicks(clamped);
        m_driver.setPWM(channel, 0, ticks);
        m_sweepStates[channel].currentPulseUs = clamped;
    }

    uint16_t ServoController::clampPulse(uint8_t channel, int32_t pulseUs) const
    {
        const uint16_t minUs = (channel < kServoCount) ? m_sweepStates[channel].minPulseUs : kDefaultMinPulseUs;
        const uint16_t maxUs = (channel < kServoCount) ? m_sweepStates[channel].maxPulseUs : kDefaultMaxPulseUs;

        if (pulseUs < static_cast<int32_t>(minUs))
        {
            return minUs;
        }
        if (pulseUs > static_cast<int32_t>(maxUs))
        {
            return maxUs;
        }
        return static_cast<uint16_t>(pulseUs);
    }

    uint16_t ServoController::pulseToTicks(uint16_t pulseUs)
    {
        const uint32_t ticks = (static_cast<uint32_t>(pulseUs) * kPWMResolution + (kServoPeriodUs / 2)) / kServoPeriodUs;
        return static_cast<uint16_t>(std::min<uint32_t>(ticks, kPWMResolution - 1));
    }

} // namespace outputs
