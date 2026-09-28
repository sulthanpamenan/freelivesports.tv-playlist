from datetime import datetime
import html
import os
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
            return response.json().get("token")
    except Exception:
        pass
    return None

def generate_epg():
    token = os.getenv("GIZMOTT_ACCESS_TOKEN") or authenticate_guest()
    if not token:
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjaGVjayI6dHJ1ZSwicHViaWQiOiI1MDE4MyIsInVpZCI6Ijc5MzgxMTQiLCJjb3VudHJ5X2NvZGUiOiJJIDIsImRldmljZV90eXBlIjoid2ViIiwiaWF0IjoxNzkwNSExNDE1LCJleHAiOjE3OTgyODc0MTV9.3yF9I5p_Y7m2YZZ-bYQkTxkmzR_uFhCfPwVSALIDDdw"

    headers = {
        "accept": "application/json, text/plain, */*",
        "access-token": token,
        "pubid": "50183",
        "channelid": "516",
        "country_code": "ID",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36",
    }

    # 1. Create a channel ID mapping
    channels_map = {}
    
    print("Retrieving channel name list for EPG...")
    try:
        list_res = requests.get("https://api.gizmott.com/api/v1/fastchannel/list", headers=headers, timeout=15)
        if list_res.status_code == 200:
            for ch in list_res.json().get("data", []):
                ch_id = str(ch.get("channel_id") or ch.get("id") or "")
                ch_name = ch.get("show_name") or ch.get("channel_name") or ch.get("name")
                if ch_id and ch_name:
                    channels_map[ch_id] = ch_name
    except Exception as e:
        print(f"Warning when retrieving the master list: {e}")

    try:
        home_res = requests.get("https://api.gizmott.com/api/v2/home", headers=headers, timeout=15)
        if home_res.status_code == 200:
            for section in home_res.json().get("data", []):
                for ch in section.get("shows", []):
                    ch_id = str(ch.get("channel_id") or "")
                    ch_name = ch.get("show_name")
                    if ch_id and ch_name and ch_id not in channels_map:
                        channels_map[ch_id] = ch_name
    except Exception as e:
        print(f"Warning while retrieving home data: {e}")

    # 2. Retrieve the schedule data
    url = "https://api.gizmott.com/api/v1/schedule/fastchannelsv2?timezone=Asia%2FJakarta"
    try:
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"Failed to retrieve schedule data from the API, status code: {response.status_code}")
            return

        res_json = response.json()
        channels_data = res_json.get("data", {}).get("schedules", [])

        if not isinstance(channels_data, list):
            print("The schedule data format from the API is invalid.")
            return

        valid_programmes = []

        for channel_item in channels_data:
            if not isinstance(channel_item, dict):
                continue
                
            channel_id = str(
                channel_item.get("channel_id") 
                or channel_item.get("id") 
                or channel_item.get("channelId") 
                or "channel"
            )
            
            if channel_id not in channels_map:
                fallback_name = (
                    channel_item.get("channel_name")
                    or channel_item.get("name")
                    or channel_item.get("channelName")
                    or channel_item.get("channel_title")
                    or f"Channel {channel_id}"
                )
                channels_map[channel_id] = fallback_name

            progs = channel_item.get("schedules") or channel_item.get("programs") or channel_item.get("events")
            if not progs:
                progs = [channel_item]

            for item in progs:
                if not isinstance(item, dict):
                    continue

                title = item.get("title", "Live Event")
                desc = item.get("description", "")

                if not desc or desc.strip().lower() in ["none", "null"]:
                    desc = ""

                start = item.get("start", "")
                stop = item.get("end", "")

                try:
                    dt_start = datetime.fromisoformat(start.replace("Z", "+00:00"))
                    dt_stop = datetime.fromisoformat(stop.replace("Z", "+00:00"))

                    if dt_stop <= dt_start:
                        continue

                    start_fmt = dt_start.strftime("%Y%m%d%H%M%S %z").strip()
                    stop_fmt = dt_stop.strftime("%Y%m%d%H%M%S %z").strip()
                except Exception:
                    start_fmt = start
                    stop_fmt = stop

                valid_programmes.append({
                    "channel": channel_id,
                    "start": start_fmt,
                    "stop": stop_fmt,
                    "title": html.escape(str(title)),
                    "desc": html.escape(str(desc)),
                })

        # 3. Write the epg.xml file
        with open("epg.xml", "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write("<tv>\n")

            for ch_id, ch_name in channels_map.items():
                f.write(f'  <channel id="{ch_id}">\n')
                f.write(f'    <display-name lang="en">{html.escape(ch_name)}</display-name>\n')
                f.write('  </channel>\n')

            for prog in valid_programmes:
                f.write(f'  <programme start="{prog["start"]}" stop="{prog["stop"]}" channel="{prog["channel"]}">\n')
                f.write(f'    <title lang="en">{prog["title"]}</title>\n')
                if prog["desc"]:
                    f.write(f'    <desc lang="en">{prog["desc"]}</desc>\n')
                f.write('  </programme>\n')

            f.write("</tv>\n")

        print(f"Success! Total channels in EPG: {len(channels_map)}, Total programs: {len(valid_programmes)}")

    except requests.exceptions.Timeout:
        print("Error: Connection to the Gizmott API timed out.")
    except requests.exceptions.RequestException as e:
        print(f"A network error occurred: {e}")
    except Exception as e:
        print(f"An error occurred while processing the EPG: {e}")

if __name__ == "__main__":
    generate_epg()
