import json
import pandas as pd
import math
import os

# Configuration
metadata_file = "segments_16k_2/metadata_asr_v2.json"  # path to your metadata file
batch_size = 500  # number of records per batch
output_dir = "batches"  # directory to save CSV batches

# Create output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

# Read the metadata file (each line is a JSON object)
data = []
with open(metadata_file, "r", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            record = json.loads(line.strip())
            # Construct the full audio file path
            # Adjust the field names if necessary.
            record["audio_path"] = f'segments_16k/{record["filename"]}.wav'
            data.append(record)

# Create a DataFrame from the metadata
df = pd.DataFrame(data)

# Determine the number of batches needed
num_batches = math.ceil(len(df) / batch_size)
print(f"Total records: {len(df)}; Number of batches: {num_batches}")

# Split the DataFrame into batches and save each as a CSV
for i in range(num_batches):
    start = i * batch_size
    end = start + batch_size
    batch_df = df.iloc[start:end]
    batch_filename = os.path.join(output_dir, f"metadata_batch_{i+11}.csv")
    batch_df.to_csv(batch_filename, index=False, encoding="utf-8-sig")
    print(f"Saved batch {i+1} with {len(batch_df)} records to {batch_filename}")
