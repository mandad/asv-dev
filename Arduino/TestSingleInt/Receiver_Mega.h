/*
    Adaped from AeroQuad v3.0.1
    www.AeroQuad.com
    Copyright (c) 2012 Ted Carancho.

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

#ifndef _RECEIVER_MEGA_H_
#define _RECEIVER_MEGA_H_

#include "Ardunio.h"
#include "Receiver.h"

class Receiver_Mega
{
    public:
        Receiver_Mega();
        int getRawChannelValue(byte channel);

    private:


}

#endif