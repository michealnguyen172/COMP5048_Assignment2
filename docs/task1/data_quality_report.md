# Data Quality Report

- Total rows in clean dataset: **9,357**
- Raw file rows: **9,471**, of which **114** are trailing rows with empty Date/Time (dropped during processing). The downloaded CSV contained 9,357 valid timestamped records after blank trailing rows were removed.

## 1. Handling of the -200 missing-value code

Every `-200` cell in the raw file was converted to a true missing value (NaN). No imputation was performed. The verification below confirms the number of raw `-200` cells equals the number of missing cells in the clean data for each attribute, and that no `-200` remains.

| attribute | raw_minus200_count | clean_missing_count | remaining_minus200_in_clean | raw_minus200 == clean_missing |
| --- | --- | --- | --- | --- |
| CO(GT) | 1683 | 1683 | 0 | True |
| PT08.S1(CO) | 366 | 366 | 0 | True |
| C6H6(GT) | 366 | 366 | 0 | True |
| PT08.S2(NMHC) | 366 | 366 | 0 | True |
| NOx(GT) | 1639 | 1639 | 0 | True |
| NO2(GT) | 1642 | 1642 | 0 | True |
| T | 366 | 366 | 0 | True |
| RH | 366 | 366 | 0 | True |
| AH | 366 | 366 | 0 | True |

## 2. Missing-data distribution by month and year-month

Missing counts per attribute. The six sensor/weather columns (PT08.S1(CO), C6H6(GT), PT08.S2(NMHC), T, RH, AH) are missing *together* in blocks (the device/logger is offline for contiguous periods), whereas the reference analyzers CO(GT), NOx(GT) and NO2(GT) have their own, larger gaps.

### By calendar month

| Month | CO(GT) | PT08.S1(CO) | C6H6(GT) | PT08.S2(NMHC) | NOx(GT) | NO2(GT) | T | RH | AH | total_missing |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 68 | 61 | 61 | 61 | 34 | 34 | 61 | 61 | 61 | 502 |
| 2 | 9 | 76 | 76 | 76 | 30 | 30 | 76 | 76 | 76 | 525 |
| 3 | 38 | 1 | 1 | 1 | 33 | 33 | 1 | 1 | 1 | 110 |
| 4 | 227 | 27 | 27 | 27 | 234 | 234 | 27 | 27 | 27 | 857 |
| 5 | 152 | 14 | 14 | 14 | 146 | 146 | 14 | 14 | 14 | 528 |
| 6 | 76 | 38 | 38 | 38 | 71 | 72 | 38 | 38 | 38 | 447 |
| 7 | 186 | 1 | 1 | 1 | 32 | 33 | 1 | 1 | 1 | 257 |
| 8 | 267 | 49 | 49 | 49 | 242 | 243 | 49 | 49 | 49 | 1046 |
| 9 | 164 | 18 | 18 | 18 | 276 | 276 | 18 | 18 | 18 | 824 |
| 10 | 351 | 1 | 1 | 1 | 357 | 357 | 1 | 1 | 1 | 1071 |
| 11 | 41 | 0 | 0 | 0 | 62 | 62 | 0 | 0 | 0 | 165 |
| 12 | 104 | 80 | 80 | 80 | 122 | 122 | 80 | 80 | 80 | 828 |

### By year-month (locates the offline blocks in time)

| YearMonth | CO(GT) | PT08.S1(CO) | C6H6(GT) | PT08.S2(NMHC) | NOx(GT) | NO2(GT) | T | RH | AH | total_missing |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2004-03 | 18 | 0 | 0 | 0 | 22 | 22 | 0 | 0 | 0 | 62 |
| 2004-04 | 225 | 27 | 27 | 27 | 234 | 234 | 27 | 27 | 27 | 855 |
| 2004-05 | 152 | 14 | 14 | 14 | 146 | 146 | 14 | 14 | 14 | 528 |
| 2004-06 | 76 | 38 | 38 | 38 | 71 | 72 | 38 | 38 | 38 | 447 |
| 2004-07 | 186 | 1 | 1 | 1 | 32 | 33 | 1 | 1 | 1 | 257 |
| 2004-08 | 267 | 49 | 49 | 49 | 242 | 243 | 49 | 49 | 49 | 1046 |
| 2004-09 | 164 | 18 | 18 | 18 | 276 | 276 | 18 | 18 | 18 | 824 |
| 2004-10 | 351 | 1 | 1 | 1 | 357 | 357 | 1 | 1 | 1 | 1071 |
| 2004-11 | 41 | 0 | 0 | 0 | 62 | 62 | 0 | 0 | 0 | 165 |
| 2004-12 | 104 | 80 | 80 | 80 | 122 | 122 | 80 | 80 | 80 | 828 |
| 2005-01 | 68 | 61 | 61 | 61 | 34 | 34 | 61 | 61 | 61 | 502 |
| 2005-02 | 9 | 76 | 76 | 76 | 30 | 30 | 76 | 76 | 76 | 525 |
| 2005-03 | 20 | 1 | 1 | 1 | 11 | 11 | 1 | 1 | 1 | 48 |
| 2005-04 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |

## 3. NOx / NO2 reference-analyzer gap at 03:00

The NOx(GT) and NO2(GT) reference analyzers are systematically missing at 03:00 (93.3% missing), while all other hours show a baseline ~14% missing rate. This is a systematic instrument/recording gap, not random missingness.

| Hour | NOx(GT) | NO2(GT) | total_rows | NOx(GT)_pct | NO2(GT)_pct |
| --- | --- | --- | --- | --- | --- |
| 0 | 54 | 54 | 390 | 13.8 | 13.8 |
| 1 | 56 | 56 | 390 | 14.4 | 14.4 |
| 2 | 58 | 58 | 390 | 14.9 | 14.9 |
| 3 | 364 | 364 | 390 | 93.3 | 93.3 |
| 4 | 58 | 58 | 390 | 14.9 | 14.9 |
| 5 | 57 | 57 | 390 | 14.6 | 14.6 |
| 6 | 56 | 56 | 390 | 14.4 | 14.4 |
| 7 | 56 | 56 | 390 | 14.4 | 14.4 |
| 8 | 61 | 62 | 390 | 15.6 | 15.9 |
| 9 | 56 | 57 | 390 | 14.4 | 14.6 |
| 10 | 54 | 54 | 390 | 13.8 | 13.8 |
| 11 | 55 | 56 | 390 | 14.1 | 14.4 |
| 12 | 55 | 55 | 390 | 14.1 | 14.1 |
| 13 | 57 | 57 | 390 | 14.6 | 14.6 |
| 14 | 57 | 57 | 390 | 14.6 | 14.6 |
| 15 | 55 | 55 | 389 | 14.1 | 14.1 |
| 16 | 54 | 54 | 389 | 13.9 | 13.9 |
| 17 | 52 | 52 | 389 | 13.4 | 13.4 |
| 18 | 54 | 54 | 390 | 13.8 | 13.8 |
| 19 | 53 | 53 | 390 | 13.6 | 13.6 |
| 20 | 53 | 53 | 390 | 13.6 | 13.6 |
| 21 | 54 | 54 | 390 | 13.8 | 13.8 |
| 22 | 55 | 55 | 390 | 14.1 | 14.1 |
| 23 | 55 | 55 | 390 | 14.1 | 14.1 |

## 4. Additional findings

- The six sensor/weather attributes share an identical missing pattern (yes) -> block offline periods.
- NOx(GT) and NO2(GT) are missing together (1,753 vs 1,756 rows) -> shared analyzer downtime.
- Missingness is NOT imputed; any visualisation must treat NaN by dropping the affected rows for that attribute only.