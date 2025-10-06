#pragma once

#include <Adafruit_PWMServoDriver.h>
#include <Arduino.h>

#include "pins.h"

namespace outputs
{

    class ServoController
    {
    public:
        struct SweepConfig
        {
            uint8_t channel = 0;
            uint16_t minPulseUs = 1000;
            uint16_t maxPulseUs = 2000;
            uint16_t stepUs = 10;
            uint32_t intervalMs = 50;
            bool enabled = false;
            bool logTelemetry = true;
        };

        ServoController();

        bool begin(TwoWire &wire);
        void update(uint32_t nowMs);

        void setTargetMicroseconds(uint8_t channel, uint16_t pulseUs);
        void enableSweep(bool enabled);
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
        static uint16_t clampPulse(uint16_t pulseUs, uint16_t minUs, uint16_t maxUs);
        static uint16_t pulseToTicks(uint16_t pulseUs);

        Adafruit_PWMServoDriver m_driver;
        SweepConfig m_sweepConfig;
        bool m_initialized;
        bool m_outputsEnabled;
        uint32_t m_lastUpdateMs;
        int32_t m_currentPulseUs;
        int8_t m_stepDirection;
        uint8_t m_logDecimator;
    };

} // namespace outputs
