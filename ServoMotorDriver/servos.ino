// --------- Servo control (PCA9685) ---------
#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

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

// Map steer [0..1] -> microseconds, with gentle easing at ends
void writeSteer(float f01) {
  if (f01 < 0) f01 = 0;
  if (f01 > 1) f01 = 1;
  // cosine ease-in-out for smoother approach near extremes
  float eased = 0.5f - 0.5f * cosf(f01 * 3.14159265f);
  uint16_t us = (uint16_t)(SERVO_MIN_US + eased * (SERVO_MAX_US - SERVO_MIN_US));
  writeServoUS(SERVO_CH, us);
}

void servoInit() {
  Wire.begin(I2C_SDA, I2C_SCL);
  if (!pwm.begin()) {
    Serial.println("PCA9685 not found. Check wiring/address (default 0x40).");
  } else {
    pwm.setPWMFreq(SERVO_FREQ);
    delay(10);
    writeSteer(steerCmd); // center (uses current steerCmd)
    Serial.println("Servo: PCA9685 ready.");
  }
}
