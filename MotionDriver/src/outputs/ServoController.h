#pragma once

#include <Adafruit_PWMServoDriver.h>
#include <Arduino.h>
#include <array>

#include "pins.h"

namespace outputs
{

    class ServoController
    {
    public:
        static constexpr uint8_t kServoCount = 6;
        static constexpr uint16_t kDefaultMinPulseUs = 1000;
        static constexpr uint16_t kDefaultMaxPulseUs = 2000;

        struct SweepConfig
        {
            bool enabled = false;
            uint8_t channel = 0;
            uint16_t minPulseUs = kDefaultMinPulseUs;
            uint16_t maxPulseUs = kDefaultMaxPulseUs;
            uint16_t stepUs = 10;
            uint32_t intervalMs = 50;
            uint32_t lastUpdateMs = 0;
            int32_t currentPulseUs = (kDefaultMinPulseUs + kDefaultMaxPulseUs) / 2;
            int8_t direction = 1;
            uint8_t logDecimator = 0;
        };

        ServoController();

        bool begin(TwoWire &wire);
        void update(uint32_t nowMs);

        void setTargetMicroseconds(uint8_t channel, uint16_t pulseUs);
        void enableSweep(bool enabled);
        void setSweepEnabled(uint8_t channel, bool enabled);
        void setSweepEnabledRange(uint8_t startChannel, uint8_t endChannel, bool enabled);
        void setSweepEnabledAll(bool enabled);
        void configureSweepChannel(uint8_t channel);
        void configureSweepRange(uint16_t minPulseUs, uint16_t maxPulseUs);
        void configureSweepStep(uint16_t stepUs, uint32_t intervalMs);
        void enableTelemetry(bool enabled);
        void setOutputsEnabled(bool enabled);
        bool outputsEnabled() const { return m_outputsEnabled; }

    private:
        static constexpr uint8_t kPCA9685Address = 0x40;
        static constexpr uint16_t kPWMResolution = 4096;
        static constexpr uint16_t kServoPeriodUs = 20000;
        static constexpr uint32_t kOscillatorFrequencyHz = 27000000UL;
        static constexpr uint16_t kDefaultFrequencyHz = 50;

        void initializeMotorOutputs();
        void writeMicroseconds(uint8_t channel, uint16_t pulseUs);
        uint16_t clampPulse(uint8_t channel, int32_t pulseUs) const;
        static uint16_t pulseToTicks(uint16_t pulseUs);

        Adafruit_PWMServoDriver m_driver;
        std::array<SweepConfig, kServoCount> m_sweepStates;
        bool m_initialized;
        bool m_outputsEnabled;
        bool m_logTelemetry;
        uint8_t m_defaultSweepChannel;
    };

} // namespace outputs
