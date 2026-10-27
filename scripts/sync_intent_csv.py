import json
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent

# Load JSON balanced corpus
with open(BASE_DIR / "data" / "intent_dataset.json", "r", encoding="utf-8") as f:
    json_data = json.load(f)

records = []
for idx, item in enumerate(json_data, 1):
    records.append({
        "id": f"TRAIN-{idx:03d}",
        "query_text": item["text"],
        "intent": item["intent"],
        "category": "BIS Domain",
        "expected_standard": "IS Standard Reference",
        "language": "en" if not any('\u0900' <= c <= '\u097F' or '\u0B80' <= c <= '\u0BFF' for c in item["text"]) else ("hi" if any('\u0900' <= c <= '\u097F' for c in item["text"]) else "ta"),
        "sample_data_flag": "SAMPLE DATA"
    })

# Add multilingual pairs to intent dataset
extra_multi = [
    ("पानी की बोतल के लिए कौन सा भारतीय मानक लागू होता है?", "STANDARD_RECOMMENDATION", "hi"),
    ("हेलमेट के लिए कौन सा भारतीय मानक है?", "STANDARD_RECOMMENDATION", "hi"),
    ("सोने के आभूषणों के लिए हॉलमार्किंग नियम क्या हैं?", "HALLMARKING", "hi"),
    ("नकली आईएसआई मार्क के खिलाफ शिकायत कैसे दर्ज करें?", "CONSUMER", "hi"),
    ("बीआईएस केंद्रीय प्रयोगशाला कहाँ स्थित है?", "LABORATORY", "hi"),
    ("आईएसआई लाइसेंस के लिए आवेदन कैसे करें?", "CERTIFICATION", "hi"),
    ("தங்க நகைகளுக்கான ஹால்மார்க் விதிகள் என்ன?", "HALLMARKING", "ta"),
    ("ஹெல்மெட்டுக்கான இந்திய தரம் என்ன?", "STANDARD_RECOMMENDATION", "ta"),
    ("போலி ஐஎஸ்ஐ முத்திரைக்கு எதிராக புகார் செய்வது எப்படி?", "CONSUMER", "ta"),
    ("குடிநீர் பாட்டில்களுக்கான தரநிலை என்ன?", "STANDARD_RECOMMENDATION", "ta")
]

for idx_extra, (text, intent, lang) in enumerate(extra_multi, len(records) + 1):
    records.append({
        "id": f"TRAIN-{idx_extra:03d}",
        "query_text": text,
        "intent": intent,
        "category": "Multilingual BIS",
        "expected_standard": "IS Standard Reference",
        "language": lang,
        "sample_data_flag": "SAMPLE DATA"
    })

df = pd.DataFrame(records)
# Save to raw, processed, and training
df.to_csv(BASE_DIR / "data" / "raw" / "intent_dataset.csv", index=False)
df.to_csv(BASE_DIR / "data" / "processed" / "intent_dataset.csv", index=False)
df.to_csv(BASE_DIR / "data" / "training" / "intent_dataset.csv", index=False)

print(f"Successfully generated {len(df)} balanced intent samples in intent_dataset.csv!")
