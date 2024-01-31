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
speech_config = speechsdk.SpeechConfig(subscription=os.environ.get('SPEECH_KEY'), region=os.environ.get('SPEECH_REGION'))
#audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)

#can't use multilingual because it doesn't allow passing phoneme field
speech_config.speech_synthesis_voice_name= 'en-US-JennyNeural'



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
                ):

    #to output a file with the audio
    #TODO: set this up so it'll upload to gdrive
    audio_config = speechsdk.audio.AudioOutputConfig(filename=output_fn)
    speech_synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config,
        audio_config=audio_config)
    
    ssml_input = f"""<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
    <voice name="en-US-JennyNeural">
        <phoneme alphabet="ipa" ph="{phonetic}"> {name} </phoneme>
    </voice>
</speak>"""

    speech_synthesizer.speak_ssml_async(ssml_input)

    #TODO: set up to return a link to the file in gdrive
    return None


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

  

                 
