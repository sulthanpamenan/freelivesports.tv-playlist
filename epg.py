from datetime import datetime
import html
import os
import requests

def generate_epg():
    url = "https://api.gizmott.com/api/v1/schedule/fastchannelsv2?timezone=Asia%2FJakarta"
    access_token = os.getenv("GIZMOTT_ACCESS_TOKEN", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjaGVjayI6dHJ1ZSwicHViaWQiOiI1MDE4MyIsInVpZCI6Ijc5MzgxMTQiLCJjb3VudHJ5X2NvZGUiOiJJIDIsImRldmljZV90eXBlIjoid2ViIiwiaWF0IjoxNzkwNSExNDE1LCJleHAiOjE3OTgyODc0MTV9.3yF9I5p_Y7m2YZZ-bYQkTxkmzR_uFhCfPwVSALIDDdw")
    headers = {
        "accept": "application/json, text/plain, */*",
        "access-token": access_token,
        "pubid": "50183",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36",
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"Failed to retrieve data from the API, status code: {response.status_code}")
            return

        res_json = response.json()
        schedules = res_json.get("data", {}).get("schedules", [])

        if not isinstance(schedules, list):
            print("The schedule data format from the API is invalid.")
            return

        channels_map = {}
        valid_programmes = []

        for item in schedules:
            if not isinstance(item, dict):
                continue
                
            channel_id = str(item.get("channel_id", "channel"))
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

            if channel_id not in channels_map:
                channel_name = (
                    item.get("channel_name")
                    or item.get("name")
                    or f"Channel {channel_id}"
                )
                channels_map[channel_id] = channel_name

            valid_programmes.append({
                "channel": channel_id,
                "start": start_fmt,
                "stop": stop_fmt,
                "title": html.escape(str(title)),
                "desc": html.escape(str(desc)),
            })

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

        print("EPG XMLTV file successfully created!")

    except requests.exceptions.Timeout:
        print("Error: Connection to the Gizmott API timed out.")
    except requests.exceptions.RequestException as e:
        print(f"A network error occurred: {e}")
    except Exception as e:
        print(f"An error occurred while processing the EPG: {e}")

if __name__ == "__main__":
    generate_epg()
