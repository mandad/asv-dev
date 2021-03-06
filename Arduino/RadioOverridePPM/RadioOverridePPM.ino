/* 
Servo position sweeps unless overridden by radio input

 modified on 22 Oct 2014
 by Damian Manda
 */

#include <Servo.h> 
 
Servo throttle;
Servo rudder;
 
//Pin definitions 
//Digital
#define radio_throttle 22
#define radio_rudder 24
#define radio_mode 26
//PWM
#define servo_throttle 9
#define servo_rudder 10

//Initialize variables
int val_mode;    // variable to read the value from the ppm pin
int val_throttle;
int val_rudder;
int out_throttle = 0;
int out_rudder = 0;
int pos = 1;  //servo position
int dir = 1;
 
void setup() 
{ 
  throttle.attach(servo_throttle);  // attaches the servo on pin 9 to the servo object
  rudder.attach(servo_rudder);
  pinMode(radio_throttle, INPUT);
  pinMode(radio_rudder, INPUT);
  pinMode(radio_mode, INPUT);
  Serial.begin(9600);
} 
 
void loop() 
{
  val_mode = pulseIn(radio_mode, HIGH, 22000);
  
  //Check if mode switch is engaged 
  if (val_mode < 1500) {
    if (pos < 180 && pos > 0) {
      pos += dir;
    } else {
      pos -= dir;
      dir = dir * -1;
    }
    throttle.write(pos);
    rudder.write(pos);
    //delay(15);
  } else {
    //Read additional channels
    val_throttle = pulseIn(radio_throttle, HIGH, 25000);
    val_rudder = pulseIn(radio_rudder, HIGH, 25000);
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
    //Serial.print("Radio Throttle: ");
    //Serial.println(val_throttle);
  }

} 
