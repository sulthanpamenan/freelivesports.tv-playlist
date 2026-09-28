import requests
from urllib.parse import parse_qs, urlparse

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

def extract_genre_from_url(url):
    """Mengekstrak genre dari parameter URL stream (.m3u8) jika tersedia."""
    try:
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        
        for key in ["content_genre", "ads.content_genre", "genre"]:
            if key in query_params and query_params[key]:
                genres = query_params[key][0].split(",")
                if genres and genres[0]:
                    for g in genres:
                        clean_g = g.strip()
                        if clean_g.lower() not in ["sport", "sports"]:
                            return clean_g
                    return genres[0].strip()
    except Exception:
        pass
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
    added_channels = set()
    channel_count = 0

    # 1. Ambil dari endpoint master fastchannel list (Mendapatkan semua ID channel aktif)
    list_url = "https://api.gizmott.com/api/v1/fastchannel/list"
    print("Mengambil data dari endpoint master fastchannel list...")
    try:
        res = requests.get(list_url, headers=headers)
        if res.status_code == 200:
            channels_data = res.json().get("data", [])
            for ch in channels_data:
                ch_id = ch.get("channel_id") or ch.get("id")
                if not ch_id:
                    continue
                
                ch_id_str = str(ch_id)
                if ch_id_str in added_channels:
                    continue
                
                name = ch.get("show_name") or ch.get("channel_name") or ch.get("name") or "Unknown"
                logo = ch.get("logo_thumb", "") or ch.get("hero_image", "") or ch.get("logo", "")
                
                stream_url = ""
                detail_url = f"https://api.gizmott.com/api/v1/fastchannel/details/{ch_id_str}"
                try:
                    detail_res = requests.get(detail_url, headers=headers)
                    if detail_res.status_code == 200:
                        detail_data = detail_res.json().get("data", [])
                        if isinstance(detail_data, list) and detail_data:
                            item_detail = detail_data[0]
                            stream_url = item_detail.get("live_link", "") or item_detail.get("stream_url", "")
                        elif isinstance(detail_data, dict):
                            stream_url = detail_data.get("live_link", "") or detail_data.get("stream_url", "")
                except Exception:
                    pass

                if stream_url:
                    added_channels.add(ch_id_str)
                    
                    # Ekstrak kategori spesifik dari URL stream
                    group_name = extract_genre_from_url(stream_url)
                    if not group_name:
                        group_name = ch.get("category_name") or ch.get("genre") or "Live Sports"
                    
                    m3u_content += f'#EXTINF:-1 tvg-id="{ch_id_str}" tvg-name="{name}" tvg-logo="{logo}" group-title="{group_name}",{name}\n'
                    m3u_content += f'{stream_url}\n'
                    channel_count += 1
                    print(f"Berhasil menambahkan: {name} (Kategori: {group_name})")
    except Exception as e:
        print(f"Error mengambil master list: {e}")

    # 2. Ambil dari endpoint beranda sebagai cadangan/tambahan
    home_url = "https://api.gizmott.com/api/v2/home"
    print("\nMemeriksa tambahan data dari beranda utama...")
    try:
        response = requests.get(home_url, headers=headers)
        if response.status_code == 200:
            res_json = response.json()
            sections = res_json.get("data", [])
            
            for section in sections:
                default_section_group = section.get("category_name", "Sports")
                shows = section.get("shows", [])
                
                for ch in shows:
                    ch_id = ch.get("channel_id")
                    if not ch_id:
                        continue
                    
                    ch_id_str = str(ch_id)
                    if ch_id_str in added_channels:
                        continue
                    
                    name = ch.get("show_name", "Unknown")
                    logo = ch.get("logo_thumb", "") or ch.get("hero_image", "")
                    
                    stream_url = ""
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

                    if stream_url:
                        added_channels.add(ch_id_str)
                        
                        group_name = extract_genre_from_url(stream_url)
                        if not group_name:
                            group_name = default_section_group
                            
                        m3u_content += f'#EXTINF:-1 tvg-id="{ch_id_str}" tvg-name="{name}" tvg-logo="{logo}" group-title="{group_name}",{name}\n'
                        m3u_content += f'{stream_url}\n'
                        channel_count += 1
                        print(f"Berhasil menambahkan (Beranda): {name} (Kategori: {group_name})")
    except Exception as e:
        print(f"Terjadi kesalahan saat mengambil data beranda: {e}")

    # Simpan hasil akhir gabungan ke file M3U
    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write(m3u_content)
        
    print(f"\nPlaylist berhasil di-generate! Total {channel_count} channel unik dimasukkan ke playlist.m3u")

if __name__ == "__main__":
    generate_playlist()
