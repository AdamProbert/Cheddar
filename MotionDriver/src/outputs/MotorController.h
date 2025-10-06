#pragma once

#include <Arduino.h>

#include "pins.h"

namespace outputs
{

    class MotorController
    {
    public:
        static constexpr uint8_t kMotorCount = 6;

        enum class Direction : int8_t
        {
            Forward = 1,
            Backward = -1
        };

        explicit MotorController(int standbyPin = PIN_DRV_STBY);

        bool begin();

        void run(uint8_t motorIndex, Direction direction, float speed, bool autoEnable = true);
        void runAll(Direction direction, float speed, bool autoEnable = true);
        void start(uint8_t motorIndex);
        void startAll();
        void stop(uint8_t motorIndex);
        void stopAll();

        Direction direction(uint8_t motorIndex) const;
        float targetSpeed(uint8_t motorIndex) const;
        bool motorEnabled(uint8_t motorIndex) const;
        bool driverEnabled() const { return m_driverEnabled; }
        bool initialized() const { return m_initialized; }

    private:
        struct MotorState
        {
            int in1Pin;
            int in2Pin;
            uint8_t channelA;
            uint8_t channelB;
            Direction direction;
            float targetSpeed;
            bool outputEnabled;
        };

        static constexpr uint8_t kChannelsPerMotor = 2;
        static constexpr uint32_t kPwmFrequencyHz = 12000;
        static constexpr uint8_t kPwmResolutionBits = 8;

        bool validIndex(uint8_t motorIndex) const;
        float clampSpeed(float speed) const;
        void applyOutput(uint8_t motorIndex);
        void updateStandby();
        void disableOutputs();

        int m_standbyPin;
        bool m_initialized;
        bool m_driverEnabled;
        MotorState m_motors[kMotorCount];
    };

} // namespace outputs
