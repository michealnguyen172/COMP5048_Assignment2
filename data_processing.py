from pathlib import Path
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent
RAW_FILE = PROJECT_DIR / "data" / "AirQualityUCI.csv"
OUTPUT_DIR = PROJECT_DIR / "output"

# Fixed analysis attributes used by the group
NUMERIC_ATTRIBUTES = [
    "CO(GT)",
    "PT08.S1(CO)",
    "C6H6(GT)",       # Benzene
    "PT08.S2(NMHC)",
    "NOx(GT)",
    "NO2(GT)",
    "T",
    "RH",
    "AH",
]

OUTPUT_DIR.mkdir(exist_ok=True)

# The UCI CSV uses semicolons as separators and commas as decimal marks
df = pd.read_csv(RAW_FILE, sep=";", decimal=",", encoding="utf-8")
source_rows = len(df)

# Remove fully empty columns created by the source CSV format
df = df.dropna(axis=1, how="all")

# Check that required source columns exist
required_columns = ["Date", "Time"] + NUMERIC_ATTRIBUTES
missing_columns = [column for column in required_columns if column not in df.columns]

if missing_columns:
    raise ValueError(f"Missing columns in source data: {missing_columns}")

# Remove rows with no Date and Time.
# These are blank rows in the source file, not air-quality observations.
df = df.dropna(subset=["Date", "Time"]).copy()
valid_time_rows = len(df)

# Convert UCI's -200 missing-data code into genuine missing values.
# No missing values are imputed or filled.
df[NUMERIC_ATTRIBUTES] = df[NUMERIC_ATTRIBUTES].replace(-200, pd.NA)

for column in NUMERIC_ATTRIBUTES:
    df[column] = pd.to_numeric(df[column], errors="coerce")

# Build the time-related attribute.
# timedelta also handles 24:00:00 as midnight of the following day.
date_part = pd.to_datetime(
    df["Date"],
    format="%d/%m/%Y",
    errors="coerce"
)

time_part = pd.to_timedelta(
    df["Time"].astype(str).str.replace(".", ":", regex=False),
    errors="coerce"
)

df["DateTime"] = date_part + time_part

# Helper fields used for filters and time-based visualisations
df["Hour"] = df["DateTime"].dt.hour
df["Weekday"] = df["DateTime"].dt.day_name()
df["Month"] = df["DateTime"].dt.month
df["MonthName"] = df["DateTime"].dt.month_name()

# Keep the selected attributes and helper time fields
clean_df = df[
    ["DateTime"] + NUMERIC_ATTRIBUTES + ["Hour", "Weekday", "Month", "MonthName"]
].copy()

# Save shared clean dataset
clean_df.to_csv(OUTPUT_DIR / "air_quality_clean.csv", index=False)

# Create missing-data evidence for your report
analysis_columns = ["DateTime"] + NUMERIC_ATTRIBUTES

missing_report = pd.DataFrame({
    "attribute": analysis_columns,
    "missing_count": clean_df[analysis_columns].isna().sum().values,
    "missing_percent": (
        clean_df[analysis_columns].isna().mean().values * 100
    ).round(2),
})

missing_report.to_csv(OUTPUT_DIR / "missing_data_report.csv", index=False)

print("Data processing complete.")
print(f"Rows read from source CSV: {source_rows:,}")
print(f"Valid time-stamped observations retained: {valid_time_rows:,}")
print(f"Clean dataset saved to: {OUTPUT_DIR / 'air_quality_clean.csv'}")
print("\nMissing-data summary:")
print(missing_report.to_string(index=False))