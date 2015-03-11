
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
byte first_pulse = 0;
unsigned long up_time[num_channels];
unsigned long down_time[num_channels];

void setup()
{
  pinMode(radio_mode, INPUT); //ch5
  attachInterrupt(4, isrCh5Change, CHANGE);
  
  // Feedback LED
  pinMode(13, OUTPUT);
  digitalWrite(13, LOW);
  #ifdef _DEBUG
  Serial.begin(115200);
  #endif
}

void loop()
{
  //Make a non-volitile version
  noInterrupts();
  val_mode = pulse[2];
  interrupts();
  
  if (mode_change_count > 100 && val_mode < 1500) {
    if (!mode_change) {
      mode_change = true;
    }
    
  } else {
    if (val_mode < 1500) {
      mode_change_count++;
    } else {
      mode_change_count = 0;
    }
    if (mode_change) {
      mode_change = false;
    }
  }
  #ifdef _DEBUG
  Serial.print("Radio Mode: ");
  Serial.print(val_mode);
  Serial.print("    Change Count: ");
  Serial.println(mode_change_count);
  #endif
  
  //Toggle the LED to show mode status
  if (mode_change) {
    digitalWrite(13, HIGH);  
  } else {
    digitalWrite(13, LOW);
  }
}

void isrCh5Change ()
{
  if (digitalRead(radio_mode) == HIGH) {
    up_time[2] = micros();
    first_pulse = first_pulse | 4;
  } else if (first_pulse & 4) {
    pulse[2] = micros() - up_time[2];
  }
}
