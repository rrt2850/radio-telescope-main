#include <Arduino.h>
#include <Wire.h>
#include <JrkG2.h>
#include <AccelStepper.h>

JrkG2I2C jrk;
uint16_t feedback;
String serialInput;

// Define motion states
// MOVEAZ - Move Azimuth Rotator
// MOVEALT - Move Altitude LinAc
// IDLE (self explanatory)
enum State { IDLE, MOVEAZ, MOVEALT };
State currentState = IDLE;

// Azimuth Drive Setup
AccelStepper azStepper(AccelStepper::DRIVER, 9, 10);
float azAngle;
long azTarget = 0; // set initial azimuth target to 0
float beltRatio = 5.0; // Gear Ratio of Pulleys
float gearboxRatio = 4.0; // Gearbox gear ratio
float microStepRes = 3200; // Microstep resolution of controller, can be changed manually
float microStepAngle = 360/microStepRes; // Effective step angle of azimuth motor

// Altitude Drive Setup
float altAngle;
unsigned int max = 4095; // Max scaled feedback
unsigned int min = 0; // Min scaled feedback
float currentPos = 0; // Initialize current pos.
const float Sd = 0.5; // meters, Distance between linac & dish axles
const float Cd = 0.0508; // meters, distance from dish axle to linac connection point
float Lmin = 0.457; // meters, Min linac length
float Lmax = 0.527; // meters, Max linac length
float L; // linac length
int altTarget; // target position
float altDelay = 5; // seconds, Altitude motion delay before azimuth motion begins

void setup() {

  // Serial Setup
  Serial.begin(115200);
  Serial.setTimeout(100);
  Wire.begin();
  while (Serial.available() > 0) {Serial.read();}
  
  // Azimuth setup routine
  azStepper.setMaxSpeed(300);
  azStepper.setAcceleration(5);
  azStepper.setCurrentPosition(0); // Boot position is 0 deg Azimuth, pointed north (ideally)
  azStepper.setPinsInverted(true); // Invert direction pin, necessary to rotate the stepper in correct direction
  // stepperCurrentLimit = 4.5 A - set this manually using the switches on the driver

  // Altitude setup routine
  uint16_t linacCurrentLimit = 5.0; // Amps
  jrk.setEncodedHardCurrentLimit(linacCurrentLimit); // Publish current limit to linac controller
}

void loop() {

  if (currentState == MOVEAZ) {
    // If in the MOVEAZ (move azimuth) state, run stepper
    // accelStepper needs the azStepper.run() function to be called as often as possible
    // This is because the accelStepper library uses elapses time to determine when it should send a pulse to the stepper
    azStepper.run();
  }

  if (Serial.available()) {
    while (!Serial.available());
    serialInput = Serial.readString(); // get serial input
    serialInput.trim(); // Trim nonsense off of serial input
    Serial.println("Reading Serial Input"); // notify user that serial input is received 

    // STOP and return to home
    if (serialInput[0] == 'S') {
      Serial.println("Returning to Home");
      
      altAngle = 5; // set altitude to minimum
      float altAngleRad = altAngle*PI/180; // convert altitude angle to radians
      L = sqrt(Sd*Sd+Cd*Cd-2*Sd*Cd*cos((4*PI/6)-altAngleRad)); // UPDATE!!! determine desired length from phi input
      altTarget = (int)(((L-Lmin)/(Lmax-Lmin))*(max-min));
      azTarget = 0;

      // Publish Target Values
      jrk.setTarget(altTarget); // publish target value to Alt Driver / Linac
      azStepper.moveTo(azTarget); // publish target value to Az Driver / AccelStepper

      currentState = MOVEALT;
      Serial.println("Current State: ");
      Serial.println(currentState);
    }

    // Zero Azimuth at current position
    if (serialInput[0] == 'Z') {
      // Zero Azimuth at current position
      // In other words, set current azimuth angle as North
      azStepper.setCurrentPosition(0);
      Serial.println('Set current Azimuth position as North');
    }

    // Move to a target
    if (serialInput[0] == 'G') {
      // jrk.setTarget(max);
      int altStart = 1;
      int altEnd = 0;
      int azStart = 0;
      int azEnd = 0;

      for(int i = 0; i < serialInput.length(); i++){
        switch (serialInput[i]){
          case 'e':
            altEnd = i-1;
            azStart = i+1;
            break;
          case ';':
            azEnd = i-1;
            break;
          default:
            break;
        }
      }

      azAngle = serialInput.substring(azStart, azEnd).toFloat(); // *180/3.14159265; // extract theta from string, convert to degrees from radians
      altAngle = serialInput.substring(altStart, altEnd).toFloat(); // extract phi from string
      Serial.println("Recieved Target:");
      Serial.println(serialInput);
      Serial.println("Azimuth Target Angle:");
      Serial.println(azAngle,10);
      Serial.println("Altitude Target Angle:");
      Serial.println(altAngle,10);

      int theta_sign = int(serialInput[1]);
      //Serial.println(theta_sign);

      if (theta_sign == -3) azAngle *= -1;

      // Print target values
      Serial.println("Moving to:");
      Serial.println(azAngle);
      Serial.println(altAngle);

      // Calculate Altitude target in terms of potentiometer feedback
      float altAngleRad = altAngle*PI/180; // convert altitude angle to radians
      //Serial.println(altAngleRad);
      L = sqrt(Sd*Sd+Cd*Cd-2*Sd*Cd*cos((4*PI/6)-altAngleRad)); // UPDATE!!! determine desired length from phi input
      altTarget = (int)(((L-Lmin)/(Lmax-Lmin))*(max-min)); //Map desired linac length to int. target value
      feedback = jrk.getScaledFeedback();

      // Feedback readout from JrkG2
      Serial.println("Target (scaled feedback):");
      Serial.println(altTarget);
      Serial.println("Current pos. (scaled feedback):");
      Serial.println(feedback);

      // Ensure target is within operating range. If not, set it to min or max and tell the user
      if (altTarget < min){
        altTarget = min;
        Serial.println("Hit Min Feedback Limit");
      }
      if (altTarget > max){
        altTarget = max;
        Serial.println("Hit Mix Feedback Limit");
      }

      // Calculate azimuth target in units of motor steps
      long azTarget = lround(azAngle*gearboxRatio*beltRatio*(1/microStepAngle));
      Serial.println("Azimuth Target (steps): ");
      Serial.println(azTarget);

      // Publish Target Values
      jrk.setTarget(altTarget); // publish target value to Alt Driver / Linac
      azStepper.moveTo(azTarget); // publish target value to Az Driver / AccelStepper

      currentState = MOVEALT;
      Serial.println("Current State: ");
      Serial.println(currentState);
    }
  }

  switch (currentState) {
    
    case IDLE:
      //nothing to do
    break;

    case MOVEALT:
      jrk.setTarget(altTarget); // Set Altitude Target
      delay(1000*altDelay);

      currentState = MOVEAZ;
      Serial.println("Current State: ");
      Serial.println(currentState);
    break;

    case MOVEAZ:
      azStepper.run();
      if (azStepper.distanceToGo() == 0) {
        // If accelStepper thinks that we've reached the azimuth target, stop azimuth motion
        currentState = IDLE;
        Serial.println("Current State: ");
        Serial.println(currentState);
        Serial.println("DONE");
      }
    break;

  }

}

