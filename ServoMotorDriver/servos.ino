// --------- Servo control (PCA9685) ---------
#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

#define SERVO_COUNT 6  // use PCA9685 channels 0..5

// Convert microseconds to PCA9685 ticks (0..4095)
static uint16_t usToTicks(uint16_t us) {
  // ticks = us * freq * 4096 / 1e6
  float ticks = (float)us * SERVO_FREQ * 4096.0f / 1000000.0f;
  if (ticks < 0)    ticks = 0;
  if (ticks > 4095) ticks = 4095;
  return (uint16_t)ticks;
}

static void writeServoUS(uint8_t ch, uint16_t us) {
  pwm.setPWM(ch, 0, usToTicks(us));
}

// NEW: write any servo (by index 0..5) using 0..1 fraction with easing
void writeServoFrac(uint8_t idx, float f01) {
  if (idx >= SERVO_COUNT) return;
  if (f01 < 0) f01 = 0;
  if (f01 > 1) f01 = 1;
  float eased = 0.5f - 0.5f * cosf(f01 * 3.14159265f);
  uint16_t us = (uint16_t)(SERVO_MIN_US + eased * (SERVO_MAX_US - SERVO_MIN_US));
  writeServoUS(idx, us);   // channel == idx (0..5)
}

// Map steer [0..1] -> microseconds, with gentle easing at ends (uses SERVO_CH)
void writeSteer(uint8_t channel, float f01) {
  if (f01 < 0) f01 = 0;
  if (f01 > 1) f01 = 1;
  float eased = 0.5f - 0.5f * cosf(f01 * 3.14159265f);
  uint16_t us = (uint16_t)(SERVO_MIN_US + eased * (SERVO_MAX_US - SERVO_MIN_US));
  writeServoUS(channel, us);
}

// Write to each servo channel
void writeSteerAll(float f01) {
  if (f01 < 0) f01 = 0;
  if (f01 > 1) f01 = 1;

  // cosine ease-in-out for smoother approach near extremes
  float eased = 0.5f - 0.5f * cosf(f01 * 3.14159265f);
  uint16_t us = (uint16_t)(SERVO_MIN_US + eased * (SERVO_MAX_US - SERVO_MIN_US));

  // Write to each defined channel
  writeServoUS(SERVO_CH_0, us);
  writeServoUS(SERVO_CH_1, us);
  writeServoUS(SERVO_CH_2, us);
  writeServoUS(SERVO_CH_3, us);
  writeServoUS(SERVO_CH_4, us);
  writeServoUS(SERVO_CH_5, us);
}

void servoInit() {
  Wire.begin(I2C_SDA, I2C_SCL);
  if (!pwm.begin()) {
    Serial.println("PCA9685 not found. Check wiring/address (default 0x40).");
  } else {
    pwm.setPWMFreq(SERVO_FREQ);
    delay(10);
    // Center all 6 servos on channels 0..5
    for (uint8_t i = 0; i < SERVO_COUNT; ++i) {
      writeServoFrac(i, 0.5f);
    }
    // Also set the steering channel (keeps your existing behavior)
    writeSteerAll(steerCmd);
    Serial.println("Servo: PCA9685 ready (6 channels: 0..5).");
  }
}
