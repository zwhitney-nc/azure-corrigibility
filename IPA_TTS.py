import os
import azure.cognitiveservices.speech as speechsdk

import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


#### big picture ####
"""
have a method that takes a name + IPA (later can do NC phon too) and returns
a link to an audio file containing the pronunciation

can maybe specify where to store the audio files in a config dict or
something

make a separate script to run this over the IPA converter test set


"""



### config
# This example requires environment variables named "SPEECH_KEY" and "SPEECH_REGION"; make sure they're set in your .bashrc or equivalent
speech_config = speechsdk.SpeechConfig(
    subscription=os.environ.get('SPEECH_KEY'),
    region=os.environ.get('SPEECH_REGION'),
)
#audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)

#can't use multilingual because it doesn't allow passing phoneme field
#speech_config.speech_synthesis_voice_name= 'en-US-JennyNeural'
speech_config.speech_synthesis_voice_name = 'en-AU-NatashaNeural'


def googleAuth(tokenPath: str,
               credFilePath: str,
               scopes = None,
               ) -> Credentials: 

    if scopes is None:
        scopes = ["https://www.googleapis.com/auth/drive",
                  "https://www.googleapis.com/auth/drive.file"]

    creds = None
    """The file token.json stores the user's access and refresh tokens, and
    is created automatically when the authorization flow completes for the
    first time."""

    if os.path.exists(tokenPath):
        creds = Credentials.from_authorized_user_file(tokenPath, SCOPES)
        #If there are no (valid) credentials available, let the user log in
        
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credFilePath, scopes
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(tokenPath, "w") as token:
            token.write(creds.to_json())


    return creds

def gdriveUpload(creds: Credentials,
                 parentFolderID: str,
                 filename: str,
                 filePath: str,
                 mimeType = "audio/wav",
                 ) -> str:

    #TODO: clean up so this outputs a URL
    try:
        service = build("drive", "v3", credentials=creds)

        folder_id = parentFolderID

        file_metadata = {
            "name": filename,
            "parents": [folder_id]
        }
        media = MediaFileUpload(filePath + filename,
                                mimetype=mimeType)
        # pylint: disable=maybe-no-member
        file = (
            service.files()
            .create(body=file_metadata,
                    media_body=media,
                    fields="webViewLink",
                    supportsAllDrives=True)
            .execute()
        )
        return file.get("webViewLink")

    except HttpError as error:
        print(f"An error occurred: {error}")
        file = None
        return file



def nameToSpeech(name: str,
                 phonetic: str, #needs to be in IPA (for now...)
                 output_fn: str,
                 locale = 'en-US',
                 voiceName ='en-US-JennyNeural',
                 ):

    #to output a file with the audio
    #TODO: set this up so it'll upload to gdrive
    audio_config = speechsdk.audio.AudioOutputConfig(filename=output_fn)
    speech_synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config,
        audio_config=None)
        #audio_config=audio_config)
    
    ssml_input = f"""<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="{locale}">
    <voice name="{voiceName}">
        <phoneme alphabet="ipa" ph="{phonetic}"> {name} </phoneme>
    </voice>
</speak>"""

    result = speech_synthesizer.speak_ssml_async(ssml_input).get()
    stream = speechsdk.AudioDataStream(result)
    stream.save_to_wav_file(output_fn)

    #TODO: set up to return a link to the file in gdrive
    return None


def nameToSpeech_noPhoneme(name: str,
                           output_fn: str,
                           ):
    
    #idk why, but writing direct to file doesn't work, it always does a segmentation fault, even though they said they fixed it in version 138

    
    #breakpoint()
    #audio_config = speechsdk.audio.AudioOutputConfig(filename=output_fn)
    #audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
    
    
    speech_synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config,
        audio_config=None)
        #audio_config=audio_config)
    
    #ssml_input = f"""<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
    #<voice name="en-US-JennyNeural">
    #     {name}
    #</voice>
#</speak>"""

    result = speech_synthesizer.speak_text_async(name).get()
    stream = speechsdk.AudioDataStream(result)
    stream.save_to_wav_file(output_fn)

    #return None

def main():
    import pandas as pd
    import gspread
    from gspread_dataframe import get_as_dataframe, set_with_dataframe

    URL_DICT = {
        'testing': 'https://docs.google.com/spreadsheets/d/18zMSfPDPvQXbCI_ewzfGpyJaMzh1Hst08nvV10q1BVk/edit?pli=1#gid=1557275257'
    }

    #load from gsheets
    gc = gspread.oauth()

    testing = gc.open_by_url(URL_DICT['testing']).worksheet(
        'Testing - 5/3/2024 + freq & US TTS')

    df = get_as_dataframe(testing, evaluate_formulas=True, drop_empty_rows=True, drop_empty_columns=True)

    path = '/Users/zacwhitney/Documents/Precision 2.0 Testing/en_tts_files'

    for name in df['Name'].unique():

        fn = f"{path}/{name}.wav"
        nameToSpeech_noPhoneme(name, fn)
        
        print(f"wrote {name} to {fn}")

    


if __name__ == '__main__':
    main()


#### SCRATCH ####

"""SCOPES = ["https://www.googleapis.com/auth/drive",
          "https://www.googleapis.com/auth/drive.file"]

creds = None
# The file token.json stores the user's access and refresh tokens, and is
# created automatically when the authorization flow completes for the first
# time.

if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            "credentials.json", SCOPES
        )
        creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
        token.write(creds.to_json())"""


#try something like this:
#results = drive_service.files().list(supportsAllDrives=True, includeItemsFromAllDrives=True, ...

"""try:
    #creds, _ = google.auth.default(scopes=SCOPES)
    service = build("drive", "v3", credentials=creds)

    folder_id = "1bY74G0aaLSnj_24RuIteTJQ_aHj7GkMo"

    file_metadata = {
        "name": "Samia2.wav",
        "parents": [folder_id]
    }
    media = MediaFileUpload("audio_files/Samia.wav", mimetype="audio/wav")
    # pylint: disable=maybe-no-member
    file = (
        service.files()
        .create(body=file_metadata,
                media_body=media,
                fields="webViewLink",
                supportsAllDrives=True)
        .execute()
    )
    print(f'File ID: {file.get("id")}')

except HttpError as error:
    print(f"An error occurred: {error}")
    file = None"""

"""
links = [
'https://drive.google.com/open?id=1dauk-mrKBX_2egGNiDDq9gZuaTosNhnE&usp=drive_copy',
'https://drive.google.com/open?id=138T4SC69KfCg_cJolbAdYnZXBgZeeS2y&usp=drive_copy',
'https://drive.google.com/open?id=14nElPcPiTbEJW2KpQF5cTe4H2YuyeI0x&usp=drive_copy',
'https://drive.google.com/open?id=1hP1veHgj9ET3P6iN_pXqtXkTGIcp22ln&usp=drive_copy',
'https://drive.google.com/open?id=1Q7nUIEQiUGXGSn0ieUdM-I_m0RI-20OZ&usp=drive_copy',
'https://drive.google.com/open?id=15LmLWngVFLP9ZVsZY69WT-TE0bKgDL0A&usp=drive_copy',
'https://drive.google.com/open?id=1BU1ifdW7QiYlh1PU-WQQWXvzL7TcsKI5&usp=drive_copy',
'https://drive.google.com/open?id=1KLthsMRJwBVtV0VkNoQQ75JqB-vMIVWS&usp=drive_copy',
'https://drive.google.com/open?id=1Ad83afLLOG01FdoGb--VSTJaEAFG0Qw8&usp=drive_copy',
'https://drive.google.com/open?id=1MMGZFRVrzpk8Z423lAIjOWSXXC-CsAoA&usp=drive_copy',
'https://drive.google.com/open?id=1dL-0a3N1jed8KKNV70fIk6hT80FOtcwY&usp=drive_copy',
'https://drive.google.com/open?id=1_ZnP6O4BlrqHB6oLsgO3c1HNETDJJQpL&usp=drive_copy',
'https://drive.google.com/open?id=1VfGDJYJ-r_4YrLe-GSSTLJRce5MwBDov&usp=drive_copy',
'https://drive.google.com/open?id=1FnObcOgxfqrTpYOAU8EXL_nyR4eMI6nR&usp=drive_copy',
'https://drive.google.com/open?id=1uotjkH4zCyHZ0Taa8AJRwJzvIPtiOpEO&usp=drive_copy',
'https://drive.google.com/open?id=1DcgQVbtx0xR2etd1ZUangXA4iqiocwE6&usp=drive_copy',
'https://drive.google.com/open?id=1D-OLM8JdmHUl5O2kOhoZCkXTxSwMKU4I&usp=drive_copy',
'https://drive.google.com/open?id=1ldX2lVOTWHkmM6nerkkXjRQ5xdsPgH77&usp=drive_copy',
'https://drive.google.com/open?id=1gvC27yKC_2uv7G7ATc4DOtylab2-9L6A&usp=drive_copy',
'https://drive.google.com/open?id=1k8ppVIhmSWlEJVa-P9TZYL-cs6Uvy4lK&usp=drive_copy',
'https://drive.google.com/open?id=1mkMRT8x0-t6UIs5GvQxI126oku1af2Qf&usp=drive_copy',
'https://drive.google.com/open?id=12JZcC9GW4Z-fTCHaAQC1TSkVdZHxaOpc&usp=drive_copy',
'https://drive.google.com/open?id=1OVsVLFXF_r7Kb3IITnUTebNG6BbdSyJn&usp=drive_copy',
'https://drive.google.com/open?id=1plB5fcTahecEiyQacHI9vIJXlVEqqZf3&usp=drive_copy',
'https://drive.google.com/open?id=1E3isj0qB71maTANX1PHQQn-slX6Lb8jz&usp=drive_copy',
'https://drive.google.com/open?id=1u3tDXBN_9XOnFiv3mOGA2Jg6p7V98z_j&usp=drive_copy',
'https://drive.google.com/open?id=1gdkqkR4tx5d6M1BzyuuWo0erYVMvywCb&usp=drive_copy',
'https://drive.google.com/open?id=1I6EUyAE5sRL-CQJP97TZpPasLNqASvHV&usp=drive_copy',
'https://drive.google.com/open?id=1yj8A0mhg1GEhj29i7UH6EVaFnPffRaf_&usp=drive_copy',
'https://drive.google.com/open?id=1QkrWo8fxJsa6GBC-ARfIwV74Di4Z4Dap&usp=drive_copy',
'https://drive.google.com/open?id=1g-bliBQ1rUnWElBNvDd_vIbzZSrXHa_i&usp=drive_copy',
'https://drive.google.com/open?id=12kd6OK8_B9s_8klN1wcnVGkLOe59nOxH&usp=drive_copy',
'https://drive.google.com/open?id=1HJN79hlUmgRkFd2KIzHLZGmk_DLM8eLp&usp=drive_copy',
'https://drive.google.com/open?id=1z5dpTE-dw6bd_ymKznZ6LarIftk2WG7A&usp=drive_copy',
'https://drive.google.com/open?id=1yrIBTGeUGafFZ1E927p0Di6fv4ITTLwZ&usp=drive_copy',
'https://drive.google.com/open?id=1jYFL5xRRro-g1WgT9iF1TGkcVcgtq-mT&usp=drive_copy',
'https://drive.google.com/open?id=1PS2p1s1fZiDfwwLWzXAu-NgPoWK8UYZ6&usp=drive_copy',
'https://drive.google.com/open?id=1q9eyS0Xp6nLP457s0xNOArfKu_oadV8R&usp=drive_copy',
'https://drive.google.com/open?id=1h4CuksZccpozRlgZ_WUgK3BlbXW8WLNC&usp=drive_copy',
'https://drive.google.com/open?id=1YAHFDeDzHNa3zMFujvM8SuQZf-J_mAnj&usp=drive_copy',
'https://drive.google.com/open?id=144E6656KKrFFt7gYdwVSfBeioeUb5mFC&usp=drive_copy',
'https://drive.google.com/open?id=1zl80rwjVg6ch9NOjiGxWfpCE_T-yaeor&usp=drive_copy',
'https://drive.google.com/open?id=1UeECAP9fF3jpfMJ3YqGxiedcG3yaRW78&usp=drive_copy',
'https://drive.google.com/open?id=1LFI_fElTqW-CxQqrIcAJdRn0_M-DPYGP&usp=drive_copy',
'https://drive.google.com/open?id=1hmQrx6bxLh-UU3-pm92YndY6t90I3Bye&usp=drive_copy',
'https://drive.google.com/open?id=1yQ3PyLnV6zhelpQhH5GLtqcT97EkUl15&usp=drive_copy',
'https://drive.google.com/open?id=1K82zXJEK3BKO75f7TSkKBOMkoXl3UgbK&usp=drive_copy',
'https://drive.google.com/open?id=1SWnCS-q_g1lkjNuc1d3Va8_CjbtFtnHY&usp=drive_copy',
'https://drive.google.com/open?id=1wCM42o62z-Y5zdhBtCQiJjyTJ01sR1Dk&usp=drive_copy',
'https://drive.google.com/open?id=1Mkyb48WFDAjq1G9nv4p59ozm-k_B7G1H&usp=drive_copy',
'https://drive.google.com/open?id=1N63_Mif5TDk3s6_tBnZCKO_4Y8uqiDIG&usp=drive_copy',
'https://drive.google.com/open?id=1SN4SX08ZzgWROkCgVKyGxGAoG9vFYt80&usp=drive_copy',
'https://drive.google.com/open?id=12e8X8sKyKfZoHYojbjqILS0deNxuz_FE&usp=drive_copy',
'https://drive.google.com/open?id=1a_0exwYJsaqd43lSY9Pyh5yVQBotOHYi&usp=drive_copy',
'https://drive.google.com/open?id=19XwY6YnKigKz7gNj4K2rdbRwO93YM8oU&usp=drive_copy',
'https://drive.google.com/open?id=1s5R_k25k-B5hC5WfECFC7CJqVAZqM3qa&usp=drive_copy',
'https://drive.google.com/open?id=1Kvc6G6QwLxvtohEYkAcia0tkGELqUfGz&usp=drive_copy',
'https://drive.google.com/open?id=1brZq9qTOEaGD8YVrcRvBYgCpHcvqgXrc&usp=drive_copy',
'https://drive.google.com/open?id=1w5yO5r4wn9EMgj9WH5uedI8oduHbXx5G&usp=drive_copy',
'https://drive.google.com/open?id=1RynzP6oMGgKItQ8YJ8KIU-eH9wZ9smBK&usp=drive_copy',
'https://drive.google.com/open?id=1wDr_0XGyjXIESxx5ZT-qZz0f8_RMo_w6&usp=drive_copy',
'https://drive.google.com/open?id=1RYQh2BaWKgdilb57YlsLjFckkz1Hpijt&usp=drive_copy',
'https://drive.google.com/open?id=1637xc4LIkFBCDZpIHnJRtKDNr230H9sc&usp=drive_copy',
'https://drive.google.com/open?id=1AfDq-OF6MMv-H7k25kMLXHP5aIwXLibb&usp=drive_copy',
'https://drive.google.com/open?id=1ZG4EP8arLoXu7nNH9v4ROlHamywIf0HF&usp=drive_copy',
'https://drive.google.com/open?id=1WodRaNprHzwdFgER6mAhFmDVAqftgtmJ&usp=drive_copy',
'https://drive.google.com/open?id=1iCSKGxKIM24zYiWGrBSlu7TmkJ911lnX&usp=drive_copy',
'https://drive.google.com/open?id=17d49WeS45LpqwFomc1c5VK864IlIig-2&usp=drive_copy',
'https://drive.google.com/open?id=1ujNVQbLDHROZIjZEEVo13ZC-1_Isdq_G&usp=drive_copy',
'https://drive.google.com/open?id=1bWEtl_oJbP9_olQwjwm5OS-8f6FQPbCW&usp=drive_copy',
'https://drive.google.com/open?id=1PRQZ-_Azis5YIas7a5yxEaj-R7x5jn1i&usp=drive_copy',
'https://drive.google.com/open?id=1hmRuWRQqXfYOskgWDL4fBC2eqRiPv21D&usp=drive_copy',
'https://drive.google.com/open?id=150ZaowBduV9U5OAZ-WDbtc3x0mYphhz0&usp=drive_copy',
'https://drive.google.com/open?id=15Bqu4wQjxBSMLk5K4T_1GRVVuY1pOg0C&usp=drive_copy',
'https://drive.google.com/open?id=186sqXuy0E4_XRsoJ5SX3ijrt2APtMYEu&usp=drive_copy',
'https://drive.google.com/open?id=1Wi5ZFQiT6PQY2o7774zmIy4YS5ng6JEN&usp=drive_copy',
'https://drive.google.com/open?id=1nETQVDFjUlMgeiLAfW902fpD0XFT0y_l&usp=drive_copy',
'https://drive.google.com/open?id=1nTDlatMRAYQUzS9lHlBWA0y1kwTyVytx&usp=drive_copy',
'https://drive.google.com/open?id=1rnXhO-Q1fsGuhW9HyxvjuRsWTe4v_724&usp=drive_copy',
'https://drive.google.com/open?id=1_dZemHxNKaBAhMMIFA-xQ3gf0Eyj7rwP&usp=drive_copy',
'https://drive.google.com/open?id=14JYrqV02rfLgTrpRMqImNtB4k1_Hvg9S&usp=drive_copy',
'https://drive.google.com/open?id=114XJsyDfMRRtCDIBEAHSj7AROkjJT0KJ&usp=drive_copy',
'https://drive.google.com/open?id=1nUNLxE1S8WznkN8zPnGBBI59zZbElnPu&usp=drive_copy',
'https://drive.google.com/open?id=1q4d5P58QfFIgskiZOPurVKNV8C4YABhB&usp=drive_copy',
'https://drive.google.com/open?id=1HMFh_lGzOU_tUb5zXOX5kqDP0517IzVR&usp=drive_copy',
'https://drive.google.com/open?id=17euXyHtaHNRTZ3vUb_PqYCRsx6k9Bf9p&usp=drive_copy',
'https://drive.google.com/open?id=1bV2zht602-OZqe_I303i_7lzsTP4HK88&usp=drive_copy',
'https://drive.google.com/open?id=17Dz3Idpqa8rFZd_kMEka3cDWeRS6UXlC&usp=drive_copy',
'https://drive.google.com/open?id=1tHN9tjPafRUNbGcMSdsc_j6B9yfrnbMh&usp=drive_copy',
'https://drive.google.com/open?id=1CJNohX9bpO27zJAxJ8Dk35FGE6tymafC&usp=drive_copy',
'https://drive.google.com/open?id=1gx4n3-gc22g0nabhYHU60gLoE5eqxJxn&usp=drive_copy',
'https://drive.google.com/open?id=1vH7hBjwgGAemXtj0FgORRDAAYc4KKiM_&usp=drive_copy',
'https://drive.google.com/open?id=1f3_KkCB3BUt5pYFjVf3WlHbrEWbMnHmH&usp=drive_copy',
'https://drive.google.com/open?id=12FwhG2iFoiEsEAyh0F6xmU_mHa2oAPRS&usp=drive_copy',
'https://drive.google.com/open?id=1WtHkNhHKGq7jQ4b_685NI9TR1gt5cs0H&usp=drive_copy',
'https://drive.google.com/open?id=13jhQxXwKDlXeWfb_m0lR6USRGL3jZ2DI&usp=drive_copy',
'https://drive.google.com/open?id=1cs4BVd7dfOqYadXKiAiTPYNCPBTsav8j&usp=drive_copy',
'https://drive.google.com/open?id=1HG2JR6yyMwLBFDs-VOqDQgvu1dSO2mfc&usp=drive_copy',
'https://drive.google.com/open?id=1kjDvtuQ-FYMlPJcPgdMjy00NNx5dAdwm&usp=drive_copy',
'https://drive.google.com/open?id=1MdEYbGBg8GbxvCUlAbE2Grrpy4fori_X&usp=drive_copy',
'https://drive.google.com/open?id=1H0r4zAkDTcwGa87iDbN25xaE0Pq7gaZf&usp=drive_copy',
'https://drive.google.com/open?id=1BXCfcYha6T84WwcZzRIwv_iVeEnI7GY8&usp=drive_copy',
'https://drive.google.com/open?id=1FsopjIpYEyLmwvOqRo5hDWjX_mb6Awzw&usp=drive_copy',
'https://drive.google.com/open?id=1lYDsYJgpltQyYmCsqYm4ddfhGNbaMalN&usp=drive_copy',
'https://drive.google.com/open?id=1ApQATYYYOYqZZJNz5IIuzlHClry7fyA-&usp=drive_copy',
'https://drive.google.com/open?id=18Z1fmPLjhd0DN4VOCM8A94nS9BXPk3jL&usp=drive_copy',
'https://drive.google.com/open?id=1UWzMk8d7GMRitlzeFwPC0vWlQU8ad6Ib&usp=drive_copy',
'https://drive.google.com/open?id=1tEmYv4w-8CUC-10IEfP7vZ9lf-Dgnd8w&usp=drive_copy',
'https://drive.google.com/open?id=1C61CCpq8vMcymA2sgpp7IOy6FO1cFIjt&usp=drive_copy',
]

df.sort_values(by='Name', inplace=True)

for name, link in zip(df['Name'].unique(), links):
    df.loc[df['Name']==name, 'US TTS Link'] = link

set_with_dataframe(testing, pd.DataFrame(df['US TTS Link']), col = 14)

"""

                 
