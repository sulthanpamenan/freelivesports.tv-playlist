import requests

def authenticate_guest():
    """Melakukan autentikasi tamu untuk mendapatkan token akses yang valid."""
    auth_url = "https://api.gizmott.com/api/v1/account/authenticate"
    headers = {
        "accept": "application/json, text/plain, */*",
        "channelid": "516",
        "country_code": "ID",
        "crossorigin": "true",
        "dev_id": "5d01d64ac5b0026957052f0330129fc6",
        "device_type": "web",
        "ip": "103.150.218.78",
        "pubid": "50183",
        "uid": "7938114",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(auth_url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            token = data.get("token")
            print("Autentikasi berhasil!")
            return token
        else:
            print(f"Gagal autentikasi: Status {response.status_code}")
            return None
    except Exception as e:
        print(f"Error saat autentikasi: {e}")
        return None

def generate_playlist():
    # 1. Dapatkan token secara dinamis lewat autentikasi
    token = authenticate_guest()
    if not token:
        print("Tidak dapat melanjutkan pembuatan playlist karena token gagal didapatkan.")
        return

    # Endpoint home atau daftar channel (disesuaikan dengan v1/v2 API Gizmott)
    url = "https://api.gizmott.com/api/v2/home"
    headers = {
        "accept": "application/json, text/plain, */*",
        "access-token": token,
        "pubid": "50183",
        "channelid": "516",
        "country_code": "ID",
        "device_type": "web",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        
        m3u_content = "#EXTM3U\n"
        
        # Ekstraksi data berdasarkan struktur JSON API
        sections = data.get("data", [])
        if not sections and isinstance(data, list):
            sections = data

        channel_count = 0
        for section in sections:
            channels = section.get("channels", [])
            for ch in channels:
                name = ch.get("channel_name", "Unknown")
                logo = ch.get("channel_image", "")
                stream_url = ch.get("stream_url", "")
                group = ch.get("genre_name", "Sports")
                
                # Jika stream_url kosong di home, Anda bisa mengambil detail via ID channel (contoh: ch.get("channel_id"))
                if not stream_url and "channel_id" in ch:
                    # Optional: Fetch detail jika stream_url tidak langsung tersedia di response home
                    ch_id = ch.get("channel_id")
                    stream_url = f"https://api.gizmott.com/api/v1/fastchannel/details/{ch_id}" # atau parsing endpoint amagi
                
                if stream_url:
                    m3u_content += f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}",{name}\n'
                    m3u_content += f'{stream_url}\n'
                    channel_count += 1
                
        with open("playlist.m3u", "w", encoding="utf-8") as f:
            f.write(m3u_content)
            
        print(f"Playlist berhasil di-generate! Total {channel_count} channel dimasukkan ke playlist.m3u")
        
    except Exception as e:
        print(f"Error generating playlist: {e}")

if __name__ == "__main__":
    generate_playlist()
