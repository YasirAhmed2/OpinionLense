import pandas as pd
import re
import string
from sklearn.model_selection import train_test_split
import os

# Cleaning Function
# -------------------
def clean_text(text: str) -> str:
    """
    Cleans YouTube comments:
    - Lowercase
    - Remove links, mentions, hashtags
    - Remove punctuation & numbers
    - Strip extra spaces
    """
    text = str(text).lower()
    text = re.sub(r"http\S+|www\S+|https\S+", "", text)   # remove links
    text = re.sub(r"@\w+|\#", "", text)                   # remove mentions/hashtags
    text = text.translate(str.maketrans("", "", string.punctuation))  # remove punctuation
    text = re.sub(r"\d+", "", text)                       # remove numbers
    text = re.sub(r"\s+", " ", text).strip()              # remove extra spaces
    return text

# -------------------
# Preprocessing Function
# -------------------
def preprocess_dataset(input_path="data/raw_comments.csv",
                       output_dir="data",
                       sample_size=None):
    """
    Loads raw YouTube comments, cleans them, and saves train/test datasets.
    """
    print("🔹 Loading dataset...")
    df = pd.read_csv(input_path)

    if "comment" not in df.columns:
        raise ValueError("❌ The dataset must contain a 'comment' column!")

    # Clean text
    print("🔹 Cleaning comments...")
    df["clean_comment"] = df["comment"].apply(clean_text)

    # Drop empty rows
    df = df[df["clean_comment"].str.strip() != ""]

    # Optional: sample (to reduce dataset size for experiments)
    if sample_size:
        df = df.sample(n=sample_size, random_state=42)

    # Split dataset
    train, test = train_test_split(df, test_size=0.2, random_state=42)

    # Ensure output dir exists
    os.makedirs(output_dir, exist_ok=True)

    # Save files
    train.to_csv(os.path.join(output_dir, "train.csv"), index=False)
    test.to_csv(os.path.join(output_dir, "test.csv"), index=False)

    print(f"✅ Preprocessing complete! Train: {len(train)} | Test: {len(test)}")

    return train, test

# -------------------
# Run from CLI
# -------------------
if __name__ == "__main__":
    preprocess_dataset("data/raw_comments.csv", "data", sample_size=100000)