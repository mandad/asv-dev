/* 
Servo position sweeps unless overridden by radio input

 modified on 27 Oct 2014
 by Damian Manda
 */

#include <Servo.h> 

//#define _DEBUG
 
Servo throttle;
Servo rudder;
 
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
  
  //Serial.begin(9600);
} 
 
void loop() 
{
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
    
    if (pos < 180 && pos > 0) {
      pos += dir;
    } else {
      pos -= dir;
      dir = dir * -1;
    }
    throttle.write(pos);
    rudder.write(pos);
    
    //have to delay or else it increments faster than the servos turn
    delayMicroseconds(15000);
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
