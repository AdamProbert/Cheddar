#pragma once

// I2C (PCA9685)
constexpr int PIN_I2C_SDA = 21;
constexpr int PIN_I2C_SCL = 22;

// UART2 to Raspberry Pi
constexpr int PIN_UART2_RX = 16; // ESP32 RX2
constexpr int PIN_UART2_TX = 17; // ESP32 TX2

// DRV8833 STBY (shared)
constexpr int PIN_DRV_STBY = 27;

// PCA9685 Output Enable (active low)
constexpr int PIN_PCA9685_OE = 5;

// Driver A (M1, M2)
constexpr int PIN_M1_IN1 = 13;
constexpr int PIN_M1_IN2 = 14;
constexpr int PIN_M2_IN1 = 25;
constexpr int PIN_M2_IN2 = 26;

// Driver B (M3, M4)
constexpr int PIN_M3_IN1 = 32;
constexpr int PIN_M3_IN2 = 33;
constexpr int PIN_M4_IN1 = 4;
constexpr int PIN_M4_IN2 = 18;

// Driver C (M5, M6)
constexpr int PIN_M5_IN1 = 19;
constexpr int PIN_M5_IN2 = 23;
constexpr int PIN_M6_IN1 = 2;  // swap if boot issues
constexpr int PIN_M6_IN2 = 15; // swap if boot issues
