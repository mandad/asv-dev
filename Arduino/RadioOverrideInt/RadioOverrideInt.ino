/* 
Servo position sweeps unless overridden by radio input

 modified on 10 Mar 2015
 Damian Manda
 damian.manda@noaa.gov
 */

#include <Servo.h> 

#define _DEBUG
 
Servo throttle;
Servo rudder;
 
//Pin definitions 
//Digital
#define radio_throttle 2
#define radio_rudder 3
#define radio_mode 19
#define radio_starter 18
//PWM
#define servo_throttle 9
#define servo_rudder 10
//Number of input/output channels
#define num_channels 4

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
  pinMode(radio_throttle, INPUT);  //ch3
  pinMode(radio_rudder, INPUT);  //ch1
  pinMode(radio_mode, INPUT);  //ch5
  pinMode(radio_starter, INPUT);  //ch6
  
  //Only attach the mode one at this point
  //INT.4 is pin 19
  attachInterrupt(4, isrCh5Change, CHANGE);
  
  //this is the blinker LED for 
  pinMode(13, OUTPUT);
  digitalWrite(13, LOW);
  
  Serial.begin(115200);
} 
 
void loop() 
{
  //Turn off interrupts to read the volatile variable
  //val_mode = pulseIn(radio_mode, HIGH, 22000);
  noInterrupts();
  val_throttle = pulse[0];
  val_rudder = pulse[1];
  val_mode = pulse[2];
  val_starter = pulse[3];
  interrupts();
   
  //Check if mode switch is engaged 
  if (mode_change_count > 100 && val_mode < 1500) {
    if (!mode_change) {
      toggleInterrupts(false);
      mode_change = true;
    }
    
    // Sweep the position of the servo
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
    
     //Write values from MOOS to servos
//     throttle.write(map(desired_thrust, 0, 100, 0, 180));
//     rudder.write(map(desired_rudder, -90, 90, 0, 180));
  } else {
    //Trying to eliminate jitter due to switching modes
    if (val_mode < 1500) {
      mode_change_count++;
    } else {
      mode_change_count = 0;
    }
    if (mode_change) {
      toggleInterrupts(true);
      mode_change = false;
    }

    //Convert value to servo scale (1-180)
    //Throttle
    out_throttle = map(val_throttle, 1110, 1910, 0, 180);
    out_throttle = constrain(out_throttle, 0, 180);
    throttle.write(out_throttle);
    //Rudder
    out_rudder = map(val_rudder, 1110, 1910, 0, 180);
    out_rudder = constrain(out_rudder, 0, 180);
    rudder.write(out_rudder);
    
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
    //throttle = pin 2
    attachInterrupt(0, isrCh3Change, CHANGE);
    //rudder = pin 3
    attachInterrupt(1, isrCh4Change, CHANGE);
    //Starter = pin 18
    attachInterrupt(5, isrCh6Change, CHANGE);
  } else {
    detachInterrupt(0);
    detachInterrupt(1);
    detachInterrupt(5);
  }
  interrupts();
}
    

//==========================
//        ISRs
//==========================

//These ignore that time wraps
//Idea for faster: after first state check, toggle a bit
void isrCh3Change ()
{
  if (digitalRead(2) == HIGH) {
    up_time[0] = micros();
    first_pulse = first_pulse | 1;
  } else if (first_pulse & 1) {
    pulse[0] = micros() - up_time[0];
  }
}

void isrCh4Change ()
{
  if (digitalRead(3) == HIGH) {
    up_time[1] = micros();
    first_pulse = first_pulse | 2;
  } else if (first_pulse & 2) {
    pulse[1] = micros() - up_time[1];
  }
}

void isrCh5Change ()
{
  if (digitalRead(19) == HIGH) {
    up_time[2] = micros();
    first_pulse = first_pulse | 4;
  } else if (first_pulse & 4) {
    pulse[2] = micros() - up_time[2];
  }
}

void isrCh6Change ()
{
  if (digitalRead(18) == HIGH) {
    up_time[3] = micros();
    first_pulse = first_pulse | 8;
  } else if (first_pulse & 8) {
    pulse[3] = micros() - up_time[3];
  }
}
