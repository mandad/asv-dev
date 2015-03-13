#include <ReceiverMega.h>
#include <Servo.h>

ReceiverMega RCReceiver;

#define NUM_PORTS 4
static byte output_pins[] = {6, 7, 8, 9};
Servo output_servo[4];

void setup() {
  for (byte i = 0; i < NUM_PORTS; i++) {
    output_servo[i].attach(output_pins[i]);
    pinMode(output_pins[i], OUTPUT);
  }
}

void loop() {
  for (byte i = 0; i < NUM_PORTS; i++) {
    output_servo[0].write(RCReceiver.getChannelValue(0));
  }
  
}
