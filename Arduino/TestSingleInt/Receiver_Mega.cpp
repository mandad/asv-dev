/*
    Adaped from AeroQuad v3.0.1
    www.AeroQuad.com
    Copyright (c) 2012 Ted Carancho.
    Some code ideas also from ArduCopter/APM and 

    Modified for standalone operation on an Arduino Mega
    Damian Manda
    12 March 2015
   
    This program is free software: you can redistribute it and/or modify 
    it under the terms of the GNU General Public License as published by 
    the Free Software Foundation, either version 3 of the License, or 
    (at your option) any later version. 
    This program is distributed in the hope that it will be useful, 
    but WITHOUT ANY WARRANTY; without even the implied warranty of 
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the 
    GNU General Public License for more details. 
    You should have received a copy of the GNU General Public License 
    along with this program. If not, see <http://www.gnu.org/licenses/>. 
*/

#define RISING_EDGE 1
#define FALLING_EDGE 0
#define MINONWIDTH 950
#define MAXONWIDTH 2075
#define MINOFFWIDTH 12000
#define MAXOFFWIDTH 24000

#include "pins_arduino.h"
#include <AQMath.h>
#include "GlobalDefined.h"

volatile uint8_t *port_to_pcmask[] = {
    &PCMSK0,
    &PCMSK1,
    &PCMSK2
};

// I think this was made a vector to enable using all interrupts if needed
volatile static uint8_t PCintLast[3];
// Channel data
typedef struct {
    byte edge;
    unsigned long riseTime;
    unsigned long fallTime;
    unsigned int lastGoodWidth;
} tPinTimingData;
volatile static tPinTimingData pinData[9];

static void MegaPcIntISR() {
    uint8_t bit;
    uint8_t curr;
    uint8_t mask;
    uint8_t pin;
    uint32_t currentTime;
    uint32_t time;

    //curr = *portInputRegister(11);
    curr = PIND
    mask = curr ^ PCintLast[0];
    PCintLast[0] = curr;

    // mask is pins that have changed. screen out non pcint pins.
    if ((mask &= PCMSK2) == 0) {
        return;
    }

    currentTime = micros();

    // mask is pcint pins that have changed.
    for (uint8_t i=0; i < 8; i++) {
        bit = 0x01 << i;
        if (bit & mask) {
            pin = i;
            // for each pin changed, record time of change
            if (bit & PCintLast[0]) {
                time = currentTime - pinData[pin].fallTime;
                pinData[pin].riseTime = currentTime;
                if ((time >= MINOFFWIDTH) && (time <= MAXOFFWIDTH))
                    pinData[pin].edge = RISING_EDGE;
                else
                    pinData[pin].edge = FALLING_EDGE; // invalid rising edge detected
            }
            else {
                time = currentTime - pinData[pin].riseTime;
                pinData[pin].fallTime = currentTime;
                if ((time >= MINONWIDTH) && (time <= MAXONWIDTH) && (pinData[pin].edge == RISING_EDGE)) {
                    pinData[pin].lastGoodWidth = time;
                    pinData[pin].edge = FALLING_EDGE;
                }
            }
        }
    }
}

SIGNAL(PCINT2_vect) {
    MegaPcIntISR();
}

#ifdef OLD_RECEIVER_PIN_ORDER
    // arduino pins 67, 65, 64, 66, 63, 62
    static byte receiverPin[6] = {5, 3, 2, 4, 1, 0}; // bit number of PORTK used for XAXIS, YAXIS, ZAXIS, THROTTLE, MODE, AUX
#else
    //arduino pins 63, 64, 65, 62, 66, 67
    static byte receiverPin[8] = {1, 2, 3, 0, 4, 5, 6, 7}; // bit number of PORTK used for XAXIS, YAXIS, ZAXIS, THROTTLE, MODE, AUX
#endif

void initializeReceiver(int nbChannel = 6) {

    initializeReceiverParam(nbChannel);

    DDRK = 0;
    PORTK = 0;
    //PCMSK2 |=(1<<lastReceiverChannel)-1;
    //Handle 4 channels
    //These are Analog In 12-15
    PCMSK2 = (1 << PCINT23) | (1 << PCINT22) | (1 << PCINT21) | (1 << PCINT20);
    // Enable interrupts on PCINT23:16 (Datasheet p112)
    PCICR |= 0x1 << PCIE2;

    for (byte channel = XAXIS; channel < lastReceiverChannel; channel++)
      pinData[receiverPin[channel]].edge = FALLING_EDGE;
}


int getRawChannelValue(byte channel) {
    byte pin = receiverPin[channel];
    uint8_t oldSREG = SREG;
    cli();
    // Get receiver value read by pin change interrupt handler
    uint16_t receiverRawValue = pinData[pin].lastGoodWidth;
    SREG = oldSREG;
    
    return receiverRawValue;
}

void setChannelValue(byte channel,int value) {
}  

// ------------------------------------------------------------------------------
// PPM READ - INTERRUPT SAFE PPM SERVO CHANNEL READ
// ------------------------------------------------------------------------------
uint16_t ppm_read_channel( uint8_t channel )
{
    // Limit channel to valid value
    uint8_t _channel = channel;
    if( _channel == 0 ) _channel = 1;
    if( _channel > SERVO_CHANNELS ) _channel = SERVO_CHANNELS;

    // Calculate ppm[..] position
    uint8_t ppm_index = ( _channel << 1 ) + 1;
    
    // Read ppm[..] in a non blocking interrupt safe manner
    uint16_t ppm_tmp = ppm[ ppm_index ];
    while( ppm_tmp != ppm[ ppm_index ] ) ppm_tmp = ppm[ ppm_index ];

    // Return as normal servo value
    return ppm_tmp + PPM_PRE_PULSE;    
}
// ------------------------------------------------------------------------------

#endif

