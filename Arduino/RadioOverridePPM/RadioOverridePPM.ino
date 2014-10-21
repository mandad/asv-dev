/* 
Servo position sweeps unless overridden by a potentiometer

 modified on 21 Oct 2014
 by Damian Manda
 */

#include <Servo.h> 
 
Servo throttle;  // create servo object to control a servo 
 
//Pin definitions 
int radio_throttle = 22;  //digital
int radio_rudder = 23;
int radio_mode = 24;  //analog
int servo_throttle = 9;

//Initialize variables
int val_mode;    // variable to read the value from the ppm pin
int val_throttle;
int val_rudder;
int servo_out = 0;
int pos = 1;  //servo position
int dir = 1;
 
void setup() 
{ 
  throttle.attach(servo_throttle);  // attaches the servo on pin 9 to the servo object
  pinMode(radio_throttle, INPUT);
  pinMode(radio_rudder, INPUT);
  pinMode(radio_mode, INPUT);
  Serial.begin(9600);
} 
 
void loop() 
{
  val_mode = pulseIn(radio_mode, HIGH, 25000);          // reads the value of the potentiometer (value between 0 and 1023)
  val_throttle = pulseIn(radio_throttle, HIGH, 25000);
  val_rudder = pulseIn(radio_rudder, HIGH, 25000);
  
  //Print value to serial
  Serial.print("Radio Throttle: ");
  Serial.println(val_throttle);
  
  //Check if value is relevant to 
  if (val_mode < 1500) {
    if (pos < 180 && pos > 0) {
      pos += dir;
    } else {
      pos -= dir;
      dir = dir * -1;
    }
    throttle.write(pos);
    //delay(15);
  } else {
    //Convert value to servo scale (1-180)
    servo_out = map(val_throttle, 1115, 1913, 0, 180); //throttle
    servo_out = constrain(servo_out, 0, 180);
    throttle.write(servo_out);                 
    //delay(15);
  }

} 
