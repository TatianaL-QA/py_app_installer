import pandas as pd


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
        print(f"Data extracted from rows {start_row} to {end_row}:\n{data}")

    # Clean the phone numbers if 'Phone' is among the columns
    if 'Phone' in data.columns:
        data['Phone'] = data['Phone'].str.replace(
            r'\s+|\t|["]', '', regex=True)  # Remove tabs, whitespaces, and quotes
        if debug:
            print(f"Cleaned phone numbers:\n{data['Phone']}")

    return data


def data_to_vcf(dataframe, CNTR_CODE="+353", debug=False):
    """
    Convert the cleaned DataFrame to vCard format.

    Args:
        dataframe (pd.DataFrame): Cleaned DataFrame with Name and Phone columns.
        CNTR_CODE (str): Country code to prefix the phone number.
        debug (bool): Print debug information if True.

    Returns:
        str: vCard formatted string for all contacts.
    """
    if debug:
        print("Starting vCard creation...")

    vcards = []

    for _, row in dataframe.iterrows():
        name = row.get('Name', 'Unknown')
        phone = row.get('Phone', '')

        # Process the phone number
        if phone.startswith("0"):
            phone = phone[1:]  # Remove leading zero
        phone = phone.replace("-", "").lstrip("0")  # Remove hyphens, left 0
        phone = f"{CNTR_CODE}{phone}"  # Add country code

        # Construct the vCard
        vcard = (
            "BEGIN:VCARD\n"
            "VERSION:3.0\n"
            f"FN:{name}\n"
            f"TEL;TYPE=CELL:{phone}\n"
            "END:VCARD\n"
        )
        vcards.append(vcard)

        if debug:
            print(f"Created vCard for {name}:\n{vcard}")

    # Combine all vCards into a single string
    vcard_result = "\n".join(vcards)

    if debug:
        print("All vCards created successfully.")
        print(vcard_result)

    return vcard_result


# Example usage:
if __name__ == "__main__":
    # Extract data
    cleaned_data = data_extract(
        "dirty_test_file.csv",
        start_row=5,
        end_row=8,
        debug=True,
        columns=[
            "Name",
            "Phone"])
    # Generate vCards
    vcard_output = data_to_vcf(cleaned_data, CNTR_CODE="+353", debug=True)
    # Save to a file or print
    with open("contacts.vcf", "w") as file:
        file.write(vcard_output)
