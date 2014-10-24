/* 
Servo position sweeps unless overridden by radio input

 modified on 22 Oct 2014
 by Damian Manda
 */

#include <Servo.h> 

//#define _DEBUG
 
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
#define num_channels 3

//Initialize variables
int val_mode;    // variable to read the value from the ppm pin
int val_throttle;
int val_rudder;
int out_throttle = 0;
int out_rudder = 0;
int pos = 1;  //servo position
int dir = 1;

//Interrupt variables
volatile unsigned long pulse[num_channels];
byte first_pulse;
unsigned long up_time[num_channels];
//long ch3_down_time = 0;
 
void setup() 
{ 
  throttle.attach(servo_throttle);  // attaches the servo on pin 9 to the servo object
  rudder.attach(servo_rudder);
  //pinMode(radio_throttle, INPUT);
  pinMode(radio_rudder, INPUT);
  pinMode(radio_mode, INPUT);
  
  //Interrupt on Pin2
  pinMode(2, INPUT);  //ch3
  pinMode(3, INPUT);  //ch4
  pinMode(21, INPUT);  //ch5
  //attachInterrupt(0, isrCh3Rise, RISING);
  //attachInterrupt(0, isrCh3Fall, FALLING);
  attachInterrupt(0, isrCh3Change, CHANGE);
  attachInterrupt(1, isrCh4Change, CHANGE);
  //attachInterrupt(2, isrCh5Change, CHANGE);
  
  #ifdef _DEBUG
  pinMode(13, OUTPUT);
  digitalWrite(13, LOW);
  Serial.begin(9600);
  #endif
} 
 
void loop() 
{
  //Turn off interrupts to read the volatile variable
  val_mode = pulseIn(radio_mode, HIGH, 22000);
  noInterrupts();
  val_throttle = pulse[0];
  val_rudder = pulse[1];
  //val_mode = pulse[3];
  interrupts();
  
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
    Serial.print("Radio Throttle: ");
    Serial.println(val_throttle);
    #endif
  }

}
//==========================
//        ISRs
//==========================

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
  if (digitalRead(21) == HIGH) {
    up_time[2] = micros();
    first_pulse = first_pulse | 4;
  } else if (first_pulse & 4) {
    pulse[2] = micros() - up_time[2];
  }
}


