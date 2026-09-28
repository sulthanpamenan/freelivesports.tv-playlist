import requests

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
    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n<tv>\n'

    # 1. Take from the master list
    list_url = "https://api.gizmott.com/api/v1/fastchannel/list"
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
                
                name = ch.get("show_name") or ch.get("channel_name") or ch.get("name") or f"Channel {ch_id_str}"
                
                detail_url = f"https://api.gizmott.com/api/v1/fastchannel/details/{ch_id_str}"
                has_stream = False
                try:
                    detail_res = requests.get(detail_url, headers=headers)
                    if detail_res.status_code == 200:
                        detail_data = detail_res.json().get("data", [])
                        if (isinstance(detail_data, list) and detail_data and (detail_data[0].get("live_link") or detail_data[0].get("stream_url"))) or \
                           (isinstance(detail_data, dict) and (detail_data.get("live_link") or detail_data.get("stream_url"))):
                            has_stream = True
                except Exception:
                    pass

                if has_stream:
                    added_channels.add(ch_id_str)
                    xml_content += f'  <channel id="{ch_id_str}">\n'
                    xml_content += f'    <display-name lang="en">{name}</display-name>\n'
                    xml_content += f'  </channel>\n'
    except Exception as e:
        print(f"Error retrieving master list for EPG: {e}")

    # 2. Go to the home screen to synchronize backups
    home_url = "https://api.gizmott.com/api/v2/home"
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
                    
                    name = ch.get("show_name", f"Channel {ch_id_str}")
                    
                    detail_url = f"https://api.gizmott.com/api/v1/fastchannel/details/{ch_id_str}"
                    has_stream = False
                    try:
                        detail_res = requests.get(detail_url, headers=headers)
                        if detail_res.status_code == 200:
                            detail_data = detail_res.json().get("data", [])
                            if (isinstance(detail_data, list) and detail_data and (detail_data[0].get("live_link") or detail_data[0].get("stream_url"))) or \
                               (isinstance(detail_data, dict) and (detail_data.get("live_link") or detail_data.get("stream_url"))):
                                has_stream = True
                    except Exception:
                        pass

                    if has_stream:
                        added_channels.add(ch_id_str)
                        xml_content += f'  <channel id="{ch_id_str}">\n'
                        xml_content += f'    <display-name lang="en">{name}</display-name>\n'
                        xml_content += f'  </channel>\n'
    except Exception as e:
        print(f"Error retrieving EPG home page: {e}")

    xml_content += '</tv>'

    with open("epg.xml", "w", encoding="utf-8") as f:
        f.write(xml_content)
        
    print(f"The epg.xml file was successfully generated with {len(added_channels)} synchronized channels!")

if __name__ == "__main__":
    generate_epg()
