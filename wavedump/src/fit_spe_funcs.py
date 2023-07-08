from __future__ import print_function, division
import h5py
import numpy as np
from scipy.stats import poisson
import sys
import csv
import os
import ROOT
from ROOT import gROOT
from ROOT import TMath

# DEFAULT VALUES FOR SPE FIT:
D_OFFSET = 0
D_LAMBDA = 0.5
D_SPE_CHARGE = 0.8
D_NOISE_SPREAD = 0.01
D_SPE_CHARGE_SPREAD = 0
D_ZERO_PEAK_SPREAD = 0.4
# Number of peaks we use for SPE fitting
num_peaks = 20

ROOT_FUNC = "[0]*(" + "+".join(["TMath::Poisson(%i,[2])*TMath::Gaus(x-[1],[3]*%i,TMath::Sqrt([4]^2+[5]^2*%i))" % (i,i,i) for i in range(0,num_peaks)]) + ")"

def iqr(h):
    probSum = np.array([0.25, 0.75], dtype=np.double)
    q = np.zeros(2, dtype=np.double)
    h.GetQuantiles(2, q, probSum)
    return q[1] - q[0]

def analyze_filter_data(h, f_h):
    """
    Fits the filtered charge histogram `f_h` with a gaussian, and gets the mean
    and standard  deviation of this gaussian: `f_m` and `f_std`.
    
    Then, fits `h` (the unfiltered charge histogram) with a gaussian around
    `f_m`, and gets the mean, standard deviation, and scale of this gaussian:
    `m`, `std`, `scale`.

    Returns `(m, f_std, std, scale)`
    """
    filter_fit = ROOT.TF1('filter_fit', 'gaus', f_h.GetMean() - 2*f_h.GetStdDev(), f_h.GetMean() + 2*f_h.GetStdDev())
    f_h.Fit(filter_fit, 'SRQ0')
    # The mean of the filtered charges should be approximately zero,
    # independent of any baseline, but still good to initialize it like this.
    offset = filter_fit.GetParameter(1)
    # The filtered charges should in principle model integrating over pure
    # noise, so the std.'s should be similar.
    noise_spread = filter_fit.GetParameter(2)

    f_h.Write()
    
    # The noise spread is usually very small compared to the width of the zero
    # peak, so scaling it up by 15 is enough capture enough of the zero peak.
    win = max(0.3, 15*noise_spread)
    means = []
    raw_fit = ROOT.TF1('raw_fit', 'gaus', offset - win, offset + win)
    raw_fit.SetParameter(1, offset)
    raw_fit.SetParameter(2, noise_spread)

    diff = 1
    count = 0
    while diff > 0.001 and count < 5:
        if offset-win < h.GetXaxis().GetXmin() or offset+win > h.GetXaxis().GetXmax():
            print('Filtered data could not find first peak!')
            return None
        raw_fit.SetRange(offset-win, offset+win)
        h.Fit(raw_fit, 'SRQ')
        diff = np.abs(raw_fit.GetParameter(1) - offset)
        offset = raw_fit.GetParameter(1)
        means.append(offset)
        count += 1
    
    if diff > 0.001:
        offset = np.mean(means)
        if offset-win < h.GetMinimum() or offset+win > h.GetMaximum():
            print('Filtered data could not find first peak!')
            return None
        raw_fit.SetRange(offset-win, offset+win)
        h.Fit(raw_fit, 'SRQ')
        offset = raw_fit.GetParameter(1)
    raw_spread = raw_fit.GetParameter(2)
    scale = raw_fit.GetParameter(0)
    return (offset, noise_spread, raw_spread, scale)

def get_bin_num(h, val):
    """
    Gets the bin number of `val` if `val` was placed into the histogram `h`.
    Does NOT add `val` to `h`.
    """
    return h.GetXaxis().FindBin(val)

class poisson_model:
    """
    p[0]: overall scale
    p[1]: offset
    p[2]: mean number of SPEs in integration window
    p[3]: SPE charge
    p[4]: std. of scope/digitizer noise
    p[5]: std. of SPE charge
    """
    def __call__(self, x, p):
        # Original model in root syntax:
        # string = "[0]*(" + "+".join(["TMath::Poisson(%i,[2])*TMath::Gaus(x-[1],[3]*%i,TMath::Sqrt([4]^2+[5]^2*%i))" % (i,i,i) for i in range(0,n)]) + ")"
        
        model = 0
        for i in range(num_peaks):
            model += TMath.Poisson(i, p[2]) * TMath.Gaus(x[0]-p[1], i*p[3], TMath.Sqrt(p[4]**2 + i*(p[5]**2)), False)
        model *= p[0]
        return model

def fac(x):
    """
    Returns x!. We use the gamma function here instead since it works even for
    non-integer values and is generally faster than calling math.factorial(x).
    """
    return np.math.gamma(x+1)

def vinogradov(N, l, ps):
    """
    Returns probability of getting `N` PEs in the integration window.  `l` is
    the mean number of primary PEs.  `ps` is the probability that a primary PE
    causes a secondary PE.  See this paper for a more detailed explanation:
    https://arxiv.org/pdf/2106.13168.pdf
    """
    model = 0
    for i in range(N+1):
        model += B_coeff(i, N) * (l*(1-ps))**i * ps**(N-i)
    model *= np.exp(-l)
    model /= fac(N)
    return model

def B_coeff(i, N):
    """
    Helper function for the vinogradov model.
    """
    if i == 0 and N == 0:
        return 1
    elif i == 0 and N > 0:
        return 0
    else:
        return (fac(N)*fac(N-1)) / (fac(i)*fac(i-1)*fac(N-i))

class vinogradov_model:
    """
    We assume that each photoelectron (PE) peak is gaussian. We add the PE
    distributions together, each weighted by a probability given by
    `vinogradov`. The whole distribution is then convolved with a single
    gaussian to model the noise of the signal.
    
    p[0]: overall scale
    p[1]: offset
    p[2]: mean number of SPEs in integration window
    p[3]: SPE charge
    p[4]: std. of scope/digitizer noise
    p[5]: std. of SPE charge
    p[6]: probability that a primary PE triggers a secondary PE (https://arxiv.org/pdf/2106.13168.pdf)
    """
    def __call__(self, x, p):
        model = 0
        for i in range(num_peaks):
            model += vinogradov(i, p[2], p[6]) * TMath.Gaus(x[0]-p[1], i*p[3], TMath.Sqrt(p[4]**2 + i*(p[5]**2)), False)
        model *= p[0]
        return model

def plot_dists():
    """
    Plots the poisson and vinogradov distributions, then exits on user input.
    """
    l = 0.5
    ps = 0.9
    x = np.arange(20)
    y_p = [np.exp(-l) * (l**i)/fac(i) for i in x]
    y_v = [vinogradov(i, l, ps) for i in x]
    print(f'poisson sum: {np.sum(y_p)}')
    print(f'vino sum: {np.sum(y_v)}')
    plt.figure()
    plt.bar(x-0.2, y_p, width=0.4, label='poisson')
    plt.bar(x+0.2, y_v, width=0.4, label='vino')
    plt.legend()
    plt.show()
    input()
    exit()

def fit_spe(h, model, f_h=None, root_func=False):
    """ 
    SPE Fitting Strategy
    
    1. We use a 7 parameter model to fit the SPE charge histogram.
       See `vinogradov_model` in this module for an explanation.
    
    2. Each SPE histogram should have a corresponding filtered
       charge histogram. It's created the same way, except with the
       signal passed through a digital high pass filter. See
       `analyze-waveforms` to see how this is done.
    
    3. From the filtered histogram, we estimate the voltage
       offset, std. of the noise, std. of the zero peak, and the
       overall scale (see `analyze_filter_data` in this module).
    
    4. We estimate the average number of SPEs in the integration
       window (`l`) as follows:
       4.1. Count all the entries in the zero peak
       4.2. Divide by total entries, giving probability that there
            are no SPEs in the integration window: P(no SPEs).
       4.3. The vinogradov distribution is approximately poisson.
            Since a poisson distribution only depends on its mean,
            having P(no SPEs) gives us `l`.
    
    5. The SPE charge (mu) is estimated using this equation:
       h.GetMean() = P(no SPEs)*(offset) + P(1 SPE)*(mu + offset) + P(2 SPEs)*(2*mu + offset) + ...
    
    6. Two fits are preformed. The first fit keeps several
       parameters fixed so that we get distinguishable peaks. The
       second fit releases most parameters to preform a final, clean
       fit of everything. Exactly which parameters get fixed or
       relased is still under active development as of the time of
       this comment: Aug. 5, 2022.
    Older than June 2022:
        *** we could set a threshold/break to find when the Y axis /charge goes above a certain values from the smallest X to set the first value (-0.4 as of the time of this comment)
    """
    filter_output = None
    if f_h:
        print('Using filtered data!')
        filter_output = analyze_filter_data(h, f_h)
    if filter_output == None:
        offset = D_OFFSET
        noise_spread = D_NOISE_SPREAD
        raw_spread = D_ZERO_PEAK_SPREAD
        scale = h.GetEntries()*0.075
    else:
        offset, noise_spread, raw_spread, scale = filter_output
    
    # Probability that an SPE trigger a secondary SPE
    ps = 0

    # `l`, short for lambda, which is the average number of PEs measured in the integration window.
    zero_peak_end = offset + 2 * raw_spread
    print(f'zero_peak_end: {zero_peak_end}')
    num_zero = h.Integral(0, get_bin_num(h, zero_peak_end))
    prob_zero = num_zero / h.GetEntries()
    if prob_zero <= 0 or prob_zero >= 1:
        l = D_LAMBDA
    else:
        l = -np.log(prob_zero)
    # The scale of the first peak (what `scale` is now) is equal to the scale
    # for our model times the first vinogradov term:
    scale /= vinogradov(0, l, ps)
    
    num_peaks = min(20, max(4, poisson.ppf(0.95, l)))

    # SPE Charge estimated using the method from this forum:
    # https://math.stackexchange.com/questions/3689141/calculating-the-mean-and-standard-deviation-of-a-gaussian-mixture-model-of-two-c
    SPE_charge = h.GetMean()
    SPE_charge -= offset * sum([vinogradov(i, l, ps) for i in range(num_peaks)])
    SPE_charge /= sum([vinogradov(i, l, ps) * i for i in range(num_peaks)])
    SPE_charge = min(4, SPE_charge)
    SPE_charge = max(zero_peak_end - offset, SPE_charge)

    if root_func:
        f1 = ROOT.TF1("f1", string, offset - 1.5*raw_spread, offset + 5*h.GetStdDev())
    else:
        # Number of parameters must be specified when using a python function
        f1 = ROOT.TF1("f1", model, offset - 1.5*raw_spread, offset + 5*h.GetStdDev(), 7)

    f1.FixParameter(0, scale)
    # f1.SetParameter(0, scale)
    # f1.SetParLimits(0, scale*0.1, scale * 100)

    f1.FixParameter(1, offset)

    f1.SetParameter(2, l)
    f1.SetParLimits(2, 0, num_peaks+5)

    f1.SetParameter(3, SPE_charge)
    f1.SetParLimits(3, zero_peak_end - offset, SPE_charge + 1)
    f1.FixParameter(4, raw_spread)
    
    f1.FixParameter(5, D_SPE_CHARGE_SPREAD)
    
    f1.FixParameter(6, ps)
    
    for i in range(6):
        print(f'[{i}]: {f1.GetParameter(i)}')
    
    r = h.Fit(f1, 'SRB+')

    for i in range(7):
        f1.ReleaseParameter(i)

    f1.FixParameter(1, f1.GetParameter(1)) 
    f1.SetParLimits(2, max(0, f1.GetParameter(2) - 1), f1.GetParameter(2) + 1)
    f1.SetParLimits(3, max(zero_peak_end-offset, f1.GetParameter(3) - 1), f1.GetParameter(3) + 1)
    f1.SetParLimits(4, 0, f1.GetParameter(4) + 0.1) 
    f1.SetParLimits(5, 0, f1.GetParameter(5) + 0.1) 
    f1.SetParLimits(6, 0, 0.25)
    
    f1.SetLineColor(3)
    r = h.Fit(f1, 'SR+')
    r = r.Get()
    if not r.IsValid():
        # Maybe we want to return `None` here?
        print("Fit error!")
    
    h.SetAxisRange(-4, 6, "X")
    h.Write()

    return (f1.GetParameter(3), f1.GetParError(3))
