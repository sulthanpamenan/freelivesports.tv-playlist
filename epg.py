from datetime import datetime
import html
import requests


def generate_epg():
    url = "https://api.gizmott.com/api/v1/schedule/fastchannelsv2?timezone=Asia%2FJakarta"

    access_token = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjaGVjayI6dHJ1ZSwicHViaWQiOiI1MDE4MyIsInVpZCI6Ijc5MzgxMTQiLCJjb3VudHJ5X2NvZGUiOiJJIDIsImRldmljZV90eXBlIjoid2ViIiwiaWF0IjoxNzkwNSExNDE1LCJleHAiOjE3OTgyODc0MTV9.3yF9I5p_Y7m2YZZ-bYQkTxkmzR_uFhCfPwVSALIDDdw"
    )

    headers = {
        "accept": "application/json, text/plain, */*",
        "access-token": access_token,
        "pubid": "50183",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36",
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            res_json = response.json()
            data_field = res_json.get("data", {})
            schedules = data_field.get("schedules", [])

            channels_map = {}
            valid_programmes = []

            if isinstance(schedules, list):
                for item in schedules:
                    if isinstance(item, dict):
                        channel_id = str(item.get("channel_id", "channel"))
                        title = item.get("title", "Live Event")
                        desc = item.get("description", "")

                        if not desc or desc.strip().lower() == "none":
                            desc = ""

                        start = item.get("start", "")
                        stop = item.get("end", "")

                        try:
                            dt_start = datetime.fromisoformat(
                                start.replace("Z", "+00:00")
                            )
                            dt_stop = datetime.fromisoformat(
                                stop.replace("Z", "+00:00")
                            )

                            if dt_stop <= dt_start:
                                continue

                            start_fmt = dt_start.strftime(
                                "%Y%m%d%H%M%S %z"
                            ).strip()
                            stop_fmt = dt_stop.strftime(
                                "%Y%m%d%H%M%S %z"
                            ).strip()
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
                            "title": html.escape(title),
                            "desc": html.escape(desc),
                        })

                xml_lines = ['<?xml version="1.0" encoding="UTF-8"?>', "<tv>"]

                for ch_id, ch_name in channels_map.items():
                    xml_lines.append(
                        f'  <channel id="{ch_id}">\n    <display-name lang="en">{html.escape(ch_name)}</display-name>\n  </channel>'
                    )

                for prog in valid_programmes:
                    prog_lines = [
                        f'  <programme start="{prog["start"]}" stop="{prog["stop"]}" channel="{prog["channel"]}">',
                        f'    <title lang="en">{prog["title"]}</title>',
                    ]
                    if prog["desc"]:
                        prog_lines.append(
                            f'    <desc lang="en">{prog["desc"]}</desc>'
                        )

                    prog_lines.append("  </programme>")
                    xml_lines.append("\n".join(prog_lines))

                xml_lines.append("</tv>")
                
                xml_content = "\n".join(xml_lines)

                with open("epg.xml", "w", encoding="utf-8") as f:
                    f.write(xml_content)
                print("EPG XMLTV file successfully generated and optimized!")
            else:
                print("The schedule data format in the API is invalid.")
        else:
            print(
                f"Failed to retrieve data from the API, status code: {response.status_code}"
            )
    except Exception as e:
        print(f"Error creating EPG: {e}")


if __name__ == "__main__":
    generate_epg()
