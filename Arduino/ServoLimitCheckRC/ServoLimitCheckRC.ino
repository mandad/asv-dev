/* 
Simple program for testing limits of servos in physical systems

 16 Apr 2015
 Damian Manda
 damian.manda@noaa.gov
 */

#include <Servo.h>
#include <ReceiverMega.h>

#define OUTPUT_PORT 8  //pwm
Servo out;

//Input RC Pulses
ReceiverMega RCReceiver;
unsigned int pulse_in;

void setup() {
  Serial.begin(115200);
  out.attach(OUTPUT_PORT);
  pulse_in = 0;
}

void loop() {
  pulse_in = RCReceiver.getChannelValue(1);  //Analog 13 == throttle
  out.writeMicroseconds(pulse_in);
  
  Serial.print("Channel Value: ");
  Serial.println(pulse_in);
  
  delayMicroseconds(1000);
}
