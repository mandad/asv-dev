/* 
Servo position sweeps unless overridden by radio input

 modified on 20 Nov 2014
 by Damian Manda
 */

#include <Servo.h>
//#include "MOOS.h"

//#define _DEBUG
 
Servo throttle;
Servo rudder;
 
//-----------------------------------
// Definitions for RC Control
//-----------------------------------

//Pin definitions 
//Digital
#define radio_mode 2
#define radio_starter 3
//PWM
#define servo_throttle 9
#define servo_rudder 10
//Hardware switch output
#define switch_out 22
//Number of input/output channels
#define num_channels 2

//Initialize variables
int val_mode;    // variable to read the value from the ppm pin
int val_throttle;
int val_rudder;
int val_starter;
int out_throttle = 0;
int out_rudder = 0;
int pos = 1;  //servo position
int dir = 1;

// mode change: true = interrupts disabled
boolean mode_change = true;
byte mode_change_count = 0;

//Interrupt variables
volatile unsigned long pulse[num_channels];
byte first_pulse;
unsigned long up_time[num_channels];
unsigned long down_time[num_channels];

//-----------------------------------
// Definitions for MOOS I/O
//-----------------------------------
// Message Variables
const int bufLen = 4096;
const char delimiter = ',';
// Input key names
const char *DESIRED_THRUST = "DESIRED_THRUST";
const char *DESIRED_RUDDER = "DESIRED_RUDDER";

// Output key names
const char *NAV_X = "NAV_X";
const char *NAV_Y = "NAV_Y";
const char *NAV_HEADING = "NAV_HEADING";
const char *NAV_SPEED = "NAV_SPEED";
const char *DEBUG = "DEBUG";
const char *OBSTACLE_DATA = "OBSTACLE_DATA";

double nav_x = 0;
double nav_y = 0;
double nav_heading = 0;
double nav_speed = 0;

double desired_thrust = 0;
double desired_rudder = 0;

 
void setup() 
{ 
  throttle.attach(servo_throttle);  // attaches the servo on pin 9 to the servo object
  rudder.attach(servo_rudder);
  
  //Interrupt inputs
  pinMode(radio_mode, INPUT);  //ch5
  pinMode(radio_starter, INPUT);  //ch6
  
  //Output to switch external gates
  //Start in RC control mode
  pinMode(switch_out, OUTPUT);
  digitalWrite(switch_out, LOW);
  
  //Only attach the mode one at this point
  //INT.0 is pin 2, 
  attachInterrupt(0, isrCh5Change, CHANGE);
  
  //this is the blinker LED for 
  pinMode(13, OUTPUT);
  digitalWrite(13, LOW);
  //Serial is output to USB
  //Serial2 is comms with MOOS
  Serial.begin(9600);
  Serial2.begin(115200);
} 
 
void loop() 
{
  //Read Serial Input from MOOS
  readInput();
  
  //Turn off interrupts to read the volatile variable
  //val_mode = pulseIn(radio_mode, HIGH, 22000);
  noInterrupts();
  val_mode = pulse[0];
  val_starter = pulse[1];
  interrupts();
   
  //Check if mode switch is engaged 
  if (mode_change_count > 100 && val_mode < 1500) {
    if (!mode_change) {
      toggleInterrupts(false);
      digitalWrite(switch_out, HIGH);
      mode_change = true;
    }
    
//    if (pos < 180 && pos > 0) {
//      pos += dir;
//    } else {
//      pos -= dir;
//      dir = dir * -1;
//    }
//    throttle.write(pos);
//    rudder.write(pos);
    //have to delay or else it increments faster than the servos turn
    //delayMicroseconds(15000);

      //Write values from MOOS to servos
      throttle.write(map(desired_thrust, 0, 100, 0, 180));
      rudder.write(map(desired_rudder, -90, 90, 0, 180));
  } else {
    //Trying to eliminate jitter due to switching modes
    if (val_mode < 1500) {
      mode_change_count++;
    } else {
      mode_change_count = 0;
    }
    if (mode_change) {
      toggleInterrupts(true);
      digitalWrite(switch_out, LOW);
      mode_change = false;
    }

    //No need to do anything w/throttle, rudder - hardware is switched 
    
    //Print value to serial
    #ifdef _DEBUG
    Serial.print("Radio Mode: ");
    Serial.println(val_mode);
    #endif
  }
  
  //Toggle the LED to show mode status
  if (mode_change) {
    digitalWrite(13, HIGH);  
  } else {
    digitalWrite(13, LOW);
  }

//  delayMicroseconds(15000);
//  Serial.println(mode_change_count);

}

void toggleInterrupts(boolean is_RC) {
  noInterrupts();
  if (is_RC) {
    attachInterrupt(1, isrCh6Change, CHANGE);
  } else {
    detachInterrupt(1);
  }
  interrupts();
}
    

//==========================
//        ISRs
//==========================

//These ignore that time wraps
//Idea for faster: after first state check, toggle a bit

void isrCh5Change ()
{
  if (digitalRead(radio_mode) == HIGH) {
    up_time[0] = micros();
    first_pulse = first_pulse | 4;
  } else if (first_pulse & 4) {
    pulse[0] = micros() - up_time[0];
  }
}

void isrCh6Change ()
{
  if (digitalRead(radio_starter) == HIGH) {
    up_time[1] = micros();
    first_pulse = first_pulse | 8;
  } else if (first_pulse & 8) {
    pulse[1] = micros() - up_time[1];
  }
}

//========================
//  MOOS Related Comms
//========================

/* Read any input from the autonomy backend */
bool readInput()
{
  bool ret = false;
  
  // Check if there's incoming serial data.
  while (Serial2.available() > 0) // Need to adjust this so we don't starve out the rest of the loop if there is a lot of data to read
  {
    char buf[bufLen];
    int nBytes;

    // Read bytes from the serial buffer
    nBytes = Serial2.readBytesUntil(delimiter, buf, bufLen);

    // Check that data was actually read
    if (nBytes > 0)
    {
      double val;
      String sBuf;

      buf[nBytes] = '\0';
      sBuf = String(buf);
      ret = true;

      // Parse the received data for different key-value pairs
      if (ValFromString(sBuf, DESIRED_THRUST, &val, delimiter))
      { // Got speed value
        //writeOutput("DEBUG", buf);
        desired_thrust = val;
        Serial.print("Throttle = ");
        Serial.println(desired_thrust);
      }

      else if (ValFromString(sBuf, DESIRED_RUDDER, &val, delimiter))
      { // Got heading value
        //writeOutput("DEBUG", buf);
        desired_rudder = val;
        Serial.print("Rudder = ");
        Serial.println(desired_rudder);
      }

      else
        continue;
    }
  }

  return ret;
} /* readInput */

/**
 * Get the value of a key from within a string.  The string should be in the
 * form: key=val<delim>...
 *    where <delim> is the value of the delimiter.
 *
 * @param str the string to parse
 * @param key the name of the key whose value to extract
 * @param valBuf (out) a buffer to place the value in
 * @param delim the delimiter separating key-value pairs
 *
 * @return true  if the value was successfully extracted
 *         false if the string was not correctly formatted
 */
bool ValFromString(String str, String key, double *valBuf, char delim)
{
  int eqIndex = str.indexOf('=');    // index of equals sign
  int delIndex = str.indexOf(delim); // index of delimiter
  int valStart = eqIndex + 1;        // index of start of value

  // Check that an '=' was found and the value field is not empty
  if (eqIndex == -1 || delIndex == valStart)
    return false;

  // Get the key from the string
  String sKey = str.substring(0, eqIndex);

  // Check that the key is correct
  if (sKey != key)
    return false;

  // Get the value of the key from the string
  const int bufLen = 255;
  char val[bufLen];
  str.substring(valStart, delIndex).toCharArray(val, bufLen);

  // Place the value in the buffer
  *valBuf = atof(val);
  return true;
} /* ValFromString */
