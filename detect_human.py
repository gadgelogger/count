import torch
import cv2
import os
from supabase import create_client, Client
import time
from config import supabase_url, supabase_key


# Supabaseの設定
url: str = supabase_url
key: str = supabase_key
supabase: Client = create_client(url, key)

# テーブル名とカラム情報
table_name = "count"
column_name = "person"
column_type = "int8"

# 保存先のディレクトリ
save_directory = "captured_images"

# 保存先のディレクトリが存在しない場合は作成する
os.makedirs(save_directory, exist_ok=True)

# YOLOv5モデルのロード
model = torch.hub.load('ultralytics/yolov5', 'yolov5s')

# Webカメラのキャプチャを開始
cap = cv2.VideoCapture(0)  # 0はデフォルトのカメラデバイス
time.sleep(2)

if not cap.isOpened():
    print("Webカメラを開くことができませんでした")
    exit()

# 写真を撮影する
ret, frame = cap.read()
if not ret:
    print("フレームを取得できませんでした")
    exit()

# 画像をモデルに渡して推論
results = model(frame)

# 結果の取得
results_df = results.pandas().xyxy[0]

# 人間のクラスIDは0（COCOデータセットのクラスID）
human_results = results_df[results_df['name'] == 'person']

# 人数をカウント
person_count = len(human_results)

# 既存のレコードを確認する
query = supabase.table(table_name).select('*').limit(1).execute()
existing_data = query.data

if existing_data:
    # 既存のレコードがある場合は更新する
    res = supabase.table(table_name).update({"person": person_count}).eq('person', existing_data[0]['person']).execute()
    print(f"Updated data: {res}")
else:
    # 既存のレコードがない場合は挿入する
    data = {column_name: person_count}
    res = supabase.table(table_name).insert(data).execute()
    print(f"Inserted data: {res}")

# 枠線の描画
for index, row in human_results.iterrows():
    x1, y1, x2, y2 = int(row['xmin']), int(row['ymin']), int(row['xmax']), int(row['ymax'])
    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

# 撮影した写真を保存する
image_path = os.path.join(save_directory, "captured_image.jpg")
cv2.imwrite(image_path, frame)
print(f"写真を {image_path} に保存しました")

# リソースを解放
cap.release()