#include <Servo.h>

#define SERVO_A_PIN 6
#define SERVO_B_PIN 7
#define STEP_INTERVAL 15
#define MIN_ANGLE 0
#define MAX_ANGLE 180

Servo servoA;
Servo servoB;

int currentA = 90;
int currentB = 90;
int targetA = 90;
int targetB = 90;

unsigned long lastStepTime = 0;
String inputLine = "";

int clampAngle(int a) {
  if (a < MIN_ANGLE) return MIN_ANGLE;
  if (a > MAX_ANGLE) return MAX_ANGLE;
  return a;
}

void setTargetAngle(int angle) {
  angle = clampAngle(angle);
  targetA = angle;
  targetB = 180 - angle;
}

void updateServos() {
  unsigned long now = millis();
  if (now - lastStepTime < STEP_INTERVAL) return;
  lastStepTime = now;

  if (currentA < targetA) currentA++;
  else if (currentA > targetA) currentA--;

  if (currentB < targetB) currentB++;
  else if (currentB > targetB) currentB--;

  servoA.write(currentA);
  servoB.write(currentB);
}

void setup() {
  Serial.begin(9600);

  servoA.attach(SERVO_A_PIN);
  servoB.attach(SERVO_B_PIN);

  servoA.write(currentA);
  servoB.write(currentB);

  Serial.println("Arduino ready");
}

void loop() {
  //Serial.print(mySerial.available());
  if (Serial.available()) {
    int angle = Serial.parseInt();

    Serial.print("Will move to angle");
    Serial.println(angle);

    if (angle >= 0 && angle <= 180) {
      setTargetAngle(angle);
    }
    
    while (Serial.available() > 0) {
      Serial.read();
    }
  }

  updateServos();
}