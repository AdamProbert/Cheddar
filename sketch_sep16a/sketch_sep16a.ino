// ESP32-C3 SuperMini safe pins
#define AIN1 5
#define AIN2 6
#define STBY 10   // enable pin (STBY on your board)

void setup() {
  Serial.begin(115200);
  delay(1000);  // let Serial come up

  pinMode(AIN1, OUTPUT);
  pinMode(AIN2, OUTPUT);
  pinMode(STBY, OUTPUT);

  digitalWrite(STBY, HIGH);   // enable driver

  Serial.println("Setup complete. Driver enabled.");
}

void loop() {
  Serial.println("Forward...");
  digitalWrite(AIN1, HIGH);
  digitalWrite(AIN2, LOW);
  delay(2000);

  Serial.println("Stop...");
  digitalWrite(AIN1, LOW);
  digitalWrite(AIN2, LOW);
  delay(1000);

  Serial.println("Reverse...");
  digitalWrite(AIN1, LOW);
  digitalWrite(AIN2, HIGH);
  delay(2000);

  Serial.println("Stop...");
  digitalWrite(AIN1, LOW);
  digitalWrite(AIN2, LOW);
  delay(1000);
}
