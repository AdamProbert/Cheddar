// --------- Serial command parsing ---------

void applySerialCommands() {
  while (Serial.available() > 0) {
    char ch = Serial.read();

    switch (ch) {
      case 'w': case 'W':
        speedTgt = +1.0f;
        Serial.println("CMD: FORWARD (target +1.0)");
        break;

      case 's': case 'S':
        speedTgt = -1.0f;
        Serial.println("CMD: REVERSE (target -1.0)");
        break;

      case 'x': case 'X':
        speedTgt =  0.0f;
        Serial.println("CMD: STOP (target 0.0)");
        break;

      case 'a': case 'A':
        steerTgt =  0.0f;
        Serial.println("CMD: LEFT (target 0.0)");
        break;

      case 'd': case 'D':
        steerTgt =  1.0f;
        Serial.println("CMD: RIGHT (target 1.0)");
        break;

      case 'c': case 'C':
        steerTgt =  0.5f;
        Serial.println("CMD: CENTER (target 0.5)");
        break;

      default:
        // Ignore everything else
        break;
    }
  }
}
