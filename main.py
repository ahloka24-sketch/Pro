import requests

ACCESS_TOKEN = "YOUR_ACCESS_TOKEN"

VIDEO_ID = "YOUR_VIDEO_ID"

url = f"https://graph.facebook.com/v19.0/{VIDEO_ID}?fields=source&access_token={ACCESS_TOKEN}"

response = requests.get(url)

data = response.json()

if "source" in data:

    video_url = data["source"]

    

    video_data = requests.get(video_url).content

    

    with open("video.mp4", "wb") as f:

        f.write(video_data)

    print("Downloaded successfully!")

else:

    print("Error:", data)
