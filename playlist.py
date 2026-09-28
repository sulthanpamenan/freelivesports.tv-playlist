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
    token = authenticate_guest()
    if not token:
        print("Tidak dapat melanjutkan pembuatan playlist karena token gagal didapatkan.")
        return

    headers = {
        "accept": "application/json, text/plain, */*",
        "access-token": token,
        "pubid": "50183",
        "channelid": "516",
        "country_code": "ID",
        "crossorigin": "true",
        "dev_id": "5d01d64ac5b0026957052f0330129fc6",
        "device_type": "web",
        "uid": "7938114",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36"
    }
    
    home_url = "https://api.gizmott.com/api/v2/home"
    
    print("Mengambil seluruh data channel dari beranda...")
    try:
        response = requests.get(home_url, headers=headers)
        if response.status_code != 200:
            print(f"Gagal mengambil data beranda: Status {response.status_code}")
            return
            
        res_json = response.json()
        sections = res_json.get("data", [])
        
        m3u_content = "#EXTM3U\n"
        channel_count = 0
        added_channels = set() # Mencegah duplikasi channel

        for section in sections:
            group_name = section.get("category_name", "Sports")
            shows = section.get("shows", [])
            
            for ch in shows:
                # Lewati jika item bukan channel live (channel_id bernilai null atau tidak ada)
                ch_id = ch.get("channel_id")
                if not ch_id:
                    continue
                
                ch_id_str = str(ch_id)
                name = ch.get("show_name", "Unknown")
                logo = ch.get("logo_thumb", "") or ch.get("hero_image", "")
                
                stream_url = ""
                # Ambil stream_url melalui endpoint detail berdasarkan channel_id
                if ch_id_str:
                    detail_url = f"https://api.gizmott.com/api/v1/fastchannel/details/{ch_id_str}"
                    try:
                        detail_res = requests.get(detail_url, headers=headers)
                        if detail_res.status_code == 200:
                            detail_json = detail_res.json()
                            detail_data = detail_json.get("data", [])
                            if isinstance(detail_data, list) and detail_data:
                                stream_url = detail_data[0].get("live_link", "") or detail_data[0].get("stream_url", "")
                            elif isinstance(detail_data, dict):
                                stream_url = detail_data.get("live_link", "") or detail_data.get("stream_url", "")
                    except Exception:
                        pass

                if stream_url and ch_id_str not in added_channels:
                    added_channels.add(ch_id_str)
                    tvg_id = ch_id_str
                    tvg_name = name
                    
                    m3u_content += f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{tvg_name}" tvg-logo="{logo}" group-title="{group_name}",{name}\n'
                    m3u_content += f'{stream_url}\n'
                    channel_count += 1
                    print(f"Berhasil menambahkan: {name} (Kategori: {group_name})")

        with open("playlist.m3u", "w", encoding="utf-8") as f:
            f.write(m3u_content)
            
        print(f"\nPlaylist berhasil di-generate! Total {channel_count} channel unik dimasukkan ke playlist.m3u")

    except Exception as e:
        print(f"Terjadi kesalahan saat mengambil playlist: {e}")

if __name__ == "__main__":
    generate_playlist()
