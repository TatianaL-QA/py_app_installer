import pandas as pd

# Configuration variables
PHONE_CL = "Phone"  # Provide the name of the column with phone numbers here
CNTR_CODE = "+353"  # Country code for phone numbers


def data_extract(file_path, start_row=1, end_row=None, debug=False, columns=None):
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
        nrows=None if end_row is None else end_row - start_row,  # Read up to the end_row
        usecols=requested_columns,  # Use the matched columns
    )

    if debug:
        print(f"Data extracted from rows {start_row} to {end_row}:\n{data}")

    # Clean the phone numbers if the phone column is among the columns
    if PHONE_CL in data.columns:
        data[PHONE_CL] = data[PHONE_CL].str.replace(r'\s+|\t|["]', '', regex=True)
        if debug:
            print(f"Cleaned phone numbers:\n{data[PHONE_CL]}")

    return data


def data_to_vcf(dataframe, output="contacts{number_of_rows}.vcs", debug=False):
    """
    Convert a DataFrame of contact data into vCard format and save to a file.

    Args:
        dataframe (pd.DataFrame): The DataFrame containing contact data.
        output (str): The filename format for saving the vCard file. Use {number_of_rows}
                      to dynamically include the number of rows.
        debug (bool): Print debug information if True.

    Returns:
        None
    """
    if dataframe.empty:
        print("No contacts to process. The DataFrame is empty.")
        return

    vcf_content = ""
    for _, row in dataframe.iterrows():
        name = row.get("Name", "Unknown")  # Use "Unknown" if Name is missing
        phone = row.get(PHONE_CL, None)

        # Skip entries without valid phone numbers
        if not phone:
            continue

        # Format the phone number for vCard
        phone = CNTR_CODE + phone.lstrip('0').replace("-", "")

        # Construct the vCard format
        vcard = (
            "BEGIN:VCARD\n"
            "VERSION:3.0\n"
            f"FN:{name}\n"
            f"TEL;TYPE=CELL:{phone}\n"
            "END:VCARD\n"
        )
        vcf_content += vcard + "\n"

        if debug:
            print(f"Generated vCard for {name}:\n{vcard}")

    # Calculate the number of contacts processed
    number_of_rows = len(dataframe)

    # Format the output filename
    output_filename = output.format(number_of_rows=number_of_rows)

    # Save the vCard content to the file
    with open(output_filename, "w", encoding="utf-8") as file:
        file.write(vcf_content)

    if debug:
        print(f"Saved vCard file to {output_filename}")


cleaned_data = data_extract("dirty_test_file.csv", start_row=3, end_row=11, debug=True, columns=["Name", PHONE_CL])
data_to_vcf(cleaned_data, output="IrelandContacts_{number_of_rows}.vcf", debug=True)
