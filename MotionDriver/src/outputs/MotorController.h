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

        // Slews each motor toward its commanded speed. Must be called from the main
        // loop; without it, motors never reach their target.
        void update(uint32_t nowMs);

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
            // Signed so a forward<->reverse change ramps down through zero and back up
            // rather than snapping across. Sign picks the direction, magnitude the duty.
            float currentSignedSpeed;
        };

        static constexpr uint8_t kChannelsPerMotor = 2;
        static constexpr uint32_t kPwmFrequencyHz = 12000;
        static constexpr uint8_t kPwmResolutionBits = 8;

        // Slew rate, in speed units per second: 3.0 takes ~330ms from rest to full and
        // ~670ms for a full reversal. Tuned to take the edge off without feeling laggy.
        // Easing the current ramp also softens the inrush that sags the rail -- see the
        // brownout notes in HARDWARE.md.
        static constexpr float kSpeedRampPerSecond = 3.0f;
        // Ceiling on the timestep, so a stalled loop resumes by ramping rather than
        // stepping a large jump in one go.
        static constexpr uint32_t kMaxRampStepMs = 50;

        // Duty below which the wheels do not turn at all -- the rover just sits and
        // buzzes. Measured on hardware 2026-07-16. A non-zero speed maps into
        // [kMinMovingDuty, 1.0] so the ramp spends its time where the wheels actually
        // move, instead of crawling through dead duty and then lurching.
        //
        // This is calibrated to the *current* 8.4V unbucked motor rail. It is a fraction
        // of whatever the rail happens to be, so it MUST be re-measured if that rail
        // changes -- notably if the ~6V motor buck in HARDWARE.md ever lands.
        static constexpr float kMinMovingDuty = 0.80f;

        bool validIndex(uint8_t motorIndex) const;
        float clampSpeed(float speed) const;
        float effectiveSignedTarget(uint8_t motorIndex) const;
        void applyOutput(uint8_t motorIndex);
        void updateStandby();
        void disableOutputs();

        int m_standbyPin;
        bool m_initialized;
        bool m_driverEnabled;
        uint32_t m_lastUpdateMs;
        MotorState m_motors[kMotorCount];
    };

} // namespace outputs
