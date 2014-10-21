/* 
Servo position sweeps unless overridden by a potentiometer

 modified on 15 Oct 2014
 by Damian Manda
 */

#include <Servo.h> 
 
Servo myservo;  // create servo object to control a servo 
 
int potpin = 0;  // analog pin used to connect the potentiometer
int val;    // variable to read the value from the analog pin
int pos = 1;  //servo position
int dir = 1;
 
void setup() 
{ 
  myservo.attach(9);  // attaches the servo on pin 9 to the servo object
  Serial.begin(9600);
} 
 
void loop() 
{
  val = analogRead(potpin);            // reads the value of the potentiometer (value between 0 and 1023)
  
  //Print value to serial
  Serial.print("Analog Value:");
  Serial.println(val);
  
  //Check if value is relevant to 
  if (val < 300) {
    if (pos < 180 && pos > 0) {
      pos += dir;
    } else {
      pos -= dir;
      dir = dir * -1;
    }
    myservo.write(pos);
    delay(15);
  } else {
    //Convert value to servo scale (1-180)
    val = map(val, 0, 1023, 0, 180);
    myservo.write(val);                 
    delay(15);
  }

} 
