import pandas as pd

# Configuration variables
COL1 = "DOB"
COL2 = "Phone"  # Provide the name of the column with phone numbers here
CNTR_CODE = "+353"  # Country code for phone numbers
DATAFILE = "data.csv"  # CSV source


def data_extract(
        file_path,
        start_row=1,
        end_row=None,
        debug=False,
        columns=None):
    """
    Extract specific columns and rows from a CSV file, cleaning phone numbers.

    Args:
        file_path (str): Path to the CSV file.
        start_row (int): Starting row index (inclusive).
        end_row (int): Ending row index (exclusive). If None, reads to the end of the file.
        debug (bool): Print debug information if True.
        columns (list[str]): List of column names to extract.

    Returns:
        pd.DataFrame: A cleaned DataFrame with the requested rows and columns.
    """
    if debug:
        print(f"Reading file: {file_path}")

    if columns is None:
        raise ValueError("You must provide a list of column names to extract.")

    # Read the first row to normalize column names
    all_columns = pd.read_csv(file_path, nrows=0).columns.tolist()
    normalized_columns = {col.strip().lower(): col for col in all_columns}
    if debug:
        print(f"Identified column names: {all_columns}")
        print(f"Normalized column map: {normalized_columns}")

    # Match the requested columns with normalized names
    requested_columns = []
    for col in columns:
        normalized_col = col.strip().lower()
        if normalized_col in normalized_columns:
            requested_columns.append(normalized_columns[normalized_col])
        else:
            raise ValueError(f"Column '{col}' not found in the dataset.")

    if debug:
        print(f"Columns to be extracted: {requested_columns}")

    # Read the specified rows and requested columns
    data = pd.read_csv(
        file_path,
        skiprows=range(1, start_row),  # Skip rows to start at the correct row
        nrows=None if end_row is None else end_row -
                                           start_row,  # Read up to the end_row
        usecols=requested_columns,  # Use the matched columns
    )

    if debug:
        print(f"Data extracted from rows {start_row} to {end_row}:{data}")

    return data


def clean_dob(dob):
    """
    Convert DOB from yyyy-mm-dd to mmddyyyy format.

    Args:
        dob (str): The original DOB string.

    Returns:
        str: The cleaned DOB string in mmddyyyy format.
    """
    return "".join(dob.split("-"))[4:] + "".join(dob.split("-"))[:4]


def clean_phone(phone):
    """
    Clean and format the phone number.

    Args:
        phone (str): The original phone number string.

    Returns:
        str: The cleaned phone number with country code.
    """
    phone = "".join(filter(str.isdigit, phone))  # Remove non-digit characters
    if phone.startswith("0"):
        phone = phone[1:]
    return f"{CNTR_CODE}{phone}"


def generate_ids(dataframe, debug=False):
    """
    Generate IDs by concatenating cleaned DOB and Phone columns.

    Args:
        dataframe (pd.DataFrame): The DataFrame containing contact data.
        debug (bool): Print debug information if True.

    Returns:
        list: A list of concatenated IDs.
    """
    if dataframe.empty:
        print("No data to process. The DataFrame is empty.")
        return []

    ids = []
    for _, row in dataframe.iterrows():
        dob = row.get(COL1, None)
        phone = row.get(COL2, None)

        if not pd.isna(dob) and not pd.isna(phone):
            # Clean and format DOB and Phone
            clean_dob_value = clean_dob(dob)
            clean_phone_value = clean_phone(phone)

            # Create the ID by concatenating cleaned DOB and Phone
            id_value = f"{clean_dob_value}{clean_phone_value}"
            ids.append(id_value)

            if debug:
                print(f"Generated ID: {id_value}")

    return ids


def save_ids_to_file(ids, filename="output.txt", debug=False):
    """
    Save the generated IDs to a text file.

    Args:
        ids (list): List of IDs to save.
        filename (str): The output file name.
        debug (bool): Print debug information if True.

    Returns:
        None
    """
    with open(filename, "w", encoding="utf-8") as file:
        for id_value in ids:
            file.write(id_value + "\n")

    if debug:
        print(f"Saved IDs to {filename}")


# Extract data from the CSV
cleaned_data = data_extract(
    DATAFILE,
    start_row=3,
    end_row=11,
    debug=True,
    columns=[
        COL1,
        COL2])

# Generate IDs from the cleaned data
ids = generate_ids(cleaned_data, debug=True)

# Save the generated IDs to a file
save_ids_to_file(ids, filename="output.txt", debug=True)
