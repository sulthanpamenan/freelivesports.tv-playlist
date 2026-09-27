import requests

def generate_playlist():
    url = "https://api.gizmott.com/api/v2/home"
    headers = {
        "accept": "application/json, text/plain, */*",
        "access-token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjaGVjayI6dHJ1ZSwicHViaWQiOiI1MDE4MyIsInVpZCI6Ijc5MzgxMTQiLCJjb3VudHJ5X2NvZGUiOiJJIDIsImRldmljZV90eXBlIjoid2ViIiwiaWF0IjoxNzkwNTExNDE1LCJleHAiOjE3OTgyODc0MTV9.3yF9I5p_Y7m2YZZ-bYQkTxkmzR_uFhCfPwVSALIDDdw",
        "pubid": "50183",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        
        m3u_content = "#EXTM3U\n"
        
        # Sesuai struktur standar API Gizmott, data home biasanya berisi section/list
        sections = data.get("data", [])
        if not sections and isinstance(data, list):
            sections = data

        for section in sections:
            channels = section.get("channels", [])
            for ch in channels:
                name = ch.get("channel_name", "Unknown")
                logo = ch.get("channel_image", "")
                stream_url = ch.get("stream_url", "")
                group = ch.get("genre_name", "Sports")
                
                if stream_url:
                    m3u_content += f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}",{name}\n'
                    m3u_content += f'{stream_url}\n'
                
        with open("playlist.m3u", "w", encoding="utf-8") as f:
            f.write(m3u_content)
        print("Playlist generated successfully!")
        
    except Exception as e:
        print(f"Error generating playlist: {e}")

if __name__ == "__main__":
    generate_playlist()
