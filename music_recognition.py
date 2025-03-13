import os
from shazamio import Shazam

async def recognize_song_with_shazam(file_path):
    shazam = Shazam()
    try:
        out = await shazam.recognize(file_path)
        track = out['track']
        title = track.get('title', None)
        subtitle = track.get('subtitle', None)
        return subtitle, title
    except Exception as e:
        print(f"Shazamio Error: {e}")
    return None, None

async def rename_music_files(folder_path):
    for filename in os.listdir(folder_path):
        if filename.endswith(('.mp3', '.flac')):
            file_path = os.path.join(folder_path, filename)
            artist, title = await recognize_song_with_shazam(file_path)

            if artist and title:
                new_filename = f"{artist} - {title}.mp3"
                new_file_path = os.path.join(folder_path, new_filename)

                os.rename(file_path, new_file_path)
                print(f"Renamed '{filename}' to '{new_filename}'.")
            else:
                print(f"Failed to identify '{filename}'.")

# Execute the async function
import asyncio
asyncio.run(rename_music_files(r'C:\Users\marie\Documents\Music'))