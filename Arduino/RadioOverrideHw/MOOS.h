// Templates must be in a separate header file (not in *.ino)

const char delimiter = ','; // delimiter separating key-value pairs

// Write output to serial in key=value format
// Returns the total number of bytes written to serial
template <class T>
inline int writeOutput(const char *key, T value)
{
  int out = 0;
  out += Serial.print(key);
  out += Serial.write('=');
  out += Serial.print(value);
  out += Serial.write(delimiter);
  out += Serial.write('\n');
  Serial.flush();
  return out;
}

// Write output to serial in key=value1:value2 format
// Returns the total number of bytes written to serial
template <class T>
inline int writeOutput(const char *key, T value1, T value2)
{
  int out = 0;
  out += Serial.print(key);
  out += Serial.write('=');
  out += Serial.print(value1);
  out += Serial.write(':');
  out += Serial.print(value2);
  out += Serial.write(delimiter);
  out += Serial.write('\n');
  Serial.flush();
  return out;
}

// Write output to serial in key#=value format where # is param index
// Returns the total number of bytes written to serial
template <class T>
inline int writeOutput(const char *key, int index, T value)
{
  int out = 0;
  out += Serial.print(key);
  out += Serial.print(index);
  out += Serial.write('=');
  out += Serial.print(value);
  out += Serial.write(delimiter);
  out += Serial.write('\n');
  Serial.flush();
  return out;
}
