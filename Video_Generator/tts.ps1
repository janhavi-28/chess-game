Add-Type -AssemblyName System.Speech
 = New-Object System.Speech.Synthesis.SpeechSynthesizer
.SetOutputToWaveFile('d:\\AIVATIKA_WORK\\Smart_Chess2\\Video_Generator\\public\\assets\\sounds\\canyoufind.wav')
.Speak('Can you find the winning move?')
.Dispose()
