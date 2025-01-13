import pandas as pd

DATAFILE1 = "data.csv"  # First CSV
DATAFILE2 = "additional_data.csv"  # Second CSV
OUTPUT_FILE = "output_with_values.csv"  # Output file for matched rows
OUTPUT_NO_VALUES_FILE = "output_no_values.csv"  # Output file for unmatched rows

TABLE1_KEY = "regnumber"  # Key column in the first table
TABLE2_KEY = "regnum"  # Key column in the second table (must match TABLE1_KEY)
TABLE1_COLUMNS = ["name", "phone", "regnumber"]  # Columns to include from the first file
TABLE2_COLUMNS = ["uuid", "userid"]  # Columns to include from the second file
SYSTEM_COLUMN = "system"  # Column indicating the system type in the second file
TARGET_SYSTEM = "SYS2"  # The specific system value to filter by


def merge_with_system_filtering(
        file1, file2, output_file, output_no_values_file,
        table1_key, table2_key, table1_columns, table2_columns,
        system_column, target_system, debug=False
):
    """
    Merge two CSV files based on a common column and an additional filtering condition.

    Args:
        file1 (str): Path to the first CSV file.
        file2 (str): Path to the second CSV file.
        output_file (str): Path to the output file for matched rows.
        output_no_values_file (str): Path to the output file for unmatched rows.
        table1_key (str): Key column in the first table.
        table2_key (str): Key column in the second table.
        table1_columns (list): Columns to include from the first file.
        table2_columns (list): Columns to include from the second file.
        system_column (str): Column to filter by in the second table.
        target_system (str): Value to match in the `system_column`.
        debug (bool): Print debug information if True.
    """
    if debug:
        print(f"Loading files:\n  File1: {file1}\n  File2: {file2}")

    df1 = pd.read_csv(file1)
    df2 = pd.read_csv(file2)

    if debug:
        print(f"First file columns: {df1.columns.tolist()}")
        print(f"Second file columns: {df2.columns.tolist()}")

    for col in table1_columns:
        if col not in df1.columns:
            raise ValueError(f"Column '{col}' not found in the first file.")

    for col in [table2_key, system_column] + table2_columns:
        if col not in df2.columns:
            raise ValueError(f"Column '{col}' not found in the second file.")

    filtered_df2 = df2[df2[system_column] == target_system]

    if debug:
        print(f"Filtered second file based on '{system_column} == {target_system}':\n{filtered_df2}")

    merged = pd.merge(
        df1, filtered_df2, left_on=table1_key, right_on=table2_key, how="left", suffixes=("_1", "_2")
    )

    if debug:
        print(f"Merged data preview:\n{merged.head()}")

    matched = merged.dropna(subset=table2_columns)  # Drop rows where any table2 column is missing
    unmatched = merged[merged[table2_columns].isna().any(axis=1)]  # Rows with missing table2 columns

    if debug:
        print(f"Matched rows:\n{matched.head()}")
        print(f"Unmatched rows:\n{unmatched.head()}")

    matched_columns = table1_columns + table2_columns
    matched_output = matched[matched_columns]
    matched_output.to_csv(output_file, index=False)

    if debug:
        print(f"Matched rows saved to {output_file}")

    unmatched_output = unmatched[table1_columns]
    unmatched_output.to_csv(output_no_values_file, index=False)

    if debug:
        print(f"Unmatched rows saved to {output_no_values_file}")


merge_with_system_filtering(
    DATAFILE1, DATAFILE2, OUTPUT_FILE, OUTPUT_NO_VALUES_FILE,
    TABLE1_KEY, TABLE2_KEY, TABLE1_COLUMNS, TABLE2_COLUMNS,
    SYSTEM_COLUMN, TARGET_SYSTEM, debug=True
)
