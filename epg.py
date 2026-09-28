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
            print(f"Gagal mengambil data dari API, status code: {response.status_code}")
            return

        res_json = response.json()
        channels_data = res_json.get("data", {}).get("schedules", [])

        if not isinstance(channels_data, list):
            print("Format data jadwal dari API tidak valid.")
            return

        channels_map = {}
        valid_programmes = []

        for channel_item in channels_data:
            if not isinstance(channel_item, dict):
                continue
                
            # Ambil ID dan Nama Channel
            channel_id = str(channel_item.get("channel_id") or channel_item.get("id") or "channel")
            channel_name = (
                channel_item.get("channel_name")
                or channel_item.get("name")
                or f"Channel {channel_id}"
            )
            channels_map[channel_id] = channel_name

            # Ambil daftar program di dalam channel (mendukung key 'schedules', 'programs', atau 'events')
            progs = channel_item.get("schedules") or channel_item.get("programs") or channel_item.get("events")
            
            # Fallback jika struktur dari API ternyata berupa list program datar
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

        # Proses penulisan file XMLTV
        with open("epg.xml", "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write("<tv>\n")

            # Tulis elemen channel
            for ch_id, ch_name in channels_map.items():
                f.write(f'  <channel id="{ch_id}">\n')
                f.write(f'    <display-name lang="en">{html.escape(ch_name)}</display-name>\n')
                f.write('  </channel>\n')

            # Tulis elemen programme
            for prog in valid_programmes:
                f.write(f'  <programme start="{prog["start"]}" stop="{prog["stop"]}" channel="{prog["channel"]}">\n')
                f.write(f'    <title lang="en">{prog["title"]}</title>\n')
                if prog["desc"]:
                    f.write(f'    <desc lang="en">{prog["desc"]}</desc>\n')
                f.write('  </programme>\n')

            f.write("</tv>\n")

        print(f"Berhasil! Total Channel: {len(channels_map)}, Total Program: {len(valid_programmes)}")

    except requests.exceptions.Timeout:
        print("Error: Koneksi ke API Gizmott timeout (waktu habis).")
    except requests.exceptions.RequestException as e:
        print(f"Error jaringan terjadi: {e}")
    except Exception as e:
        print(f"Terjadi kesalahan saat memproses EPG: {e}")

if __name__ == "__main__":
    generate_epg()
