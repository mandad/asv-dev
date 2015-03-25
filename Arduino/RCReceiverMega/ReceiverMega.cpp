/*
    Adaped from AeroQuad v3.0.1
    Copyright (c) 2012 Ted Carancho.
    Some code ideas also from ArduCopter/APM and 
    https://github.com/lestofante/arduinoSketch/blob/master/ClassPPM/InputPin.cpp

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

    p399 Datasheet - Register summary 
    p69 - Input/Output Config
    p99 - Input Pin registers
*/

#include "ReceiverMega.h"
#include <Arduino.h>
// #include <util/atomic.h>

#define RISING_EDGE 1
#define FALLING_EDGE 0
// These are specific to the Futaba S-FHSS
#define MINONWIDTH 920
#define MAXONWIDTH 2100
#define MINOFFWIDTH 11530
#define MAXOFFWIDTH 12710

#define START_REGISTER 4    //the position of the first interrupt in the vector
#define NUM_INPUTS 4

volatile uint8_t *port_to_pcmask[] = {
    &PCMSK0,
    &PCMSK1,
    &PCMSK2
};
volatile static tPinTimingData _pinData[NUM_INPUTS];

// I think this was made a vector to enable using all interrupts if needed
// Currently only uses index zero
volatile static uint8_t PCintLast[3];

ISR(PCINT2_vect) {
    uint8_t bit;
    uint8_t curr;
    uint8_t changed;
    uint8_t pin;
    uint32_t currentTime;
    uint32_t delTime;

    //http://garretlab.web.fc2.com/en/arduino/inside/arduino/Arduino.h/portInputRegister.html
    //curr = *portInputRegister(11);
    curr = PINK;
    changed = curr ^ PCintLast[0];
    PCintLast[0] = curr;

    // changed is pins that have changed. screen out non pcint pins.
    if ((changed &= PCMSK2) == 0) {
        return;
    }

    currentTime = micros();

    // changed is pcint pins that have changed.
    for (uint8_t i = START_REGISTER; i < START_REGISTER + NUM_INPUTS; i++) {
        bit = 0x01 << i;
        if (bit & changed) {
            pin = i - START_REGISTER;
            // for each pin changed, record time of change
            if (bit & curr) {
                delTime = currentTime - _pinData[pin].fallTime;
                _pinData[pin].riseTime = currentTime;
                if ((delTime >= MINOFFWIDTH) && (delTime <= MAXOFFWIDTH))
                    _pinData[pin].edge = RISING_EDGE;
                else
                    _pinData[pin].edge = FALLING_EDGE; // invalid rising edge detected
            }
            else {
                delTime = currentTime - _pinData[pin].riseTime;
                _pinData[pin].fallTime = currentTime;
                if ((delTime >= MINONWIDTH) && (delTime <= MAXONWIDTH) && (_pinData[pin].edge == RISING_EDGE)) {
                    _pinData[pin].lastGoodWidth = delTime;
                    _pinData[pin].edge = FALLING_EDGE;
                }
            }
        }
    }
}

ReceiverMega::ReceiverMega() {
    //initializeReceiverParam(nbChannel);

    // Set data direction (input)
    DDRK = 0;
    // Set all data registers (pull up) to off
    PORTK = 0;
    //PCMSK2 |=(1<<lastReceiverChannel)-1;
    /* Handle 4 channels
        PCINT20 = ADC12 = PK4
        PCINT21 = ADC13 = PK5
        PCINT22 = ADC14 = PK6
        PCINT23 = ADC15 = PK7
    */
    PCMSK2 = (1 << PCINT23) | (1 << PCINT22) | (1 << PCINT21) | (1 << PCINT20);
    // Enable interrupts on PCINT23:16 (Datasheet p112)
    PCICR |= 0x1 << PCIE2;

    // Initialize state variables
    PCintLast[0] = 0;
    for (uint8_t channel = 0; channel < NUM_INPUTS; channel++) {
      _pinData[channel].edge = FALLING_EDGE;
      //Initialize to larger signal that we will ever get (max uint16)
      _pinData[channel].lastGoodWidth = 65535;
  }
}

uint16_t ReceiverMega::getChannelValue(uint8_t channel) {
    /*  Channel Indexes are as follows:
        0 -> PCINT20 = Analog 12
        1 -> PCINT21 = Analog 13
        2 -> PCINT22 = Analog 14
        3 -> PCINT23 = Analog 15
    */
    // Limit channel to valid value
    uint8_t _channel = channel;
    if(_channel > NUM_INPUTS)
        _channel = NUM_INPUTS;

    // Read in a non blocking interrupt safe manner
    // Possibly use ATOMIC_BLOCK(ATOMIC_RESTORESTATE) {}
    uint16_t ppm_tmp = _pinData[_channel].lastGoodWidth;
    while( ppm_tmp != _pinData[_channel].lastGoodWidth)
        ppm_tmp = _pinData[_channel].lastGoodWidth;
    
    return ppm_tmp;
}

// Orig version
// uint16_t getChannelValue(uint8_t channel) {
//     uint8_t pin = receiverPin[channel];
//     uint8_t oldSREG = SREG;
//     cli();
//     // Get receiver value read by pin change interrupt handler
//     uint16_t receiverRawValue = _pinData[pin].lastGoodWidth;
//     SREG = oldSREG;
    
//     return receiverRawValue;
// }