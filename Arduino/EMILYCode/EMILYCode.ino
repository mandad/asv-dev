/* 
 Output servos are either driven by input from MOOS-IvP system or RC Radio
 Override controlled by a channel on the radio

 13 Mar 2015
 Damian Manda
 damian.manda@noaa.gov
 */
 
#include <Servo.h>
#include <ReceiverMega.h>
//#include "MOOS.h"

//#define _DEBUG
 
Servo throttle;
Servo rudder;

//On Board LED
#define mode_status 13
 
//-----------------------------------
// Definitions for RC Control
//-----------------------------------
ReceiverMega RCReceiver;

//Pin definitions 
//Positions in Receive Array
#define radio_rudder 0    //Analog 12
#define radio_throttle 1  //Analog 13
#define radio_mode 2      //Analog 14
#define radio_starter 4   //Analog 15
//PWM Output
#define servo_throttle 9
#define servo_rudder 8
//Number of input/output channels
#define num_channels 4

//Initialize variables
int out_throttle = 0;
int out_rudder = 0;
int pos = 1;  //servo position
byte dir = 1;

// mode change: true = interrupts disabled
boolean mode_change = true;
byte mode_change_count = 0;

//Input RC Pulses
unsigned int pulse[num_channels];


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

int missing_moos_comms = 0;

 
void setup() 
{ 
  throttle.attach(servo_throttle);  // attaches the servo on pin 9 to the servo object
  rudder.attach(servo_rudder);
  
  //this is the blinker LED for status
  pinMode(13, OUTPUT);
  digitalWrite(13, LOW);
  
  //Serial is output to USB
  //Serial2 is comms with MOOS over Pins
  Serial.begin(115200);
  //Serial2.begin(115200);
} 
 
void loop() 
{
  
  //Get latest values from RC Input
  for (byte i = 0; i < num_channels; i++)
    pulse[i] = RCReceiver.getChannelValue(i);
   
  //Check if mode switch is engaged 
  if (mode_change_count > 10 && pulse[radio_mode] < 1500) {
    if (!mode_change) {
      digitalWrite(mode_status, HIGH);
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
    
      //Read Serial Input from MOOS
      bool moos_status = readInput();
      if (moos_status) {
        //Write values from MOOS to servos
        throttle.write(map(desired_thrust, 0, 100, 0, 180));
        rudder.write(map(desired_rudder, -90, 90, 0, 180));
        missing_moos_comms = 0;
      } else if (missing_moos_comms < 5000) {
         throttle.write(map(desired_thrust, 0, 100, 0, 180));
         rudder.write(map(desired_rudder, -90, 90, 0, 180));
      } else {
        //Go in slow circles
        throttle.write(15);
        rudder.write(115);
      }
      if (!moos_status)
        missing_moos_comms++;
        
  } else {
    //Trying to eliminate jitter due to switching modes
    if (pulse[radio_mode] < 1500) {
      mode_change_count++;
    } else {
      mode_change_count = 0;
    }
    if (mode_change) {
      digitalWrite(mode_status, LOW);
      mode_change = false;
    }

    //Pass through the values from the RC Input
    passThroughRC();
    
    //Print value to serial
    #ifdef _DEBUG
    Serial.print("Radio Mode: ");
    Serial.println(pulse[radio_mode]);
    #endif
  }

//  delayMicroseconds(15000);
//  Serial.println(mode_change_count);

}

void passThroughRC()
{
    throttle.writeMicroseconds(pulse[radio_throttle]);
    rudder.writeMicroseconds(pulse[radio_rudder]);
}
 
//========================
//  MOOS Related Comms
//========================

/* Read any input from the autonomy backend */
bool readInput()
{
  bool ret = false;
  
  // Check if there's incoming serial data.
  while (Serial.available() > 0) // Need to adjust this so we don't starve out the rest of the loop if there is a lot of data to read
  {
    char buf[bufLen];
    int nBytes;

    // Read bytes from the serial buffer
    nBytes = Serial.readBytesUntil(delimiter, buf, bufLen);

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
        #ifdef _DEBUG
        Serial.print("Throttle = ");
        Serial.println(desired_thrust);
        #endif
      }

      else if (ValFromString(sBuf, DESIRED_RUDDER, &val, delimiter))
      { // Got heading value
        //writeOutput("DEBUG", buf);
        desired_rudder = val;
        #ifdef _DEBUG
        Serial.print("Rudder = ");
        Serial.println(desired_rudder);
        #endif
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
