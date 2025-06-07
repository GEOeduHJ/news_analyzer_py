import pandas as pd
import json

# CSV 파일 읽기
df = pd.read_csv('sigungu_coordinates.csv', encoding='utf-8-sig')

# JSON 형식으로 변환
coords_dict = {}
for _, row in df.iterrows():
    if pd.notna(row['sigungu']):
        coords_dict[row['sigungu']] = {
            'lat': row['lat'],
            'lon': row['lon']
        }

# JSON 파일로 저장
with open('sigungu_coordinates.json', 'w', encoding='utf-8') as f:
    json.dump(coords_dict, f, ensure_ascii=False, indent=2)

print("변환이 완료되었습니다.")
