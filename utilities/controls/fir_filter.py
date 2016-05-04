import numpy as np
import pdb

def hamming(M, sym=True):
    r"""Return a Hamming window.
    The Hamming window is a taper formed by using a raised cosine with
    non-zero endpoints, optimized to minimize the nearest side lobe.
    Parameters
    ----------
    M : int
        Number of points in the output window. If zero or less, an empty
        array is returned.
    sym : bool, optional
        When True (default), generates a symmetric window, for use in filter
        design.
        When False, generates a periodic window, for use in spectral analysis.
    Returns
    -------
    w : ndarray
        The window, with the maximum value normalized to 1 (though the value 1
        does not appear if `M` is even and `sym` is True).
    Notes
    -----
    The Hamming window is defined as
    .. math::  w(n) = 0.54 - 0.46 \cos\left(\frac{2\pi{n}}{M-1}\right)
               \qquad 0 \leq n \leq M-1
    The Hamming was named for R. W. Hamming, an associate of J. W. Tukey and
    is described in Blackman and Tukey. It was recommended for smoothing the
    truncated autocovariance function in the time domain.
    Most references to the Hamming window come from the signal processing
    literature, where it is used as one of many windowing functions for
    smoothing values.  It is also known as an apodization (which means
    "removing the foot", i.e. smoothing discontinuities at the beginning
    and end of the sampled signal) or tapering function.
    References
    ----------
    .. [1] Blackman, R.B. and Tukey, J.W., (1958) The measurement of power
           spectra, Dover Publications, New York.
    .. [2] E.R. Kanasewich, "Time Sequence Analysis in Geophysics", The
           University of Alberta Press, 1975, pp. 109-110.
    .. [3] Wikipedia, "Window function",
           http://en.wikipedia.org/wiki/Window_function
    .. [4] W.H. Press,  B.P. Flannery, S.A. Teukolsky, and W.T. Vetterling,
           "Numerical Recipes", Cambridge University Press, 1986, page 425.
    Examples
    --------
    Plot the window and its frequency response:
    >>> from scipy import signal
    >>> from scipy.fftpack import fft, fftshift
    >>> import matplotlib.pyplot as plt
    >>> window = signal.hamming(51)
    >>> plt.plot(window)
    >>> plt.title("Hamming window")
    >>> plt.ylabel("Amplitude")
    >>> plt.xlabel("Sample")
    >>> plt.figure()
    >>> A = fft(window, 2048) / (len(window)/2.0)
    >>> freq = np.linspace(-0.5, 0.5, len(A))
    >>> response = 20 * np.log10(np.abs(fftshift(A / abs(A).max())))
    >>> plt.plot(freq, response)
    >>> plt.axis([-0.5, 0.5, -120, 0])
    >>> plt.title("Frequency response of the Hamming window")
    >>> plt.ylabel("Normalized magnitude [dB]")
    >>> plt.xlabel("Normalized frequency [cycles per sample]")
    """
    # Docstring adapted from NumPy's hamming function
    if M < 1:
        return np.array([])
    if M == 1:
        return np.ones(1, 'd')
    odd = M % 2
    if not sym and not odd:
        M = M + 1
    n = np.arange(0, M)
    w = 0.54 - 0.46 * np.cos(2.0 * np.pi * n / (M - 1))
    if not sym and not odd:
        w = w[:-1]
    return w

def firwin(numtaps, cutoff, width=None, window='hamming', pass_zero=True,
           scale=True, nyq=1.0):
    """
    FIR filter design using the window method.
    This function computes the coefficients of a finite impulse response
    filter.  The filter will have linear phase; it will be Type I if
    `numtaps` is odd and Type II if `numtaps` is even.
    Type II filters always have zero response at the Nyquist rate, so a
    ValueError exception is raised if firwin is called with `numtaps` even and
    having a passband whose right end is at the Nyquist rate.
    Parameters
    ----------
    numtaps : int
        Length of the filter (number of coefficients, i.e. the filter
        order + 1).  `numtaps` must be even if a passband includes the
        Nyquist frequency.
    cutoff : float or 1D array_like
        Cutoff frequency of filter (expressed in the same units as `nyq`)
        OR an array of cutoff frequencies (that is, band edges). In the
        latter case, the frequencies in `cutoff` should be positive and
        monotonically increasing between 0 and `nyq`.  The values 0 and
        `nyq` must not be included in `cutoff`.
    width : float or None, optional
        If `width` is not None, then assume it is the approximate width
        of the transition region (expressed in the same units as `nyq`)
        for use in Kaiser FIR filter design.  In this case, the `window`
        argument is ignored.
    window : string or tuple of string and parameter values, optional
        Desired window to use. See `scipy.signal.get_window` for a list
        of windows and required parameters.
    pass_zero : bool, optional
        If True, the gain at the frequency 0 (i.e. the "DC gain") is 1.
        Otherwise the DC gain is 0.
    scale : bool, optional
        Set to True to scale the coefficients so that the frequency
        response is exactly unity at a certain frequency.
        That frequency is either:
        - 0 (DC) if the first passband starts at 0 (i.e. pass_zero
          is True)
        - `nyq` (the Nyquist rate) if the first passband ends at
          `nyq` (i.e the filter is a single band highpass filter);
          center of first passband otherwise
    nyq : float, optional
        Nyquist frequency.  Each frequency in `cutoff` must be between 0
        and `nyq`.
    Returns
    -------
    h : (numtaps,) ndarray
        Coefficients of length `numtaps` FIR filter.
    Raises
    ------
    ValueError
        If any value in `cutoff` is less than or equal to 0 or greater
        than or equal to `nyq`, if the values in `cutoff` are not strictly
        monotonically increasing, or if `numtaps` is even but a passband
        includes the Nyquist frequency.
    See also
    --------
    scipy.signal.firwin2
    Examples
    --------
    Low-pass from 0 to f:
    >>> from scipy import signal
    >>> numtaps = 3
    >>> f = 0.1
    >>> signal.firwin(numtaps, f)
    array([ 0.06799017,  0.86401967,  0.06799017])
    Use a specific window function:
    >>> signal.firwin(numtaps, f, window='nuttall')
    array([  3.56607041e-04,   9.99286786e-01,   3.56607041e-04])
    High-pass ('stop' from 0 to f):
    >>> signal.firwin(numtaps, f, pass_zero=False)
    array([-0.00859313,  0.98281375, -0.00859313])
    Band-pass:
    >>> f1, f2 = 0.1, 0.2
    >>> signal.firwin(numtaps, [f1, f2], pass_zero=False)
    array([ 0.06301614,  0.88770441,  0.06301614])
    Band-stop:
    >>> signal.firwin(numtaps, [f1, f2])
    array([-0.00801395,  1.0160279 , -0.00801395])
    Multi-band (passbands are [0, f1], [f2, f3] and [f4, 1]):
    >>> f3, f4 = 0.3, 0.4
    >>> signal.firwin(numtaps, [f1, f2, f3, f4])
    array([-0.01376344,  1.02752689, -0.01376344])
    Multi-band (passbands are [f1, f2] and [f3,f4]):
    >>> signal.firwin(numtaps, [f1, f2, f3, f4], pass_zero=False)
    array([ 0.04890915,  0.91284326,  0.04890915])
    """

    # The major enhancements to this function added in November 2010 were
    # developed by Tom Krauss (see ticket #902).

    cutoff = np.atleast_1d(cutoff) / float(nyq)

    # Check for invalid input.
    if cutoff.ndim > 1:
        raise ValueError("The cutoff argument must be at most "
                         "one-dimensional.")
    if cutoff.size == 0:
        raise ValueError("At least one cutoff frequency must be given.")
    if cutoff.min() <= 0 or cutoff.max() >= 1:
        raise ValueError("Invalid cutoff frequency: frequencies must be "
                         "greater than 0 and less than nyq.")
    if np.any(np.diff(cutoff) <= 0):
        raise ValueError("Invalid cutoff frequencies: the frequencies "
                         "must be strictly increasing.")

    if width is not None:
        # A width was given.  Find the beta parameter of the Kaiser window
        # and set `window`.  This overrides the value of `window` passed in.
        atten = kaiser_atten(numtaps, float(width) / nyq)
        beta = kaiser_beta(atten)
        window = ('kaiser', beta)

    pass_nyquist = bool(cutoff.size & 1) ^ pass_zero
    if pass_nyquist and numtaps % 2 == 0:
        raise ValueError("A filter with an even number of coefficients must "
                         "have zero response at the Nyquist rate.")

    # Insert 0 and/or 1 at the ends of cutoff so that the length of cutoff
    # is even, and each pair in cutoff corresponds to passband.
    cutoff = np.hstack(([0.0] * pass_zero, cutoff, [1.0] * pass_nyquist))

    # `bands` is a 2D array; each row gives the left and right edges of
    # a passband.
    bands = cutoff.reshape(-1, 2)

    # Build up the coefficients.
    alpha = 0.5 * (numtaps - 1)
    m = np.arange(0, numtaps) - alpha
    h = 0
    for left, right in bands:
        h += right * np.sinc(right * m)
        h -= left * np.sinc(left * m)

    # Get and apply the window function.
    win = hamming(numtaps, sym=True)
    h *= win

    pdb.set_trace()

    # Now handle scaling if desired.
    if scale:
        # Get the first passband.
        left, right = bands[0]
        if left == 0:
            scale_frequency = 0.0
        elif right == 1:
            scale_frequency = 1.0
        else:
            scale_frequency = 0.5 * (left + right)
        c = np.cos(np.pi * m * scale_frequency)
        s = np.sum(h * c)
        h /= s

    return h
