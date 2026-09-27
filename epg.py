import requests
import json

def generate_epg():
    url = "https://api.gizmott.com/api/v1/schedule/fastchannelsv2?timezone=Asia%2FJakarta"
    headers = {
        "accept": "application/json, text/plain, */*",
        "access-token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjaGVjayI6dHJ1ZSwicHViaWQiOiI1MDE4MyIsInVpZCI6Ijc5MzgxMTQiLCJjb3VudHJ5X2NvZGUiOiJJIDIsImRldmljZV90eXBlIjoid2ViIiwiaWF0IjoxNzkwNTExNDE1LCJleHAiOjE3OTgyODc0MTV9.3yF9I5p_Y7m2YZZ-bYQkTxkmzR_uFhCfPwVSALIDDdw",
        "pubid": "50183",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36"
    }
    
    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n<tv>\n</tv>'
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            res_json = response.json()
            data_field = res_json.get("data", [])
            
            # Cetak tipe data dan cuplikan isi 'data' ke log untuk diinspeksi
            print(f"Tipe data 'data': {type(data_field)}")
            print(f"Cuplikan isi: {str(data_field)[:300]}")
            
            if isinstance(data_field, list):
                xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n<tv>\n'
                for item in data_field:
                    if isinstance(item, dict):
                        title = item.get("title", "Live Event")
                        desc = item.get("description", "")
                        start = item.get("start_time", "")
                        stop = item.get("end_time", "")
                        channel_id = item.get("channel_id", "channel")
                        
                        xml_content += f'  <programme start="{start}" stop="{stop}" channel="{channel_id}">\n'
                        xml_content += f'    <title lang="en">{title}</title>\n'
                        xml_content += f'    <desc lang="en">{desc}</desc>\n'
                        xml_content += f'  </programme>\n'
                xml_content += '</tv>'
    except Exception as e:
        print(f"Error parsing EPG: {e}")
        
    with open("epg.xml", "w", encoding="utf-8") as f:
        f.write(xml_content)
    print("EPG XMLTV file processed successfully!")

if __name__ == "__main__":
    generate_epg()
