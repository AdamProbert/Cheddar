#pragma once

#include <Arduino.h>

#include "pins.h"

namespace outputs
{

    class MotorController
    {
    public:
        enum class Direction : int8_t
        {
            Forward = 1,
            Backward = -1
        };

        MotorController(int in1Pin = PIN_M1_IN1, int in2Pin = PIN_M1_IN2, int standbyPin = PIN_DRV_STBY);

        bool begin();

        void run(Direction direction, float speed, bool autoEnable = true);
        void start();
        void stop();

        Direction direction() const { return m_direction; }
        float targetSpeed() const { return m_targetSpeed; }
        bool enabled() const { return m_enabled; }
        bool initialized() const { return m_initialized; }

    private:
        static constexpr uint8_t kPwmChannelA = 0;
        static constexpr uint8_t kPwmChannelB = 1;
        static constexpr uint32_t kPwmFrequencyHz = 12000;
        static constexpr uint8_t kPwmResolutionBits = 8;

        float clampSpeed(float speed) const;
        void applyOutput();
        void disableOutputs();

        int m_in1Pin;
        int m_in2Pin;
        int m_standbyPin;
        Direction m_direction;
        float m_targetSpeed;
        bool m_initialized;
        bool m_enabled;
    };

} // namespace outputs
