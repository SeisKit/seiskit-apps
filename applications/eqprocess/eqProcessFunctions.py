import numpy as np
import pandas as pd
from scipy import signal, integrate
from numpy.fft import rfft
from numpy import linspace

def detrendFunction(data, method='linear', order=1):
    time = data['Time (s)'].values
    acceleration = data.iloc[:, 1].values

    if method == 'linear':
        detrended_acc = signal.detrend(acceleration, type='linear')
    elif method == 'polynomial':
        p = np.polyfit(time, acceleration, order)
        trend = np.polyval(p, time)
        detrended_acc = acceleration - trend
    else:
        raise ValueError("Method must be 'linear' or 'polynomial'.")

    detrended_data = pd.DataFrame({'Time (s)': time, 'Detrended Acceleration': detrended_acc})
    return detrended_data

def butterworth(filterType, cutoff, delta, order):
    fn = 0.5 / delta

    if filterType == "bandpass":
        highcut = cutoff[0]
        lowcut = cutoff[1]
        b, a = signal.butter(order, [highcut/fn, lowcut/fn], btype = filterType)
    elif filterType == "lowpass":
        lowcut = cutoff[0]
        b, a = signal.butter(order, lowcut/fn, btype = filterType)
    elif filterType == "highpass":
        highcut = cutoff[0]
        b, a = signal.butter(order, highcut/fn, btype = filterType)

    return b, a

def filterFunction(data, filterType, cutoff, delta, order):

    b, a = butterworth(filterType, cutoff, delta, order = order)
    dataFiltered = data.copy()
    dataFiltered['y'] = signal.filtfilt(b, a, data['y'].values)

    return dataFiltered

def ResponseSpectrum(T, s, z, dt):
    T = np.array(T)
    T[T == 0] = np.finfo(float).eps

    if z >= 0.04:
        SA = RSFD(T, s, z, dt)
    else:
        SA = RSPW(T, s, z, dt)
        
    return SA

def RSPW(T, s, zi, dt):
    import numpy as np
    
    pi = np.pi
    nper = np.size(T)
    n = np.size(s)
    SA = np.zeros(nper)
    
    for k in range(nper):
        wn = 2 * pi / T[k]
        wd = wn * (1 - zi ** 2) ** 0.5
        
        u = np.zeros((2, n))
        
        ex = np.exp(-zi * wn * dt)
        cwd = np.cos(wd * dt)
        swd = np.sin(wd * dt)
        zisq = 1 / np.sqrt(1 - (zi ** 2))
        
        a11 = ex * (cwd + zi * zisq * swd)
        a12 = (ex / wd) * swd
        a21 = -wn * zisq * ex * swd
        a22 = ex * (cwd - zi * zisq * swd)
        
        b11 = ex * (((2 * zi ** 2 - 1) / (wn ** 2 * dt) + zi / wn) * (1 / wd) * np.sin(wd * dt) +
                    (2 * zi / (wn ** 3 * dt) + 1 / (wn ** 2)) * np.cos(wd * dt)) - 2 * zi / (wn ** 3 * dt)
        b12 = -ex * (((2 * zi ** 2 - 1) / (wn ** 2 * dt)) * (1 / wd) * np.sin(wd * dt) +
                     (2 * zi / (wn ** 3 * dt)) * np.cos(wd * dt)) - 1 / (wn ** 2) + 2 * zi / (wn ** 3 * dt)
        b21 = -((a11 - 1) / (wn ** 2 * dt)) - a12
        b22 = -b21 - a12
        
        A = np.array([[a11, a12], [a21, a22]])
        B = np.array([[b11, b12], [b21, b22]])
        
        for q in range(n - 1):
            u[:, q + 1] = np.dot(A, u[:, q]) + np.dot(B, np.array([s[q], s[q + 1]]))
        
        at = -2 * wn * zi * u[1, :] - (wn ** 2) * u[0, :]
        
        SA[k] = np.max(np.abs(at))
    
    return SA

def RSFD(T, s, z, dt):
    import numpy as np
    from numpy.fft import fft, ifft
    
    pi = np.pi

    npo = np.size(s)
    nT = np.size(T)
    SA = np.zeros(nT)
    
    n = int(2 ** np.ceil(np.log2(npo + 10 * np.max(T) / dt)))
    fs = 1 / dt
    s = np.append(s, np.zeros(n - npo))
    
    fres = fs / n
    nfrs = int(np.ceil(n / 2))
    freqs = fres * np.arange(0, nfrs + 1, 1)
    ww = 2 * pi * freqs
    ffts = fft(s)
    
    m = 1
    for kk in range(nT):
        w = 2 * pi / T[kk]
        k = m * w ** 2
        c = 2 * z * m * w
        
        H1 = 1 / (-m * ww ** 2 + k + 1j * c * ww)
        H2 = 1j * ww / (-m * ww ** 2 + k + 1j * c * ww)
        H3 = -ww ** 2 / (-m * ww ** 2 + k + 1j * c * ww)
        
        H1 = np.append(H1, np.conj(H1[n // 2 - 1:0:-1]))
        H1[n // 2] = np.real(H1[n // 2])
        
        H2 = np.append(H2, np.conj(H2[n // 2 - 1:0:-1]))
        H2[n // 2] = np.real(H2[n // 2])
        
        H3 = np.append(H3, np.conj(H3[n // 2 - 1:0:-1]))
        H3[n // 2] = np.real(H3[n // 2])
        
        CoF3 = H3 * ffts
        a = ifft(CoF3)
        a = a - s
        SA[kk] = np.max(np.abs(a))
    
    return SA

def ariasIntensityCreator(filteredAcc, samplingInterval):
    # calculate time array
    ariasTime = samplingInterval * np.arange(0, len(filteredAcc))

    # square the accelerations
    accSquare = np.square(filteredAcc)
    
    # integrate to find arias intensity
    ariasIntensity = samplingInterval * integrate.cumtrapz(accSquare, initial=0)
    
    # calculate the 5% and 95% Arias Intensity
    arias05 = 0.05 * ariasIntensity[-1]
    arias95 = 0.95 * ariasIntensity[-1]
    
    # calculate the duration where arias intensity is between 5% and 95%
    timeAriasList = [index for index, value in enumerate(ariasIntensity) if value > arias05 and value < arias95]
    
    if timeAriasList:
        durationAriasIntensity = ariasTime[timeAriasList[-1]] - ariasTime[timeAriasList[0]]
    else:
        durationAriasIntensity = 0
    
    ariasDict = {
        'ariasIntensity': ariasIntensity,
        'arias05': arias05,
        'arias95': arias95,
        'timeAriasList': timeAriasList,
        'ariasTime': ariasTime,
        'durationAriasIntensity': durationAriasIntensity
    }

    return ariasDict

def fourierTransform(data, delta, npts):

    amp = abs(rfft(data))                          
    freq = linspace(0, int((1/delta)/2), int((npts/2)+1))

    return freq, amp