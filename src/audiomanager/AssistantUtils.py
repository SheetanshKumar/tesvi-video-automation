from gtts import gTTS
import src.audiomanager.AssistantConfig as ac
from mutagen.mp3 import MP3

def assistant_speaks(output, file):
    toSpeak = gTTS(text=output, lang='en-US', slow=False)
    toSpeak.save(file)
    print(output)
    ac.LENGTH_SPOKEN = ac.LENGTH_SPOKEN + len(output)


# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "My First Project-4063e620ab5f.json"
# from google.cloud import texttospeech
#
# def assistant_speaks(text, filename):
#     client = texttospeech.TextToSpeechClient()
#     synthesis_input = texttospeech.types.SynthesisInput(text=text)
#
#     voice = texttospeech.types.VoiceSelectionParams(
#         language_code='en-IN',
#         name=ConstantsText.google_wavenet_name,
#         ssml_gender=ConstantsText.google_wavenet_gender)
#
#     audio_config = texttospeech.types.AudioConfig(
#         audio_encoding=texttospeech.enums.AudioEncoding.MP3)
#
#     response = client.synthesize_speech(synthesis_input, voice, audio_config)
#
#     with open(filename, 'wb') as out:
#         out.write(response.audio_content)
#     print(text)
#     ac.length_spoken = ac.length_spoken + len(output)
