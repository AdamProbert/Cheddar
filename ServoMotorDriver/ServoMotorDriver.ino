#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

// ===================== CONFIG / PINS =====================
// DRV8833 (DC motor) pins on ESP32-C3 SuperMini
#define AIN1 5
#define AIN2 6
#define STBY 10   // DRV8833 STBY (enable)

// I2C for PCA9685 (Servos)
#define I2C_SDA 4
#define I2C_SCL 7
#define PCA_ADDR 0x40

// Servo timing (tune to your servo if needed)
const uint16_t SERVO_MIN_US = 500;
const uint16_t SERVO_MAX_US = 2500;
const float    SERVO_FREQ   = 50.0f;    // 50 Hz for hobby servos
const uint8_t  SERVO_CH_0     = 0;        // channel 0 on PCA9685
const uint8_t  SERVO_CH_1     = 1;        // channel 1 on PCA9685
const uint8_t  SERVO_CH_2     = 2;        // channel 2 on PCA9685
const uint8_t  SERVO_CH_3     = 3;        // channel 3 on PCA9685
const uint8_t  SERVO_CH_4     = 4;        // channel 4 on PCA9685
const uint8_t  SERVO_CH_5     = 5;        // channel 5 on PCA9685


// Motor PWM
const uint32_t MOTOR_PWM_FREQ_HZ  = 20000; // 20 kHz (quiet)
const uint8_t  MOTOR_PWM_RES_BITS = 12;    // 0..4095
const int      MOTOR_PWM_MAX      = (1 << MOTOR_PWM_RES_BITS) - 1;
const float    MOTOR_MAX_ABS      = 0.90f; // cap at 90% duty

// Control loop
const uint32_t UPDATE_INTERVAL_MS = 20;    // ~50 Hz control loop
const float SPEED_SLEW_PER_S = 1.5f;       // speed glide rate (units/sec)
const float STEER_SLEW_PER_S = 2.0f;       // steering glide rate (units/sec)

// ===================== GLOBAL STATE =====================
Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(PCA_ADDR);

// current vs target commands
float speedCmd  = 0.0f;  // [-1..+1]
float speedTgt  = 0.0f;  // [-1..+1]
float steerCmd  = 0.5f;  // [0..1] (0=left, 0.5=center, 1=right)
float steerTgt  = 0.5f;  // [0..1]

uint32_t lastUpdateMs = 0;

// ===================== FORWARD DECLS =====================
// from motors.ino
void motorInit();
void setMotorSigned(float v);
// from servos.ino
void servoInit();
void writeSteer(float f01);
void writeSteerAll(uint8_t channel, float f01);
// from serial_input.ino
void applySerialCommands();

// Utility: slew a value toward a target by at most (rate * dt)
static inline float slewToward(float current, float target, float maxDelta) {
  float delta = target - current;
  if (delta >  maxDelta) delta =  maxDelta;
  if (delta < -maxDelta) delta = -maxDelta;
  return current + delta;
}

void setup() {
  Serial.begin(115200);
  delay(800);

  motorInit();
  servoInit();

  lastUpdateMs = millis();
  Serial.println("Ready. Keys: w(forward) s(reverse) x(stop) a(left) d(right) c(center)");
  Serial.println("Also words: start/stop/forward/reverse/left/right/center");
  Serial.println("Tip: Serial Monitor Line ending = Newline (or Both NL & CR).");
}

void loop() {
  // Handle incoming commands (WASD + words)
  applySerialCommands();

  // Timed control loop (non-blocking)
  uint32_t now = millis();
  uint32_t dtms = now - lastUpdateMs;
  if (dtms >= UPDATE_INTERVAL_MS) {
    lastUpdateMs = now;
    float dts = dtms / 1000.0f;

    // glide toward targets
    speedCmd = slewToward(speedCmd, speedTgt, SPEED_SLEW_PER_S * dts);
    steerCmd = slewToward(steerCmd, steerTgt, STEER_SLEW_PER_S * dts);

    // apply outputs
    setMotorSigned(speedCmd);
    writeSteerAll(steerCmd);
  }
}
