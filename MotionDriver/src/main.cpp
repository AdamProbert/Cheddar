#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

#include "pins.h"

constexpr uint8_t kPCA9685_I2C_ADDR = 0x40;
constexpr uint8_t kSERVO_CHANNEL = 0;
constexpr uint16_t kSERVO_MIN_US = 1000;
constexpr uint16_t kSERVO_MAX_US = 2000;
constexpr uint16_t kSERVO_NEUTRAL_US = 1500;
constexpr uint16_t kSERVO_STEP_US = 100;
constexpr uint16_t kSERVO_FREQUENCY_HZ = 50;
constexpr uint16_t kSERVO_PERIOD_US = 20000;
constexpr uint32_t kSERVO_STEP_INTERVAL_MS = 20;
constexpr uint16_t kPCA9685_RESOLUTION = 4096;

Adafruit_PWMServoDriver g_pwmDriver = Adafruit_PWMServoDriver();

uint32_t g_lastServoUpdateMs = 0;
int32_t g_currentServoUs = kSERVO_NEUTRAL_US;
int8_t g_servoStepDirection = 1;
uint8_t g_servoLogDecimator = 0;

uint16_t ServoPulseUsToTicks(uint16_t pulseUs)
{
    const uint32_t clamped = constrain(pulseUs, kSERVO_MIN_US, kSERVO_MAX_US);
    const uint32_t ticks = ((clamped * kPCA9685_RESOLUTION) + (kSERVO_PERIOD_US / 2)) / kSERVO_PERIOD_US;
    return static_cast<uint16_t>(min<uint32_t>(ticks, kPCA9685_RESOLUTION - 1));
}

void WriteServoMicroseconds(uint8_t channel, uint16_t pulseUs)
{
    const uint16_t ticks = ServoPulseUsToTicks(pulseUs);
    g_pwmDriver.setPWM(channel, 0, ticks);
}

void InitializeMotorOutputs()
{
    const int kMotorPins[] = {
        PIN_M1_IN1, PIN_M1_IN2, PIN_M2_IN1, PIN_M2_IN2,
        PIN_M3_IN1, PIN_M3_IN2, PIN_M4_IN1, PIN_M4_IN2,
        PIN_M5_IN1, PIN_M5_IN2, PIN_M6_IN1, PIN_M6_IN2};

    pinMode(PIN_DRV_STBY, OUTPUT);
    digitalWrite(PIN_DRV_STBY, LOW);

    for (int pin : kMotorPins)
    {
        pinMode(pin, OUTPUT);
        digitalWrite(pin, LOW);
    }
}

void setup()
{
    Serial.begin(115200);
    Serial.println("Cheddar servo bring-up");

    InitializeMotorOutputs();

    Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);
    g_pwmDriver.begin();
    Wire.beginTransmission(kPCA9685_I2C_ADDR);
    const uint8_t i2cError = Wire.endTransmission();
    if (i2cError != 0)
    {
        Serial.printf("PCA9685 init failed (I2C error %u). Check wiring and power.\n", i2cError);
        while (true)
        {
            delay(1000);
        }
    }
    g_pwmDriver.setOscillatorFrequency(27000000);
    g_pwmDriver.setPWMFreq(kSERVO_FREQUENCY_HZ);
    delay(10);

    WriteServoMicroseconds(kSERVO_CHANNEL, kSERVO_NEUTRAL_US);
    g_lastServoUpdateMs = millis();

    Serial.println("Servo initialized to neutral.");
}

void loop()
{
    const uint32_t now = millis();
    if (now - g_lastServoUpdateMs < kSERVO_STEP_INTERVAL_MS)
    {
        return;
    }

    g_lastServoUpdateMs = now;
    g_currentServoUs += g_servoStepDirection * kSERVO_STEP_US;

    if (g_currentServoUs >= kSERVO_MAX_US || g_currentServoUs <= kSERVO_MIN_US)
    {
        g_currentServoUs = constrain(g_currentServoUs, kSERVO_MIN_US, kSERVO_MAX_US);
        g_servoStepDirection *= -1;
    }

    WriteServoMicroseconds(kSERVO_CHANNEL, static_cast<uint16_t>(g_currentServoUs));

    if (++g_servoLogDecimator >= 5)
    {
        g_servoLogDecimator = 0;
        Serial.printf("Servo pulse: %d us\n", static_cast<int>(g_currentServoUs));
    }
}
