import yt_dlp
from pydub import AudioSegment
import os

#Create a folder to save
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, '..', 'downloads'))
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
#youtube videos download

def download_youtube_audio(url:str)->str:
    output_path=os.path.join(DOWNLOAD_DIR,"%(title)s.%(ext)s")
    ydl_opts={
        "format":"bestaudio/best",
        "outtmpl":output_path,
        "postprocessors":[
            {
                "key":"FFmpegExtractAudio",
                "preferredcodec":"wav",
                "preferredquality":"192",
            }
        ],
        "quiet":True #suppress downlaod progress log 
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info=ydl.extract_info(url,download=True)
        filename=ydl.prepare_filename(info).replace(".webm",".wav").replace(".m4a",".wav")
    return filename

data=download_youtube_audio("https://youtu.be/BHihkRwisbE?si=qrIdQ7WxDqahKbad")



#conveting any audio/video file to wav format using pydub
def convert_to_wav(input_path:str)->str:
    output_path=os.path.splitext(input_path)[0]+"_converted.wav"
    audio=AudioSegment.from_file(input_path) #deteh audio type 
    audio=audio.set_channels(1).set_frame_rate(16000) #set_channel->monoaudio ,16khz->
    audio.export(output_path,format="wav")
    return output_path

print(convert_to_wav(data))
