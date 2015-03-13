#include <ReceiverMega.h>
#include <Servo.h>

ReceiverMega RCReceiver;

#define NUM_PORTS 4
// These pins don't have any other function
static byte output_pins[] = {6, 7, 8, 9};
Servo output_servo[4];

void setup() {
  for (byte i = 0; i < NUM_PORTS; i++) {
    output_servo[i].attach(output_pins[i]);
    //pinMode(output_pins[i], OUTPUT);
  }
  Serial.begin(115200);
}

void loop() {
  for (byte i = 0; i < NUM_PORTS; i++) {
    output_servo[i].writeMicroseconds(RCReceiver.getChannelValue(i));
  }
  delayMicroseconds(10000);
  Serial.print("ADC12: ");
  Serial.println(RCReceiver.getChannelValue(0));
}
