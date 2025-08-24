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