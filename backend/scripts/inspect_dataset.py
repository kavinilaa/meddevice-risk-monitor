import os
import pandas as pd

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))

def inspect_file(filepath):
    filename = os.path.basename(filepath)
    print(f"\n{'='*70}")
    print(f"FILE: {filename}")
    print(f"Size: {os.path.getsize(filepath):,} bytes")
    print(f"{'='*70}")
    
    # Read first 5000 rows for structure and count total rows
    df_sample = pd.read_csv(filepath, nrows=5)
    print("Columns and Types:")
    for col in df_sample.columns:
        print(f" - {col} ({df_sample[col].dtype})")
    
    # Read full file for stats
    df = pd.read_csv(filepath, low_memory=False)
    print(f"\nTotal Rows: {len(df):,}")
    print(f"Total Columns: {len(df.columns)}")
    
    print("\nMissing Values:")
    for col in df.columns:
        missing = df[col].isnull().sum()
        pct = (missing / len(df)) * 100
        print(f" - {col}: {missing:,} ({pct:.1f}%)")
        
    print("\nSample (First 2 records):")
    print(df.head(2).to_dict(orient="records"))
    
    # Check key columns
    print("\nUnique count of key columns:")
    for col in df.columns:
        if df[col].nunique() < 50:
            print(f" - {col} unique values ({df[col].nunique()}): {list(df[col].dropna().unique()[:10])}")
        else:
            print(f" - {col} unique count: {df[col].nunique():,}")

def main():
    print(f"Looking for dataset files in: {DATA_DIR}")
    if not os.path.exists(DATA_DIR):
        print(f"Directory not found: {DATA_DIR}")
        return
        
    for fname in sorted(os.listdir(DATA_DIR)):
        if fname.endswith(".csv"):
            inspect_file(os.path.join(DATA_DIR, fname))

if __name__ == "__main__":
    main()
