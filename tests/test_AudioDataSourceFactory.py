'''
@author: Amine Sehili <amine.sehili@gmail.com>
September 2015

'''

import unittest
from functools import partial
import sys
from auditok import dataset, ADSFactory, BufferAudioSource, WaveAudioSource, DuplicateArgument
import wave


try:
    from builtins import range
except ImportError:
    if sys.version_info < (3, 0):
        range = xrange

class TestADSFactoryFileAudioSource(unittest.TestCase):
    
    def setUp(self):
        self.audio_source = WaveAudioSource(filename=dataset.one_to_six_arabic_16000_mono_bc_noise)
    
    
    def test_ADS_type(self):
        
        ads = ADSFactory.ads(audio_source=self.audio_source)
        
        self.assertIsInstance(ads, ADSFactory.AudioDataSource,
                              msg="wrong type for ads object, expected: 'ADSFactory.AudioDataSource', found: {0}".format(type(ads)))
        
        
    def test_default_block_size(self):
        ads = ADSFactory.ads(audio_source=self.audio_source)
        size = ads.get_block_size()
        self.assertEqual(size, 160, "Wrong default block_size, expected: 160, found: {0}".format(size))
        
        
    def test_block_size(self):
        ads = ADSFactory.ads(audio_source=self.audio_source, block_size=512)
        size = ads.get_block_size()
        self.assertEqual(size, 512, "Wrong block_size, expected: 512, found: {0}".format(size))
        
        # with alias keyword
        ads = ADSFactory.ads(audio_source=self.audio_source, bs=160)
        size = ads.get_block_size()
        self.assertEqual(size, 160, "Wrong block_size, expected: 160, found: {0}".format(size))
    
    def test_block_duration(self):
        
        ads = ADSFactory.ads(audio_source=self.audio_source, block_dur=0.01) # 10 ms
        size = ads.get_block_size()
        self.assertEqual(size, 160, "Wrong block_size, expected: 160, found: {0}".format(size))
        
        # with alias keyword
        ads = ADSFactory.ads(audio_source=self.audio_source, bd=0.025) # 25 ms
        size = ads.get_block_size()
        self.assertEqual(size, 400, "Wrong block_size, expected: 400, found: {0}".format(size))
        
    def test_hop_duration(self):
        
        ads = ADSFactory.ads(audio_source=self.audio_source, block_dur=0.02, hop_dur=0.01) # 10 ms
        size = ads.hop_size
        self.assertEqual(size, 160, "Wrong hop_size, expected: 160, found: {0}".format(size))
        
        # with alias keyword
        ads = ADSFactory.ads(audio_source=self.audio_source, bd=0.025, hop_dur=0.015) # 15 ms
        size = ads.hop_size
        self.assertEqual(size, 240, "Wrong block_size, expected: 240, found: {0}".format(size))    
        
    
    def test_sampling_rate(self):
        ads = ADSFactory.ads(audio_source=self.audio_source)
        
        srate = ads.get_sampling_rate()
        self.assertEqual(srate, 16000, "Wrong sampling rate, expected: 16000, found: {0}".format(srate))
        
    def test_sample_width(self):
        ads = ADSFactory.ads(audio_source=self.audio_source)
        
        swidth = ads.get_sample_width()
        self.assertEqual(swidth, 2, "Wrong sample width, expected: 2, found: {0}".format(swidth))
    
    def test_channels(self):
        ads = ADSFactory.ads(audio_source=self.audio_source)
        
        channels = ads.get_channels()
        self.assertEqual(channels, 1, "Wrong number of channels, expected: 1, found: {0}".format(channels))
        
    def test_read(self):
        ads = ADSFactory.ads(audio_source=self.audio_source, block_size = 256)
        
        ads.open()
        ads_data = ads.read()
        ads.close()
        
        audio_source = WaveAudioSource(filename=dataset.one_to_six_arabic_16000_mono_bc_noise)
        audio_source.open()
        audio_source_data = audio_source.read(256)
        audio_source.close()
        
        self.assertEqual(ads_data, audio_source_data, "Unexpected data read from ads")
    
    def test_Limiter_Deco_type(self):
        ads = ADSFactory.ads(audio_source=self.audio_source, max_time=1)
        
        self.assertIsInstance(ads, ADSFactory.LimiterADS,
                              msg="wrong type for ads object, expected: 'ADSFactory.LimiterADS', found: {0}".format(type(ads)))
         
    
    def test_Limiter_Deco_read(self):
        # read a maximum of 0.75 seconds from audio source
        ads = ADSFactory.ads(audio_source=self.audio_source, max_time=0.75)
        
        ads_data = []
        ads.open()
        while True:
            block = ads.read()
            if block is None:
                break
            ads_data.append(block)
        ads.close()
        ads_data = b''.join(ads_data)    
                    
        audio_source = WaveAudioSource(filename=dataset.one_to_six_arabic_16000_mono_bc_noise)
        audio_source.open()
        audio_source_data = audio_source.read(int(16000 * 0.75))
        audio_source.close()
        
        self.assertEqual(ads_data, audio_source_data, "Unexpected data read from LimiterADS")
        
        
    def test_Limiter_Deco_read_limit(self):
        # read a maximum of 1.25 seconds from audio source
        ads = ADSFactory.ads(audio_source=self.audio_source, max_time=1.191)
        
        # desired duration into bytes is obtained by:
        # max_time * sampling_rate * sample_width * nb_channels
        # Limiter deco tries to a total quantity of data as
        # possible to the desired duration in bytes.   
        # It reads N block of size block_size where:
        # (N - 1) * block_size < desired duration, AND
        # N * block_size >= desired duration
        
        # theoretical size to reach          
        expected_size = int(ads.get_sampling_rate() * 1.191) * \
                       ads.get_sample_width() * ads.get_channels()
        
        
        # how much data are required to get N blocks of size block_size
        block_size_bytes = ads.get_block_size() * ads.get_sample_width() * ads.get_channels()
        r = expected_size % block_size_bytes
        if r > 0:
            expected_size += block_size_bytes - r
        
        total_read = 0
        ads.open()
        i = 0
        while True:
            block = ads.read()
            if block is None:
                break
            i += 1
            total_read += len(block)
        
        ads.close()
            
        self.assertEqual(total_read, expected_size, "Wrong data length read from LimiterADS, expected: {0}, found: {1}".format(expected_size, total_read))
        
        
        
    def test_Recorder_Deco_type(self):
        ads = ADSFactory.ads(audio_source=self.audio_source, record=True)
        
        self.assertIsInstance(ads, ADSFactory.RecorderADS,
                              msg="wrong type for ads object, expected: 'ADSFactory.RecorderADS', found: {0}".format(type(ads)))
         
        
    def test_Recorder_Deco_read(self):
        ads = ADSFactory.ads(audio_source=self.audio_source, record=True, block_size=500)
        
        ads_data = []
        ads.open()
        for i in range(10):
            block = ads.read()
            if block is None:
                break
            ads_data.append(block)
        ads.close()
        ads_data = b''.join(ads_data)    
                    
        audio_source = WaveAudioSource(filename=dataset.one_to_six_arabic_16000_mono_bc_noise)
        audio_source.open()
        audio_source_data = audio_source.read(500 * 10)
        audio_source.close()
        
        self.assertEqual(ads_data, audio_source_data, "Unexpected data read from RecorderADS")
        
    def test_Recorder_Deco_is_rewindable(self):
        ads = ADSFactory.ads(audio_source=self.audio_source, record=True)
        
        self.assertTrue(ads.is_rewindable(), "RecorderADS.is_rewindable should return True")
        
    
    def test_Recorder_Deco_rewind(self):
        ads = ADSFactory.ads(audio_source=self.audio_source, record=True, block_size = 320)
        
        ads.open()
        ads.read()
        ads.rewind()
        
        
        self.assertIsInstance(ads.get_audio_source(), 
                              BufferAudioSource, "After rewind RecorderADS.get_audio_source should \
                              be an instance of BufferAudioSource")
        ads.close()
        
        
    def test_Recorder_Deco_rewind_and_read(self):
        ads = ADSFactory.ads(audio_source=self.audio_source, record=True, block_size = 320)
        
        ads.open()
        for i in range(10):
            ads.read()
            
        ads.rewind()
        
        # read all available data after rewind
        ads_data = []
        while True:
            block = ads.read()
            if block is None:
                break
            ads_data.append(block)
        ads.close()
        ads_data = b''.join(ads_data)    
                    
        audio_source = WaveAudioSource(filename=dataset.one_to_six_arabic_16000_mono_bc_noise)
        audio_source.open()
        audio_source_data = audio_source.read(320 * 10)
        audio_source.close()
        
        self.assertEqual(ads_data, audio_source_data, "Unexpected data read from RecorderADS")
    
    def test_Overlap_Deco_type(self):
        # an OverlapADS is obtained if a valid hop_size is given
        ads = ADSFactory.ads(audio_source=self.audio_source, block_size = 256, hop_size = 128)
        
        self.assertIsInstance(ads, ADSFactory.OverlapADS,
                              msg="wrong type for ads object, expected: 'ADSFactory.OverlapADS', found: {0}".format(type(ads)))
         
        
        
    
    def test_Overlap_Deco_read(self):
        
        # Use arbitrary valid block_size and hop_size
        block_size = 1714
        hop_size = 313
        
        ads = ADSFactory.ads(audio_source=self.audio_source, block_size=block_size, hop_size=hop_size)
        
        # Read all available data overlapping blocks
        ads.open()
        ads_data = []
        while True:
            block = ads.read()
            if block is None:
                break
            ads_data.append(block)
        ads.close()
        
        # Read all data from file and build a BufferAudioSource
        fp = wave.open(dataset.one_to_six_arabic_16000_mono_bc_noise, "r")
        wave_data = fp.readframes(fp.getnframes())
        fp.close()
        audio_source = BufferAudioSource(wave_data, ads.get_sampling_rate(),
                                         ads.get_sample_width(), ads.get_channels())
        audio_source.open()
        
        # Compare all blocks read from OverlapADS to those read
        # from an audio source with a manual set_position
        for i,block in enumerate(ads_data):
            
            tmp = audio_source.read(block_size)
            
            self.assertEqual(block, tmp, "Unexpected block (N={0}) read from OverlapADS".format(i))
            
            audio_source.set_position((i+1) * hop_size)
        
        audio_source.close()
    
    
            
            
    def test_Limiter_Overlap_Deco_type(self):
        ads = ADSFactory.ads(audio_source=self.audio_source, max_time=1, block_size = 256, hop_size = 128)
        
        self.assertIsInstance(ads, ADSFactory.OverlapADS,
                            msg="wrong type for ads object, expected: 'ADSFactory.OverlapADS', found: {0}".format(type(ads)))
         
        
        self.assertIsInstance(ads.ads, ADSFactory.LimiterADS,
                              msg="wrong type for ads object, expected: 'ADSFactory.LimiterADS', found: {0}".format(type(ads)))
           
        
        
    def test_Limiter_Overlap_Deco_read(self):    
        
        block_size = 256
        hop_size = 200
        
        ads = ADSFactory.ads(audio_source=self.audio_source, max_time=0.50, block_size=block_size, hop_size=hop_size)
        
        # Read all available data overlapping blocks
        ads.open()
        ads_data = []
        while True:
            block = ads.read()
            if block is None:
                break
            ads_data.append(block)
        ads.close()
        
        # Read all data from file and build a BufferAudioSource
        fp = wave.open(dataset.one_to_six_arabic_16000_mono_bc_noise, "r")
        wave_data = fp.readframes(fp.getnframes())
        fp.close()
        audio_source = BufferAudioSource(wave_data, ads.get_sampling_rate(),
                                         ads.get_sample_width(), ads.get_channels())
        audio_source.open()
        
        # Compare all blocks read from OverlapADS to those read
        # from an audio source with a manual set_position
        for i,block in enumerate(ads_data):            
            tmp = audio_source.read(block_size)
            
            self.assertEqual(block, tmp, "Unexpected block (N={0}) read from OverlapADS".format(i))
            
            audio_source.set_position((i+1) * hop_size)
        
        audio_source.close()
    
        
        
    def test_Limiter_Overlap_Deco_read_limit(self):
        
        block_size = 313
        hop_size = 207
        ads = ADSFactory.ads(audio_source=self.audio_source,
                             max_time=1.932, block_size=block_size,
                             hop_size=hop_size)
        
        # Limiter + Overlap decos => read N block of actual data
        # one block of size block_size
        # N - 1 blocks of size hop_size
        # the total size of read data might be a slightly greater
        # than the required size calculated from max_time
        
        # theoretical size to reach          
        expected_size = int(ads.get_sampling_rate() * 1.932) * \
                       ads.get_sample_width() * ads.get_channels()
        
        # minus block_size
        expected_size -= (block_size * ads.get_sample_width() * ads.get_channels())
        
        # how much data are required to get N - 1 blocks of size hop_size
        hop_size_bytes = hop_size * ads.get_sample_width() * ads.get_channels()
        r = expected_size % hop_size_bytes
        if r > 0:
            expected_size += hop_size_bytes - r
        
        expected_size += block_size * ads.get_sample_width() * ads.get_channels()
        
        cache_size = (block_size - hop_size) * ads.get_sample_width() * ads.get_channels()
        total_read = cache_size
        
        ads.open()
        i = 0
        while True:
            block = ads.read()
            if block is None:
                break
            i += 1
            total_read += len(block) - cache_size
        
        ads.close()
        self.assertEqual(total_read, expected_size, "Wrong data length read from LimiterADS, expected: {0}, found: {1}".format(expected_size, total_read))
        
        
        
    def test_Recorder_Overlap_Deco_type(self):
        ads = ADSFactory.ads(audio_source=self.audio_source, block_size=256, hop_size=128, record=True)
        
        self.assertIsInstance(ads, ADSFactory.OverlapADS,
                            msg="wrong type for ads object, expected: 'ADSFactory.OverlapADS', found: {0}".format(type(ads)))
         
        
        self.assertIsInstance(ads.ads, ADSFactory.RecorderADS,
                              msg="wrong type for ads object, expected: 'ADSFactory.RecorderADS', found: {0}".format(type(ads)))
               
    
        
    def test_Recorder_Overlap_Deco_is_rewindable(self):
        ads = ADSFactory.ads(audio_source=self.audio_source, block_size=320, hop_size=160, record=True)
        self.assertTrue(ads.is_rewindable(), "RecorderADS.is_rewindable should return True")
        

    def test_Recorder_Overlap_Deco_rewind_and_read(self):
        
        # Use arbitrary valid block_size and hop_size
        block_size = 1600
        hop_size = 400
        
        ads = ADSFactory.ads(audio_source=self.audio_source, block_size=block_size, hop_size=hop_size, record=True)
        
        # Read all available data overlapping blocks
        ads.open()
        i = 0
        while True:
            block = ads.read()
            if block is None:
                break
            i += 1
        
        ads.rewind()
        
        # Read all data from file and build a BufferAudioSource
        fp = wave.open(dataset.one_to_six_arabic_16000_mono_bc_noise, "r")
        wave_data = fp.readframes(fp.getnframes())
        fp.close()
        audio_source = BufferAudioSource(wave_data, ads.get_sampling_rate(),
                                         ads.get_sample_width(), ads.get_channels())
        audio_source.open()
        
        # Compare all blocks read from OverlapADS to those read
        # from an audio source with a manual set_position
        for j in range(i):
            
            tmp = audio_source.read(block_size)
            
            self.assertEqual(ads.read(), tmp, "Unexpected block (N={0}) read from OverlapADS".format(i))
            audio_source.set_position((j+1) * hop_size)
        
        ads.close()
        audio_source.close()
    
    
    def test_Limiter_Recorder_Overlap_Deco_rewind_and_read(self):
        
        # Use arbitrary valid block_size and hop_size
        block_size = 1600
        hop_size = 400
        
        ads = ADSFactory.ads(audio_source=self.audio_source, max_time = 1.50, block_size=block_size, hop_size=hop_size, record=True)
        
        # Read all available data overlapping blocks
        ads.open()
        i = 0
        while True:
            block = ads.read()
            if block is None:
                break
            i += 1
        
        ads.rewind()
        
        # Read all data from file and build a BufferAudioSource
        fp = wave.open(dataset.one_to_six_arabic_16000_mono_bc_noise, "r")
        wave_data = fp.readframes(fp.getnframes())
        fp.close()
        audio_source = BufferAudioSource(wave_data, ads.get_sampling_rate(),
                                         ads.get_sample_width(), ads.get_channels())
        audio_source.open()
        
        # Compare all blocks read from OverlapADS to those read
        # from an audio source with a manual set_position
        for j in range(i):
            
            tmp = audio_source.read(block_size)
            
            self.assertEqual(ads.read(), tmp, "Unexpected block (N={0}) read from OverlapADS".format(i))
            audio_source.set_position((j+1) * hop_size)
        
        ads.close()
        audio_source.close()
    
    
    def test_Limiter_Recorder_Overlap_Deco_rewind_and_read_limit(self):
        
        # Use arbitrary valid block_size and hop_size
        block_size = 1000
        hop_size = 200
        
        ads = ADSFactory.ads(audio_source=self.audio_source, max_time = 1.317, block_size=block_size, hop_size=hop_size, record=True)
        
        # Limiter + Overlap decos => read N block of actual data
        # one block of size block_size
        # N - 1 blocks of size hop_size
        # the total size of read data might be a slightly greater
        # than the required size calculated from max_time
        
        # theoretical size to reach          
        expected_size = int(ads.get_sampling_rate() * 1.317) * \
                       ads.get_sample_width() * ads.get_channels()
        
        # minus block_size
        expected_size -= (block_size * ads.get_sample_width() * ads.get_channels())
        
        # how much data are required to get N - 1 blocks of size hop_size
        hop_size_bytes = hop_size * ads.get_sample_width() * ads.get_channels()
        r = expected_size % hop_size_bytes
        if r > 0:
            expected_size += hop_size_bytes - r
        
        expected_size += block_size * ads.get_sample_width() * ads.get_channels()
        
        cache_size = (block_size - hop_size) * ads.get_sample_width() * ads.get_channels()
        total_read = cache_size
        
        ads.open()
        i = 0
        while True:
            block = ads.read()
            if block is None:
                break
            i += 1
            total_read += len(block) - cache_size
        
        ads.close()
        self.assertEqual(total_read, expected_size, "Wrong data length read from LimiterADS, expected: {0}, found: {1}".format(expected_size, total_read))
        
class TestADSFactoryBufferAudioSource(unittest.TestCase):
    
    def setUp(self):
        self.signal = "ABCDEFGHIJKLMNOPQRSTUVWXYZ012345"
        self.ads = ADSFactory.ads(data_buffer=self.signal, sampling_rate=16,
                             sample_width=2, channels=1)
        
    def test_ADS_BAS_type(self):
        self.assertIsInstance(self.ads.get_audio_source(), 
                              BufferAudioSource, "ads should \
                              be an instance of BufferAudioSource")
    
    def test_ADS_BAS_sampling_rate(self):
        srate = self.ads.get_sampling_rate()
        self.assertEqual(srate, 16, "Wrong sampling rate, expected: 16000, found: {0}".format(srate))
      
        
    def test_ADS_BAS_get_sample_width(self):
        swidth = self.ads.get_sample_width()
        self.assertEqual(swidth, 2, "Wrong sample width, expected: 2, found: {0}".format(swidth))
    
    def test_ADS_BAS_get_channels(self):
        channels = self.ads.get_channels()
        self.assertEqual(channels, 1, "Wrong number of channels, expected: 1, found: {0}".format(channels))
        
    def test_Limiter_Recorder_Overlap_Deco_rewind_and_read(self):
        
        # Use arbitrary valid block_size and hop_size
        block_size = 5
        hop_size = 4
        
        ads = ADSFactory.ads(data_buffer=self.signal, sampling_rate=16,
                             sample_width=2, channels=1, max_time = 0.80,
                             block_size=block_size, hop_size=hop_size,
                             record=True)
        
        # Read all available data overlapping blocks
        ads.open()
        i = 0
        while True:
            block = ads.read()
            if block is None:
                break
            i += 1
        
        ads.rewind()
        
        # Build a BufferAudioSource
        audio_source = BufferAudioSource(self.signal, ads.get_sampling_rate(),
                        ads.get_sample_width(), ads.get_channels())
        audio_source.open()
        
        # Compare all blocks read from OverlapADS to those read
        # from an audio source with a manual set_position
        for j in range(i):
            
            tmp = audio_source.read(block_size)
            
            block = ads.read()
            
            self.assertEqual(block, tmp, "Unexpected block (N={0}) read from OverlapADS".format(i))
            audio_source.set_position((j+1) * hop_size)
        
        ads.close()
        audio_source.close()


class TestADSFactoryAlias(unittest.TestCase):
    
    def setUp(self):
        self.signal = "ABCDEFGHIJKLMNOPQRSTUVWXYZ012345"
    
    def test_sampling_rate_alias(self):
        ads = ADSFactory.ads(data_buffer=self.signal, sr=16,
                             sample_width=2, channels=1)
        srate = ads.get_sampling_rate()
        self.assertEqual(srate, 16, "Wrong sampling rate, expected: 16000, found: {0}".format(srate))
    
    def test_sampling_rate_duplicate(self):
        func = partial(ADSFactory.ads, data_buffer=self.signal, sr=16, sampling_rate=16,
                             sample_width=2, channels=1)
        self.assertRaises(DuplicateArgument, func)
    
    def test_sample_width_alias(self):
        ads = ADSFactory.ads(data_buffer=self.signal, sampling_rate=16,
                             sw=2, channels=1)
        swidth = ads.get_sample_width()
        self.assertEqual(swidth, 2, "Wrong sample width, expected: 2, found: {0}".format(swidth))
    
    def test_sample_width_duplicate(self):
        func = partial(ADSFactory.ads, data_buffer=self.signal,sampling_rate=16,
                             sw=2, sample_width=2, channels=1)
        self.assertRaises(DuplicateArgument, func)
        
    def test_channels_alias(self):
        ads = ADSFactory.ads(data_buffer=self.signal, sampling_rate=16,
                             sample_width=2, ch=1)
        channels = ads.get_channels()
        self.assertEqual(channels, 1, "Wrong number of channels, expected: 1, found: {0}".format(channels))
    
    def test_channels_duplicate(self):
        func = partial(ADSFactory.ads, data_buffer=self.signal,sampling_rate=16,
                             sample_width=2, ch=1, channels=1)
        self.assertRaises(DuplicateArgument, func)
    
    
    def test_block_size_alias(self):
        ads = ADSFactory.ads(data_buffer=self.signal, sampling_rate=16,
                             sample_width=2, channels=1, bs=8)
        size = ads.get_block_size()
        self.assertEqual(size, 8, "Wrong block_size using bs alias, expected: 8, found: {0}".format(size))
        
    def test_block_size_duplicate(self):
        func = partial(ADSFactory.ads, data_buffer=self.signal,sampling_rate=16,
                             sample_width=2, channels=1, bs=4, block_size=4)
        self.assertRaises(DuplicateArgument, func)
    
    def test_block_duration_alias(self):
        ads = ADSFactory.ads(data_buffer=self.signal, sampling_rate=16,
                             sample_width=2, channels=1, bd=0.75)
        # 0.75 ms = 0.75 * 16 = 12
        size = ads.get_block_size()
        self.assertEqual(size, 12, "Wrong block_size set with a block_dur alias 'bd', expected: 8, found: {0}".format(size))
        
    def test_block_duration_duplicate(self):
        func = partial(ADSFactory.ads, data_buffer=self.signal,sampling_rate=16,
                             sample_width=2, channels=1, bd=4, block_dur=4)
        self.assertRaises(DuplicateArgument, func)
        
    def test_block_size_duration_duplicate(self):
        func = partial(ADSFactory.ads, data_buffer=self.signal,sampling_rate=16,
                             sample_width=2, channels=1, bd=4, bs=12)
        self.assertRaises(DuplicateArgument, func)
        
    def test_hop_duration_alias(self):
        
        ads = ADSFactory.ads(data_buffer=self.signal, sampling_rate=16,
                             sample_width=2, channels=1, bd=0.75, hd=0.5 )
        size = ads.hop_size
        self.assertEqual(size, 8, "Wrong block_size using bs alias, expected: 8, found: {0}".format(size))
        self.assertIsInstance(ads, ADSFactory.OverlapADS, "ads expected to an ADSFactory.OverlapADS object")
    
    
    def test_hop_duration_duplicate(self):
        
        func = partial(ADSFactory.ads, data_buffer=self.signal, sampling_rate=16,
                             sample_width=2, channels=1, bd=0.75, hd=0.5, hop_dur=0.5)
        self.assertRaises(DuplicateArgument, func)
    
    
    def test_hop_size_duration_duplicate(self):
        func = partial(ADSFactory.ads, data_buffer=self.signal,sampling_rate=16,
                             sample_width=2, channels=1, bs=8, hs=4, hd=1)
        self.assertRaises(DuplicateArgument, func)
    
    
    def test_hop_size_greater_than_block_size(self):
        func = partial(ADSFactory.ads, data_buffer=self.signal, sampling_rate=16,
                             sample_width=2, channels=1, bs=4, hs=8)
        self.assertRaises(ValueError, func)
        
    
    def test_filename_alias(self):
        ads = ADSFactory.ads(fn=dataset.one_to_six_arabic_16000_mono_bc_noise)
    
    
    def test_filename_duplicate(self):
        
        func = partial(ADSFactory.ads, fn=dataset.one_to_six_arabic_16000_mono_bc_noise, filename=dataset.one_to_six_arabic_16000_mono_bc_noise)
        self.assertRaises(DuplicateArgument, func)
    
    
    def test_data_buffer_alias(self):
        ads = ADSFactory.ads(db=self.signal, sampling_rate=16,
                             sample_width=2, channels=1)
        self.assertEqual(ads.get_audio_source().get_data_buffer(), self.signal, "Wrong value for data buffer")
    
    
    def test_data_buffer_duplicate(self):
        func = partial(ADSFactory.ads, data_buffer=self.signal, db=self.signal, sampling_rate=16,
                             sample_width=2, channels=1)
        self.assertRaises(DuplicateArgument, func)
        
    
    def test_max_time_alias(self):
        ads = ADSFactory.ads(data_buffer=self.signal, sampling_rate=16,
                             sample_width=2, channels=1, mt=10)
        self.assertIsInstance(ads, ADSFactory.LimiterADS, "ads expected to an ADSFactory.LimiterADS object")
    
    
    def test_max_time_duplicate(self):
        func = partial(ADSFactory.ads, data_buffer=self.signal, sampling_rate=16,
                             sample_width=2, channels=1, mt=True, max_time=True)
        
        self.assertRaises(DuplicateArgument, func)
    
    def test_record_alias(self):
        ads = ADSFactory.ads(data_buffer=self.signal, sampling_rate=16,
                             sample_width=2, channels=1, rec=True)
        self.assertIsInstance(ads, ADSFactory.RecorderADS, "ads expected to an ADSFactory.RecorderADS object")
    
    
    def test_record_duplicate(self):
        func = partial(ADSFactory.ads, data_buffer=self.signal, sampling_rate=16,
                             sample_width=2, channels=1, rec=True, record=True)
        self.assertRaises(DuplicateArgument, func)
      
      
    def test_Limiter_Recorder_Overlap_Deco_rewind_and_read_alias(self):
        
        # Use arbitrary valid block_size and hop_size
        block_size = 5
        hop_size = 4
        
        ads = ADSFactory.ads(db=self.signal, sr=16,
                             sw=2, ch=1, mt = 0.80,
                             bs=block_size, hs=hop_size,
                             rec=True)
        
        # Read all available data overlapping blocks
        ads.open()
        i = 0
        while True:
            block = ads.read()
            if block is None:
                break
            i += 1
        
        ads.rewind()
        
        # Build a BufferAudioSource
        audio_source = BufferAudioSource(self.signal, ads.get_sampling_rate(),
                        ads.get_sample_width(), ads.get_channels())
        audio_source.open()
        
        # Compare all blocks read from OverlapADS to those read
        # from an audio source with a manual set_position
        for j in range(i):
            
            tmp = audio_source.read(block_size)
            
            block = ads.read()
            
            self.assertEqual(block, tmp, "Unexpected block (N={0}) read from OverlapADS".format(i))
            audio_source.set_position((j+1) * hop_size)
        
        ads.close()
        audio_source.close()
    

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
