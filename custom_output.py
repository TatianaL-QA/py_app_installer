def generate_custom_strings(dataframe, output_file="custom_output.txt", debug=False):
    """
    Generate concatenated strings for each row of the data based on specified rules.

    Args:
        dataframe (pd.DataFrame): The DataFrame containing contact data.
        output_file (str): The file where the generated strings will be saved.
        debug (bool): Print debug information if True.

    Returns:
        None
    """
    # User-provided constant strings
    STR1 = "my string1"
    STR2 = "my string2"

    # Check if the DataFrame is empty
    if dataframe.empty:
        print("No data to process. The DataFrame is empty.")
        return

    # Open the output file for writing
    with open(output_file, "w", encoding="utf-8") as file:
        for _, row in dataframe.iterrows():
            # Extract and clean the necessary columns
            phone = row.get("Phone", None)
            dob = row.get("DOB", None)
            name = row.get("Name", "Unknown")  # Default to "Unknown" if missing
            sname = row.get("Sname", "Unknown")  # Default to "Unknown" if missing
            car_reg = row.get("CarReg", "Unknown")  # Default to "Unknown" if missing

            if pd.isna(phone) or pd.isna(dob):
                if debug:
                    print(f"Skipping row due to missing data: Phone={phone}, DOB={dob}")
                continue

            # Clean and format the DOB and Phone
            cleaned_dob = clean_dob(dob, debug=debug)  # Uses existing clean_dob function
            cleaned_phone = clean_phone(phone, debug=debug)  # Uses existing clean_phone function

            # Concatenate strings as per requirements
            STR3 = f"{cleaned_dob}{cleaned_phone}"
            output_string = f"{STR1};{cleaned_phone};{STR2};{name};{sname};{STR3};{car_reg};\n"

            # Write the output string to the file
            file.write(output_string)

            if debug:
                print(f"Generated string: {output_string.strip()}")

    if debug:
        print(f"Saved custom strings to {output_file}")
