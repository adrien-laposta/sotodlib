# Copyright (c) 2018-2019 Simons Observatory.
# Full license can be found in the top level "LICENSE" file.
"""Data simulation.

This module contains code for simulating data.

"""


class MakeNoiseData(DataG3Module):
    """
    Writes a signal with just noise. To be used where an observation 
    has already been set up but there's no data (such as the output of 
    so3g.python.quicksim.py) mostly just an easy way to get numbers in G3Timestreams
    
    The noise is a basic white noise plus a 1/f component described by a 
    knee frequency and index
    
    Args:
        input (str): the key to a G3Timestream map in the G3Frame
            to replace with noise data
        output (str or None): key of G3Timestream map of output data
            if None: input will be overwritten with output
        white_noise (float): while noise level
        f_knee (float): knee frequency
        f_knee_index (float): index of 1/f spectrum, should be negative
        
    Returns:
        None
    """
    def __init__(self, input='signal', output=None, white_noise = 24, f_knee = 0.01, f_knee_index=-2):
        self.white_noise = white_noise
        self.f_knee = f_knee
        self.f_knee_index = f_knee_index
        super().__init__(input, output)
    
    def process(self, data, k):
        freqs = np.fft.fftfreq(data.n_samples, core.G3Units.Hz/data.sample_rate)
        noise = self.white_noise*(1 + (freqs[1:]/self.f_knee)**self.f_knee_index)
        noise = noise*np.exp( 1.0j * np.random.uniform(0, 2*np.pi, size=(data.n_samples-1),))
        ## prevent divide by zero error and assume 1/f doesn't go to infinity
        noise = np.append(noise[0], noise)
        return np.real(np.fft.fft(noise)).astype('float64')
            
class MakeJumps(DataG3Module):
    
    """
    G3Module that takes a G3Timestream map and adds randomly 
    distributed jumps
    
    Args:
        input (str): the key to a G3TimestreamMap that is the data source
        output (str or None): the key for a G3TimestreamMap that will have data
            plus glitches. If None: jumps are added to Input
        info (str): a G3Timestream map will be made with this name that 
            includes just the jumps. 
        max_jumps (int): number of jumps in each G3Timestream is 
            np.random.randint(max_jumps)
        height_std_sigma (float): hight of each jump is a draw from a normal 
            distribution with standard deviation of
            height_std_sigma*np.std(timestream)
    """
    
    def __init__(self, input='signal', output=None, info='flags_encoded_jumps', 
                 max_jumps=3, height_std_sigma=10):
        self.info = info
        self.max_jumps = max_jumps
        self.height_std_sigma = height_std_sigma
        super().__init__(input, output)
        
    def __call__(self, f):
        if f.type == core.G3FrameType.Scan:
            self.jump_map = core.G3TimestreamMap()

        super().__call__(f)
            
        if f.type == core.G3FrameType.Scan:
            self.jump_map.start = f[self.input].start
            self.jump_map.stop = f[self.input].stop
            f[self.info] = self.jump_map

    def process(self, data, det_name):
        locs = np.random.randint(data.n_samples, size=(np.random.randint(self.max_jumps),) )
        heights = np.random.randn( len(locs) )*self.height_std_sigma*np.std(data)
        jumps = np.zeros( (data.n_samples,) )
        for i in range(len(locs)):
            jumps[locs[i]:] += heights[i]
    
        self.jump_map[det_name] = core.G3Timestream( jumps )
        return data + jumps

        
class MakeGlitches(DataG3Module):
    """
    G3Module that takes the G3Timestream map and adds randomly 
    distributed glitches
    
    Args:
        input (str): the key to a G3TimestreamMap that is the data source
        output (str or None): the key for a G3TimestreamMap that will have data
            plus glitches. If None: Glitches are added to Input
        info (str): a G3Timestream map will be made with this name that 
            includes just the glitches. 
        max_glitches (int): number of glitches in each G3Timestream is 
            np.random.randint(max_glitches)
        height_std_sigma (float): hight of each jump is a draw from a normal 
            distribution with standard deviation of
            height_std_sigma*np.std(timestream)
    """
    
    def __init__(self, input='signal', output=None, info='flags_encoded_glitches', max_glitches=3, height_std_sigma=20):
        self.info = info
        self.max_glitches = max_glitches
        self.height_std_sigma = height_std_sigma
        super().__init__(input, output)
        
    def __call__(self, f):
        if f.type == core.G3FrameType.Scan:
            self.glitch_map = core.G3TimestreamMap()

        super().__call__(f)
        
        if f.type == core.G3FrameType.Scan:
            self.glitch_map.start = f[self.input].start
            self.glitch_map.stop = f[self.input].stop
            f[self.info] = self.glitch_map
       
    def process(self, data, det_name):
        locs = np.random.randint(data.n_samples, size=(np.random.randint(self.max_glitches),) )
        heights = np.random.randn( len(locs) )*self.height_std_sigma*np.std(data)
        glitches = np.zeros( (data.n_samples,) )
        glitches[locs] += heights
        
        self.glitch_map[det_name] = core.G3Timestream( glitches )
        return core.G3Timestream( data + glitches )