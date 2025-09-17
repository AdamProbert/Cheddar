// --------- Motor control (DRV8833) ---------

void motorInit() {
  pinMode(STBY, OUTPUT);
  digitalWrite(STBY, HIGH);

  // Configure per-pin PWM (Arduino-ESP32 core 3.x)
  analogWriteFrequency(AIN1, MOTOR_PWM_FREQ_HZ);
  analogWriteFrequency(AIN2, MOTOR_PWM_FREQ_HZ);
  analogWriteResolution(AIN1, MOTOR_PWM_RES_BITS);
  analogWriteResolution(AIN2, MOTOR_PWM_RES_BITS);

  // Stop
  analogWrite(AIN1, 0);
  analogWrite(AIN2, 0);

  Serial.println("Motor: DRV8833 ready.");
}

// Signed motor: speed in [-1..+1] using analogWrite backend
void setMotorSigned(float v) {
  if (v >  1) v =  1;
  if (v < -1) v = -1;
  v *= MOTOR_MAX_ABS;

  int duty = (int)(fabsf(v) * MOTOR_PWM_MAX);

  if (v > 0) {
    // forward: AIN1 PWM, AIN2 low
    analogWrite(AIN1, duty);
    analogWrite(AIN2, 0);
  } else if (v < 0) {
    // reverse: AIN2 PWM, AIN1 low
    analogWrite(AIN1, 0);
    analogWrite(AIN2, duty);
  } else {
    // stop (coast)
    analogWrite(AIN1, 0);
    analogWrite(AIN2, 0);
  }
}
