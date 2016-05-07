import numpy as np
import matplotlib.pyplot as plt
from scipy import signal

# 10 Hz samples
fs = 10

nyq = 0.5 * fs
wc = 0.25 / nyq
bi, ai = signal.butter(2, wc)
bf = signal.firwin(11, wc)

bi = [0.7656, -1.5312, 0.7656]
ai = [1, -1.47548, 0.58692]

w1, h1 = signal.freqz(bi, ai)
w2, h2 = signal.freqz(bf)

plt.title('Digital filter frequency response')
plt.plot(w1, 20*np.log10(np.abs(h1)), 'b')
plt.plot(w2, 20*np.log10(np.abs(h2)), 'r')
plt.ylabel('Amplitude Response (dB)')
plt.xlabel('Frequency (rad/sample)')
plt.grid()
plt.show()