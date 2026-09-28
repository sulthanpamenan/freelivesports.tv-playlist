import requests
from datetime import datetime, timedelta

def authenticate_guest():
    """Perform guest authentication to obtain a valid access token."""
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
            print("EPG authentication successful!")
            return token
    except Exception as e:
        print(f"Error during EPG authentication: {e}")
    return None

def generate_epg():
    token = authenticate_guest()
    if not token:
        print("Cannot proceed with EPG generation because the token could not be obtained.")
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

    added_channels = set()
    channels_xml = ""
    programmes_xml = ""

    now = datetime.utcnow()
    start_time = (now - timedelta(days=1)).strftime('%Y%m%d%H%M%S +0000')
    stop_time = (now + timedelta(days=3)).strftime('%Y%m%d%H%M%S +0000')

    # 1. Take from the master list
    list_url = "https://api.gizmott.com/api/v1/fastchannel/list"
    print("Retrieving channel data for the EPG from the master list...")
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
                
                stream_url = ""
                detail_url = f"https://api.gizmott.com/api/v1/fastchannel/details/{ch_id_str}"
                try:
                    detail_res = requests.get(detail_url, headers=headers)
                    if detail_res.status_code == 200:
                        detail_data = detail_res.json().get("data", [])
                        if isinstance(detail_data, list) and detail_data:
                            stream_url = detail_data[0].get("live_link", "") or detail_data[0].get("stream_url", "")
                        elif isinstance(detail_data, dict):
                            stream_url = detail_data.get("live_link", "") or detail_data.get("stream_url", "")
                except Exception:
                    pass

                if stream_url:
                    added_channels.add(ch_id_str)
                    
                    # channel element
                    channels_xml += f'  <channel id="{ch_id_str}">\n'
                    channels_xml += f'    <display-name lang="en">{name}</display-name>\n'
                    channels_xml += f'  </channel>\n'
                    
                    # default/live program
                    programmes_xml += f'  <programme start="{start_time}" stop="{stop_time}" channel="{ch_id_str}">\n'
                    programmes_xml += f'    <title lang="en">{name} - Live Stream</title>\n'
                    programmes_xml += f'    <desc lang="en">Enjoy continuous live streaming and broadcasting on {name}.</desc>\n'
                    programmes_xml += f'  </programme>\n'
    except Exception as e:
        print(f"Error retrieving master list for EPG: {e}")

    # 2. Go to the home screen to synchronize backups
    home_url = "https://api.gizmott.com/api/v2/home"
    print("Checking additional homepage data for EPG...")
    try:
        response = requests.get(home_url, headers=headers)
        if response.status_code == 200:
            sections = response.json().get("data", [])
            for section in sections:
                shows = section.get("shows", [])
                for ch in shows:
                    ch_id = ch.get("channel_id")
                    if not ch_id:
                        continue
                    
                    ch_id_str = str(ch_id)
                    if ch_id_str in added_channels:
                        continue
                    
                    name = ch.get("show_name", "Unknown")
                    
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
                        
                        channels_xml += f'  <channel id="{ch_id_str}">\n'
                        channels_xml += f'    <display-name lang="en">{name}</display-name>\n'
                        channels_xml += f'  </channel>\n'
                        
                        programmes_xml += f'  <programme start="{start_time}" stop="{stop_time}" channel="{ch_id_str}">\n'
                        programmes_xml += f'    <title lang="en">{name} - Live Stream</title>\n'
                        programmes_xml += f'    <desc lang="en">Enjoy continuous live streaming and broadcasting on {name}.</desc>\n'
                        programmes_xml += f'  </programme>\n'
    except Exception as e:
        print(f"Error mengambil data beranda untuk EPG: {e}")

    # Combine the entire XML structure
    full_xml = '<?xml version="1.0" encoding="UTF-8"?>\n<tv>\n' + channels_xml + programmes_xml + '</tv>'

    with open("epg.xml", "w", encoding="utf-8") as f:
        f.write(full_xml)
        
    print(f"\nFile epg.xml berhasil di-generate! Total {len(added_channels)} channel dengan program EPG yang sinkron.")

if __name__ == "__main__":
    generate_epg()
