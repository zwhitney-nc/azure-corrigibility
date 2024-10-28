import os
os.chdir('//Users/zacwhitney/Documents/Phon_Utils/')

from phon_utils import NCtoIPA


os.chdir('/Users/zacwhitney/Documents/azure_corrigibility/')
import IPA_TTS

import pandas as pd
import gspread
from gspread_dataframe import get_as_dataframe, set_with_dataframe

gc = gspread.oauth()

au_poc = gc.open_by_url('https://docs.google.com/spreadsheets/d/1xttQ4UqI_J_bPqegijj-gEslTkuQ-buBpv6b9pfz5OU/edit?gid=1715169649#gid=1715169649')
cleaned = au_poc.worksheet('cleaned')
df = get_as_dataframe(cleaned, drop_empty_rows=True)

df['phon_fn_ipa'] = df['phon_fn_nc'].apply(
    lambda x: NCtoIPA.convert_NC_to_IPA(x)
)

df['phon_sn_ipa'] = df['phon_sn_nc'].apply(
    lambda x: NCtoIPA.convert_NC_to_IPA(x)
)

set_with_dataframe(cleaned, df)

path = '/Users/zacwhitney/Documents/Australia PoC/audio/'

#IPA_TTS.nameToSpeech('peter', 'ˈpi.tɚ', path + '/peter.wav')

def generateAudio(x):
    fullName = x['First Name'] + ' ' + x['Last Name']
    fullPhon = x['phon_fn_ipa'] + ' ' + x['phon_sn_ipa']
    output_fn = path + fullName + '.wav'

    IPA_TTS.nameToSpeech(fullName,
                         fullPhon,
                         output_fn,
                         locale = 'en-AU',
                         voiceName = 'en-AU-NatashaNeural',
                         )

df.apply(generateAudio, axis=1)

#IPA_TTS.nameToSpeech('vijetha badarinath', 'vi.ˈd͡ʒeɪ.tɑ bɑd.ɹi.ˈnɑð', path + 'vijetha badarinath.wav')
