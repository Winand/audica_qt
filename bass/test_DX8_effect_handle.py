# Copyright(c) Max Kolosov 2011 maxkolosov@inbox.ru
# http://vosolok2008.narod.ru
# BSD license


from pybass import *

if not BASS_Init(-1, 44100, 0, 0, 0):
	print 'BASS_Init error', get_error_description(BASS_ErrorGetCode())
else:
	channelHandle = BASS_StreamCreateFile(False, 'test.ogg', 0, 0, 0)
	DX8_effect_handle = BASS_ChannelSetFX(channelHandle, BASS_FX_DX8_REVERB ,0)
	print('DX8 effect handle', DX8_effect_handle)
	params = BASS_DX8_REVERB()
	print('fInGain', params.fInGain)
	print('fReverbMix', params.fReverbMix)
	print('fReverbTime', params.fReverbTime)
	print('fHighFreqRTRatio', params.fHighFreqRTRatio)
	params.fInGain = -95
	params.fReverbMix = -95
	params.fReverbTime = 2999
	params.fHighFreqRTRatio = 0.998
	result_BASS_FXSetParameters = BASS_FXSetParameters(DX8_effect_handle, ctypes.pointer(params))
	print('result BASS_FXSetParameters', result_BASS_FXSetParameters)
	result_BASS_FXGetParameters = BASS_FXGetParameters(DX8_effect_handle, ctypes.pointer(params))
	print('result BASS_FXGetParameters', result_BASS_FXGetParameters)
	print('fInGain', params.fInGain)
	print('fReverbMix', params.fReverbMix)
	print('fReverbTime', params.fReverbTime)
	print('fHighFreqRTRatio', params.fHighFreqRTRatio)
	if not BASS_Free():
		print 'BASS_Free error', get_error_description(BASS_ErrorGetCode())
