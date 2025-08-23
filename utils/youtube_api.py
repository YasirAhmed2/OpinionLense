from googleapiclient.discovery import build
from config import API_KEY

def get_youtube_service():
    return build("youtube", "v3", developerKey=API_KEY)

def fetch_comments(video_id, max_results=100):
    youtube = get_youtube_service()
    request = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id,
        maxResults=max_results,
        textFormat="plainText"
    )
    response = request.execute()

    comments = []
    for item in response["items"]:
        comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
        comments.append(comment)
    return comments
