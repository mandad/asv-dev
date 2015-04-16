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
#define radio_starter 3   //Analog 15
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
boolean mode_change = false;
boolean first_time = true;
byte mode_change_count = 0;
unsigned int flash_count = 0;

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

//---------------------------------
// Definitions for Physical System
//---------------------------------
#define RUDDER_FULL_RIGHT 1000
#define RUDDER_FULL_LEFT  2000
#define RUDDER_AMIDSHIPS  1500

#define THROTTLE_OFF      1000
#define THROTTLE_LOW_ON   1200    //Lowest with engine still running
#define THROTTLE_MAX      2000

#define starter_signal    22
#define inhibit_signal    23

void setup() 
{
  Serial.end();
  
  throttle.attach(servo_throttle);  // attaches the servo on pin 9 to the servo object
  rudder.attach(servo_rudder);
  pinMode(starter_signal, OUTPUT);
  digitalWrite(starter_signal, LOW);
  pinMode(inhibit_signal, OUTPUT);
  digitalWrite(inhibit_signal, HIGH);  //Require an RC signal before allowing start
  
  //this is the blinker LED for status
  pinMode(mode_status, OUTPUT);
  digitalWrite(mode_status, LOW);
  
  //Make sure stuff is initialized
  for (byte i = 0; i < num_channels; i++)
    pulse[i] = 0;
  mode_change = false;
  first_time = true;
  mode_change_count = 0;
  
  //Serial is output to USB
  //Serial2 is comms with MOOS over Pins
  //Serial.begin(115200);
  //Serial2.begin(115200);
} 
 
void loop() 
{
  
  //Get latest values from RC Input
  for (byte i = 0; i < num_channels; i++)
    pulse[i] = RCReceiver.getChannelValue(i);
   
  //Check if mode switch is engaged 
  if (mode_change_count > 10 && pulse[radio_mode] < 1500) {
    if (!mode_change | first_time) {
      digitalWrite(mode_status, HIGH);
      Serial.begin(115200);
      mode_change = true;
      first_time = false;
    }
    digitalWrite(starter_signal, LOW);
    digitalWrite(inhibit_signal, LOW);
    
      //Read Serial Input from MOOS
      bool moos_status = readInput();
      if (moos_status) {
        //Write values from MOOS to servos
        throttle.writeMicroseconds(scaleThrottle(desired_thrust));
        rudder.writeMicroseconds(scaleRudder(desired_rudder));
        missing_moos_comms = 0;
      } else if (missing_moos_comms < 5000) {
         throttle.writeMicroseconds(scaleThrottle(desired_thrust));
         rudder.writeMicroseconds(scaleRudder(desired_rudder));
      } else {
        //Go in slow circles
        throttle.writeMicroseconds(THROTTLE_LOW_ON);
        rudder.writeMicroseconds(RUDDER_AMIDSHIPS);
      }
      if (!moos_status && missing_moos_comms < 5000)
        missing_moos_comms++;
        
  } else if (pulse[radio_mode] == 65535) {
    //No RC Radio contact, center everything
    throttle.write(0);
    rudder.write(90);
    digitalWrite(starter_signal, LOW);
    digitalWrite(inhibit_signal, HIGH);
    
    //Flash the LED to indicate this status
    if (flash_count++ == 0) {
      digitalWrite(mode_status, LOW);
    } else if (flash_count == 1000) {
      digitalWrite(mode_status, HIGH);
    } else if (flash_count > 2000) {
      flash_count = 0;
    }   
  } else {
    //Trying to eliminate jitter due to switching modes
    if (pulse[radio_mode] < 1500) {
      mode_change_count++;
    } else {
      mode_change_count = 0;
    }
    if (mode_change | first_time) {
      digitalWrite(mode_status, LOW);
      Serial.end();
      mode_change = false;
      first_time = false;
    }
    
    //Pass through the values from the RC Input
    passThroughRC();
    
    manageEngine();
    
    //Print value to serial
    #ifdef _DEBUG
    Serial.print("Radio Mode: ");
    Serial.println(pulse[radio_mode]);
    #endif
  }

//  delayMicroseconds(15000);
//  Serial.println(mode_change_count);

}

void manageEngine() {
      //TODO: test these limits
    if (pulse[radio_starter]  > 1850) {
      //Run the starter motor
      digitalWrite(starter_signal, HIGH);
      digitalWrite(inhibit_signal, LOW);
    } else if (pulse[radio_starter] > 1200) {
      //Don't run starter but don't kill either (normal ops)
      digitalWrite(starter_signal, LOW);
      digitalWrite(inhibit_signal, LOW);
    } else {
      //Don't run starter, kill the engine
      digitalWrite(starter_signal, LOW);
      digitalWrite(inhibit_signal, HIGH);
      // Note that this will override pass through value
      throttle.writeMicroseconds(THROTTLE_OFF);
    }
}

void passThroughRC()
{
    throttle.writeMicroseconds(scaleThrottle(map(pulse[radio_throttle], 1900, 1100, 0, 100)));
    rudder.writeMicroseconds(scaleRudder(map(pulse[radio_rudder], 1100, 1900, -45, 45)));
}

unsigned int scaleThrottle(unsigned int input) 
{
  unsigned int th_out = map(input, 0, 100, THROTTLE_LOW_ON, THROTTLE_MAX);
  return constrain(th_out, THROTTLE_LOW_ON, THROTTLE_MAX);
}
 
unsigned int scaleRudder(unsigned int input)
{
  // May need to be more complex if not linear
  unsigned int rud_out =  map(input, -45, 45, RUDDER_FULL_LEFT, RUDDER_FULL_RIGHT);
  return constrain(rud_out, RUDDER_FULL_LEFT, RUDDER_FULL_RIGHT);
}
 
//========================
//  MOOS Related Comms
//========================

/* Read any input from the autonomy backend */
bool readInput()
{
  bool ret = false;
  bool got_rudder = false;
  bool got_thrust = false;
  
  // Check if there's incoming serial data.
  // Need to adjust this so we don't starve out the rest of the loop if there is a lot of data to read
  while (Serial.available() > 14 && (!got_thrust || !got_rudder))
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
        got_thrust = true;
        #ifdef _DEBUG
        Serial.print("Throttle = ");
        Serial.println(desired_thrust);
        #endif
      }

      else if (ValFromString(sBuf, DESIRED_RUDDER, &val, delimiter))
      { // Got heading value
        //writeOutput("DEBUG", buf);
        desired_rudder = val;
        got_rudder = true;
        #ifdef _DEBUG
        Serial.print("Rudder = ");
        Serial.println(desired_rudder);
        #endif
      }
    }
  }
  
  //clear the incoming buffer
  Serial.flushRX();
  
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
