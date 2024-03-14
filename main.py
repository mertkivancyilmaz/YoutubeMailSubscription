import os
import pickle
import requests
import schedule
import time
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from base64 import urlsafe_b64encode

# Kanal bilgileri
CHANNEL_ID = "UCju29RmyEoky0EWOYVvIVRg" # Vecspass kanalının ID si
EMAIL = "kvancy1907@gmail.com" # Alıcının e-mail adresi
CREDENTIALS_FILE = "client_secret_123456789.json" # indirilen JSON dosyasının adı

# Youtube Data API servisi ve kimlik doğrulama
youtube_scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
youtube_creds = None
youtube_token_file = "youtube_token.pickle"
if os.path.exists(youtube_token_file):
    with open(youtube_token_file, "rb") as f:
        youtube_creds = pickle.load(f)
if not youtube_creds or not youtube_creds.valid:
    if youtube_creds and youtube_creds.expired and youtube_creds.refresh_token:
        youtube_creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, youtube_scopes)
        youtube_creds = flow.run_local_server(port=0)
    with open(youtube_token_file, "wb") as f:
        pickle.dump(youtube_creds, f)
youtube_service = build("youtube", "v3", credentials=youtube_creds)

# Gmail API servisi ve kimlik doğrulama
gmail_scopes = ["https://www.googleapis.com/auth/gmail.send"]
gmail_creds = None
gmail_token_file = "gmail_token.pickle"
if os.path.exists(gmail_token_file):
    with open(gmail_token_file, "rb") as f:
        gmail_creds = pickle.load(f)
if not gmail_creds or not gmail_creds.valid:
    if gmail_creds and gmail_creds.expired and gmail_creds.refresh_token:
        gmail_creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, gmail_scopes)
        gmail_creds = flow.run_local_server(port=0)
    with open(gmail_token_file, "wb") as f:
        pickle.dump(gmail_creds, f)
gmail_service = build("gmail", "v1", credentials=gmail_creds)

# Mail gönderme fonksiyonu
def send_mail():
    # Kanalın videolar sekmesindeki son videoyu bulmak içinr
    # Kanalın videolar sekmesindeki videoları içeren oynatma listesinin kimliğini gerekli olan scriptle alır
    response = youtube_service.channels().list(part="contentDetails", id=CHANNEL_ID).execute() #
    items = response.get("items", [])

    #Youtube API için kanal bilgisi almak
    channel = items[0]
    playlist_id = channel["contentDetails"]["relatedPlaylists"]["uploads"]

    # Oynatma listesinin ilk elemanını almak
    response = youtube_service.playlistItems().list(part="snippet", playlistId=playlist_id, maxResults=1).execute()
    items = response.get("items", [])

    #Youtube API için video bilgisi almak
    video = items[0]
    video_id = video["snippet"]["resourceId"]["videoId"]
    video_title = video["snippet"]["title"]
    video_thumbnail_url = video["snippet"]["thumbnails"]["default"]["url"]

    # Video küçük resmini indirin
    response = requests.get(video_thumbnail_url)
    video_thumbnail = response.content

    # Mail oluşturun
    message = MIMEMultipart()
    message["to"] = EMAIL
    message["subject"] = "Vecspass kanalının en güncel videosu"
    message.attach(MIMEText(f"Merhaba, \n\nVecspass kanalının son paylaştığı video: {video_title} \n\nVideo linki: https://www.youtube.com/watch?v={video_id} \n\nKüçük resmi ektedir. \n\nİyi seyirler!"))
    message.attach(MIMEImage(video_thumbnail, name="thumbnail.jpg"))

    # Maili gönderin
    raw_message = urlsafe_b64encode(message.as_bytes())
    raw_message = raw_message.decode()
    body = {"raw": raw_message}
    message = gmail_service.users().messages().send(userId="me", body=body).execute()
    print("Mail gönderildi")

# Zamana duyarlı mail gönderme
schedule.every().day.at("08:00").do(send_mail)

# Zamanlayıcıyı başlat
while True:
    print('Uygulama halen çalışıyor')
    schedule.run_pending()
    time.sleep(59)