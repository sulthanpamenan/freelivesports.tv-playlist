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
    
    m3u_content = "#EXTM3U\n"
    channel_count = 0
    
    print("Mengambil data channel...")
    for ch_id in range(1940, 2050):
        detail_url = f"https://api.gizmott.com/api/v1/fastchannel/details/{ch_id}"
        try:
            response = requests.get(detail_url, headers=headers)
            if response.status_code == 200:
                res_data = response.json()
                data_list = res_data.get("data", [])
                
                if data_list and isinstance(data_list, list):
                    ch = data_list[0]
                    name = ch.get("channel_name", "Unknown")
                    logo = ch.get("logo", "")
                    stream_url = ch.get("live_link", "")
                    
                    # Mengambil kategori asli channel secara otomatis
                    categories = ch.get("categories", [])
                    group = categories[0].get("category_name", "General") if categories else "General"
                    
                    # Atribut EPG tvg-id dan tvg-name
                    tvg_id = str(ch.get("channel_id", ch_id))
                    tvg_name = name
                    
                    if stream_url:
                        m3u_content += f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{tvg_name}" tvg-logo="{logo}" group-title="{group}",{name}\n'
                        m3u_content += f'{stream_url}\n'
                        channel_count += 1
                        print(f"Berhasil menambahkan: {name} [{group}]")
        except Exception as e:
            continue

    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write(m3u_content)
        
    print(f"Playlist berhasil di-generate! Total {channel_count} channel dimasukkan ke playlist.m3u")

if __name__ == "__main__":
    generate_playlist()
