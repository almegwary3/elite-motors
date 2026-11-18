import json
from pathlib import Path

# مكان ملفات الشركات
DATASET_FOLDER = Path("dataset")

# ملف البيانات النهائي
OUTPUT_FILE = Path("cars.json")

all_cars = []

# قراءة جميع ملفات JSON
for file in DATASET_FOLDER.glob("*.json"):

    try:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)

        all_cars.append({
            "brand": file.stem,
            "data": data
        })

        print(f"Loaded: {file.name}")

    except Exception as error:
        print(f"Error in {file.name}: {error}")

# حفظ البيانات المجمعة
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(all_cars, f, ensure_ascii=False, indent=2)

print("\nDataset preparation completed!")
print("Companies loaded:", len(all_cars))