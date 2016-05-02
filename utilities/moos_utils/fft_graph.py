import slog_graph
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
import pdb

def angle180(angle):
    while angle > 180:
        angle = angle - 360
    while angle <= -180:
        angle = angle + 360
    return angle

rot = slog_graph.SLogGraph("/Users/damian/School/Research/Code/MOOS-IVP/MOOS Logs/2016-04-16_Swains/MOOSLog_2016_04_16_____19_41_25_ROT_Tests/MOOSLog_2016_04_16_____19_41_25.slog")
mras = slog_graph.SLogGraph("/Users/damian/School/Research/Code/MOOS-IVP/MOOS Logs/2016-04-16_Swains/MOOSLog_2016_04_16_____20_04_59_MRAS/MOOSLog_2016_04_16_____20_04_59.slog")
survey = slog_graph.SLogGraph("/Users/damian/School/Research/Code/MOOS-IVP/MOOS Logs/2016-04-16_Swains/MOOSLog_2016_04_16_____21_13_00_Survey/MOOSLog_2016_04_16_____21_13_00.slog")

rot.set_time_range((415, 860))
mras.set_time_range((300, 760))
survey.set_time_range((30, 1020))

# 10 Hz samples
fs = 10.0
T = 1/fs

rot_rot = rot.get_col_data(2)
mras_rot = mras.get_col_data(2)
survey_rot = survey.get_col_data(2)
raw_rot = [angle180(x) for x in rot.get_col_data(1)]
raw_rot = np.diff(raw_rot) / T
raw_rot = raw_rot[raw_rot != 0]
raw_rot = [angle180(x) for x in raw_rot]

#pdb.set_trace()

# ---- Frequency Spectrum -------
f, Pwelch_spec = signal.welch(rot_rot, fs, nperseg=512, scaling='spectrum')
plt.semilogy(f, Pwelch_spec)
f_mras, Pwelch_spec_mras = signal.welch(mras_rot, fs, nperseg=512, scaling='spectrum')
plt.semilogy(f_mras, Pwelch_spec_mras)
f_survey, Pwelch_spec_survey = signal.welch(survey_rot, fs, nperseg=1024, scaling='spectrum')
plt.semilogy(f_survey, Pwelch_spec_survey)
plt.xlabel('frequency [Hz]')
plt.ylabel('PSD')
plt.title('Spectrum of ROT')
plt.legend(["Rate of Turn Test", "MRAS Adaptation Test", "Survey Pattern"])
plt.grid()
#plt.show()

# ---- Filter the signal --------
#b = signal.firwin2(150, [0.0, 0.3, 0.6, 1.0], [1.0, 2.0, 0.5, 0.0])
nyq = 0.5 * fs
wc = 0.22 / nyq
b, a = signal.butter(2, wc)
bf = signal.firwin(15, wc)

to_filter = rot_rot
rot_filt = signal.lfilter(b, a, to_filter)
rot_filt_fir = signal.lfilter(bf, [1], to_filter)
plt.figure()
plt.plot(to_filter)
plt.plot(rot_filt, lw=2)
plt.plot(rot_filt_fir, lw=2)
plt.legend(["Original", "IIR", "FIR"])
plt.show()