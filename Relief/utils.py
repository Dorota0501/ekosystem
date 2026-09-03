import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXCEL_PATH = PROJECT_ROOT / "dane.xlsx"
FOREST_SHARE_PATH = PROJECT_ROOT / "Udzial lasu.xlsx"
PREPARED_DATASETS_DIR = PROJECT_ROOT / "prepared_datasets"

SHEETS = {
    "woda": 1,
    "rosliny": 2,
    "ssaki": 3,
    "ptaki": 4,
    "bezkregowce": 5,
}

EXCEL_NAME_COLUMN_POSITION = 0
EXCEL_FEATURE_START_POSITION = 1
NUMBER_OF_FEATURES = 30

CSV_NAME_COLUMN_POSITION = 0
CSV_CLASS_COLUMN_POSITION = 32

FOREST_NAME_COLUMN_POSITION = 0
FOREST_SHARE_COLUMN_POSITION = 1
FOREST_TYPE_COLUMN_POSITION = 2
VALID_FOREST_TYPES = ("LS", "NL")


def load_data(data_file=EXCEL_PATH):
    """
    Load all datasets from the Excel file.

    ```
    Each dataset is loaded from a predefined worksheet specified
    in the SHEETS dictionary.

    Parameters
    ----------
    data_file : str or pathlib.Path, optional
        Path to the Excel file containing all datasets.

    Returns
    -------
    dict
        Dictionary containing the loaded datasets.

        Example:

        {
            "woda": DataFrame,
            "rosliny": DataFrame,
            "ssaki": DataFrame,
            "ptaki": DataFrame,
            "bezkregowce": DataFrame
        }

    Raises
    ------
    FileNotFoundError
        If the Excel file does not exist.
    """

    data_file = Path(data_file)

    if not data_file.exists():
        raise FileNotFoundError(
            f"Excel file not found: {data_file}"
        )

    dataframes = {}

    for dataset_name, sheet_number in SHEETS.items():
        # Load the dataset from the specified Excel worksheet.
        df = pd.read_excel(data_file, sheet_name=sheet_number, engine="openpyxl")

        dataframes[dataset_name] = df

    return dataframes


def load_classes(class_file):
    """
    Load object identifiers and decision classes from a CSV file.

    Only two columns are used from the CSV file:

        Column position 0:
            Object identifier.

        Column position 32:
            Decision class.

    All remaining CSV columns are ignored.

    Parameters
    ----------
    class_file : str or pathlib.Path
        Path to the CSV file containing object identifiers
        and decision classes.

    Returns
    -------
    pandas.DataFrame
        DataFrame containing exactly two columns:

        Name
            Object identifier.

        Klasa
            Decision class.

    Raises
    ------
    FileNotFoundError
        If the CSV file does not exist.

    ValueError
        If the CSV file does not contain at least 33 columns
        or contains duplicated object identifiers.
    """

    class_file = Path(class_file)

    if not class_file.exists():
        raise FileNotFoundError(
            f"Class file not found: {class_file}"
        )

    # Load the complete CSV file because columns are selected by position.
    df_classes = pd.read_csv(class_file, sep=",", encoding="utf-8-sig")

    # Calculate the minimum number of columns required to access column 32.
    required_columns = CSV_CLASS_COLUMN_POSITION + 1

    if df_classes.shape[1] < required_columns:
        raise ValueError(
            f"Class file '{class_file}' contains "
            f"{df_classes.shape[1]} columns, but at least "
            f"{required_columns} columns are required."
        )

    # Select only the object identifier and decision class columns.
    df_classes = df_classes.iloc[:, [CSV_NAME_COLUMN_POSITION, CSV_CLASS_COLUMN_POSITION]].copy()

    # Assign standardized column names used by the remaining functions.
    df_classes.columns = ["Name", "Klasa"]

    # Convert identifiers to strings and remove leading and trailing whitespace.
    df_classes["Name"] = (df_classes["Name"].astype(str).str.strip())

    # Find all duplicated object identifiers.
    duplicated_names = df_classes[df_classes["Name"].duplicated(keep=False)]

    if not duplicated_names.empty:
        duplicate_values = (duplicated_names["Name"].drop_duplicates().tolist())

        raise ValueError(
            f"Duplicated object identifiers found in "
            f"class file '{class_file}': "
            f"{duplicate_values}"
        )

    return df_classes


def prepare_dataset(df, df_classes):
    """
    Prepare one dataset for the ReliefF algorithm.

    ```
    The Excel dataset is used as the source of feature values
    and feature names.

    The Excel structure is interpreted as follows:

        Column position 0:
            Object identifier.

        Column positions 1 to 30:
            Exactly 30 conditional attributes used by ReliefF.

        Remaining columns:
            Ignored.

    The CSV dataset is used only as the source of decision classes.

    The CSV structure is interpreted as follows:

        Column position 0:
            Object identifier.

        Column position 32:
            Decision class.

        Remaining columns:
            Ignored.

    Decision classes are matched to Excel observations using
    object identifiers.

    Parameters
    ----------
    df : pandas.DataFrame
        Dataset loaded from the Excel file.

    df_classes : pandas.DataFrame
        DataFrame containing the Name and Klasa columns loaded
        from the corresponding CSV file.

    Returns
    -------
    tuple
        Tuple containing:

        df_result : pandas.DataFrame
            DataFrame containing object identifiers,
            exactly 30 conditional attributes,
            and decision classes.

        names : pandas.Series
            Object identifiers.

        X : pandas.DataFrame
            Exactly 30 conditional attributes used by ReliefF.

        y : pandas.Series
            Decision classes matched to observations.

    Raises
    ------
    ValueError
        If the Excel dataset contains too few columns,
        duplicated identifiers, or missing decision classes.

    RuntimeError
        If the final dataset structure is inconsistent.
    """

    # Calculate the minimum number of Excel columns required.
    minimum_required_columns = (EXCEL_FEATURE_START_POSITION + NUMBER_OF_FEATURES)

    if df.shape[1] < minimum_required_columns:
        raise ValueError(
            "The Excel dataset contains too few columns. "
            f"Found {df.shape[1]} columns, but at least "
            f"{minimum_required_columns} columns are required."
        )

    # Get the object identifiers from the first Excel column.
    names = (df.iloc[:, EXCEL_NAME_COLUMN_POSITION].copy().astype(str).str.strip())

    # Calculate the ending position of the conditional attribute range.
    feature_end_position = (EXCEL_FEATURE_START_POSITION + NUMBER_OF_FEATURES)

    # Select exactly 30 conditional attributes from the Excel file.
    X = df.iloc[:, EXCEL_FEATURE_START_POSITION:feature_end_position].copy()

    if X.shape[1] != NUMBER_OF_FEATURES:
        raise ValueError(
            "The number of extracted conditional attributes "
            f"is incorrect. Expected {NUMBER_OF_FEATURES}, "
            f"but extracted {X.shape[1]}."
        )

    # Create a temporary DataFrame containing identifiers and features.
    df_excel = pd.concat([names.rename("Name"), X], axis=1)

    # Find all duplicated object identifiers in the Excel dataset.
    duplicated_excel_names = df_excel[df_excel["Name"].duplicated(keep=False)]

    if not duplicated_excel_names.empty:
        duplicate_values = (duplicated_excel_names["Name"].drop_duplicates().tolist())

        raise ValueError(
            "Duplicated object identifiers found in "
            f"the Excel dataset: {duplicate_values}"
        )

    # Create a mapping from object identifiers to decision classes.
    class_mapping = df_classes.set_index("Name")["Klasa"]

    # Match decision classes to Excel observations using object identifiers.
    y = names.map(class_mapping)

    # Find observations for which no decision class was found.
    missing_mask = y.isna()

    if missing_mask.any():
        missing_names = (names[missing_mask].tolist())

        raise ValueError(
            "Decision classes were not found for the following "
            f"object identifiers: {missing_names}"
        )

    # Create the final DataFrame containing identifiers, features, and classes.
    df_result = df_excel.copy()

    df_result["Klasa"] = y.values

    # Verify that exactly 30 conditional attributes are available.
    if X.shape[1] != NUMBER_OF_FEATURES:
        raise RuntimeError(
            "CRITICAL ERROR: X does not contain exactly "
            f"{NUMBER_OF_FEATURES} conditional attributes. "
            f"Current number of attributes: {X.shape[1]}"
        )

    # Verify that X and y contain the same number of observations.
    if len(X) != len(y):
        raise RuntimeError(
            "CRITICAL ERROR: X and y contain different "
            "numbers of observations."
        )

    # Verify that names and X contain the same number of observations.
    if len(names) != len(X):
        raise RuntimeError(
            "CRITICAL ERROR: names and X contain different "
            "numbers of observations."
        )

    return (df_result, names, X, y)


def prepare_all_datasets(data_file=EXCEL_PATH, classes_dir=PROJECT_ROOT):
    """
    Load and prepare all datasets for ReliefF experiments.

    For each dataset, the function:

        1. Loads the corresponding worksheet from the Excel file.
        2. Extracts object identifiers from column position 0.
        3. Extracts exactly 30 conditional attributes from
           column positions 1 to 30.
        4. Loads the corresponding CSV file.
        5. Extracts object identifiers from CSV column position 0.
        6. Extracts decision classes from CSV column position 32.
        7. Matches decision classes using object identifiers.
        8. Creates X containing exactly 30 conditional attributes.
        9. Creates y containing the matched decision classes.

    Parameters
    ----------
    data_file : str or pathlib.Path, optional
        Path to the Excel file containing all datasets.

    classes_dir : str or pathlib.Path, optional
        Directory containing the CSV files with decision classes.

    Returns
    -------
    dict
        Dictionary containing prepared datasets.

        Example:

        datasets["woda"]["df"]
        datasets["woda"]["names"]
        datasets["woda"]["X"]
        datasets["woda"]["y"]

    Raises
    ------
    FileNotFoundError
        If a required CSV class file does not exist.

    RuntimeError
        If a prepared dataset does not contain exactly
        the expected number of conditional attributes.
    """

    # Load all datasets from the Excel file.
    raw_data = load_data(data_file=data_file)

    classes_dir = Path(classes_dir)

    datasets = {}

    for dataset_name, df in raw_data.items():

        # Create the path to the CSV file corresponding to the dataset.
        class_file = (classes_dir / f"{dataset_name}.csv")

        if not class_file.exists():
            raise FileNotFoundError(
                f"Class file for dataset '{dataset_name}' "
                f"was not found: {class_file}"
            )

        # Load only object identifiers and decision classes from the CSV file.
        df_classes = load_classes(
            class_file=class_file
        )

        # Prepare the dataset using Excel features and matched CSV classes.
        (df_result, names, X, y) = prepare_dataset(df=df, df_classes=df_classes)

        # Verify that the prepared dataset contains exactly 30 features.
        if X.shape[1] != NUMBER_OF_FEATURES:
            raise RuntimeError(
                f"ERROR in dataset '{dataset_name}': "
                f"expected {NUMBER_OF_FEATURES} conditional "
                f"attributes, but received {X.shape[1]}."
            )

        # Store the prepared dataset components.
        datasets[dataset_name] = {"df": df_result, "names": names, "X": X, "y": y}

        # Display information about the prepared dataset.
        print(
            f"Prepared dataset '{dataset_name}': "
            f"{len(X)} observations, "
            f"{X.shape[1]} conditional attributes."
        )

    return datasets


def load_forest_classification(forest_file=FOREST_SHARE_PATH):
    """
    Load forest-area information used to divide observations into LS and NL.

    The first worksheet of the Excel file is interpreted as follows:

        Column position 0:
            Object identifier.

        Column position 1:
            Percentage of the object area covered by forest.

        Column position 2:
            Object type: LS for a forest object or NL for a non-forest object.

    The forest percentage is retained for validation and possible later use,
    but it is not added to the 30 conditional attributes passed to ReliefF.

    Parameters
    ----------
    forest_file : str or pathlib.Path, optional
        Path to the Excel file containing forest-area information.

    Returns
    -------
    pandas.DataFrame
        DataFrame containing the standardized columns Name, Forest_share
        and Forest_type.

    Raises
    ------
    FileNotFoundError
        If the forest classification file does not exist.

    ValueError
        If the worksheet contains fewer than three columns, duplicated object
        identifiers, missing values, or values other than LS and NL.
    """

    forest_file = Path(forest_file)

    if not forest_file.exists():
        raise FileNotFoundError(
            f"Forest classification file not found: {forest_file}"
        )

    df_forest = pd.read_excel(
        forest_file,
        sheet_name=0,
        engine="openpyxl"
    )

    minimum_required_columns = FOREST_TYPE_COLUMN_POSITION + 1

    if df_forest.shape[1] < minimum_required_columns:
        raise ValueError(
            f"Forest classification file '{forest_file}' contains "
            f"{df_forest.shape[1]} columns, but at least "
            f"{minimum_required_columns} columns are required."
        )

    # Select only the identifier, forest share and final LS/NL classification.
    df_forest = df_forest.iloc[
        :,
        [
            FOREST_NAME_COLUMN_POSITION,
            FOREST_SHARE_COLUMN_POSITION,
            FOREST_TYPE_COLUMN_POSITION,
        ]
    ].copy()

    df_forest.columns = ["Name", "Forest_share", "Forest_type"]

    # Standardize identifiers and LS/NL values before matching observations.
    df_forest["Name"] = df_forest["Name"].astype(str).str.strip()
    df_forest["Forest_type"] = (
        df_forest["Forest_type"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    duplicated_names = df_forest[
        df_forest["Name"].duplicated(keep=False)
    ]

    if not duplicated_names.empty:
        duplicate_values = (
            duplicated_names["Name"].drop_duplicates().tolist()
        )

        raise ValueError(
            "Duplicated object identifiers found in forest "
            f"classification file '{forest_file}': {duplicate_values}"
        )

    missing_type_mask = df_forest["Forest_type"].isna()

    if missing_type_mask.any():
        missing_names = df_forest.loc[missing_type_mask, "Name"].tolist()

        raise ValueError(
            "Forest type was not provided for the following object "
            f"identifiers: {missing_names}"
        )

    invalid_type_mask = ~df_forest["Forest_type"].isin(VALID_FOREST_TYPES)

    if invalid_type_mask.any():
        invalid_values = (
            df_forest.loc[invalid_type_mask, "Forest_type"]
            .drop_duplicates()
            .tolist()
        )

        raise ValueError(
            "Forest type must contain only LS or NL. "
            f"Invalid values: {invalid_values}"
        )

    return df_forest


def split_dataset_by_forest_type(df_result, df_forest):
    """
    Divide one prepared dataset into forest (LS) and non-forest (NL) objects.

    The function divides only observations. It does not select attributes by
    their names or suffixes. Consequently, both returned X DataFrames contain
    the same 30 conditional attributes as the original prepared dataset.

    Parameters
    ----------
    df_result : pandas.DataFrame
        Prepared dataset containing Name, exactly 30 conditional attributes
        and Klasa.

    df_forest : pandas.DataFrame
        Forest classification returned by load_forest_classification().

    Returns
    -------
    dict
        Dictionary with LS and NL keys. Each value contains df, names, X and y.

    Raises
    ------
    ValueError
        If an object has no LS/NL classification or one of the resulting
        datasets is empty.

    RuntimeError
        If the input or resulting X DataFrames do not contain exactly 30
        conditional attributes.
    """

    expected_columns = NUMBER_OF_FEATURES + 2

    if df_result.shape[1] != expected_columns:
        raise RuntimeError(
            "Prepared dataset must contain Name, exactly "
            f"{NUMBER_OF_FEATURES} conditional attributes and Klasa. "
            f"Current number of columns: {df_result.shape[1]}"
        )

    forest_type_mapping = df_forest.set_index("Name")["Forest_type"]

    # Match LS/NL information without changing the original observation order.
    working_df = df_result.copy()
    working_df["Forest_type"] = working_df["Name"].map(forest_type_mapping)

    missing_mask = working_df["Forest_type"].isna()

    if missing_mask.any():
        missing_names = working_df.loc[missing_mask, "Name"].tolist()

        raise ValueError(
            "Forest classification was not found for the following "
            f"object identifiers: {missing_names}"
        )

    split_datasets = {}

    for forest_type in VALID_FOREST_TYPES:
        # Filter rows only. All 30 original conditional attributes are kept.
        subset_df = (
            working_df.loc[working_df["Forest_type"] == forest_type]
            .drop(columns="Forest_type")
            .reset_index(drop=True)
        )

        if subset_df.empty:
            raise ValueError(
                f"The prepared dataset contains no {forest_type} objects."
            )

        names = subset_df["Name"].copy()
        X = subset_df.iloc[
            :,
            EXCEL_FEATURE_START_POSITION:
            EXCEL_FEATURE_START_POSITION + NUMBER_OF_FEATURES
        ].copy()
        y = subset_df["Klasa"].copy()

        if X.shape[1] != NUMBER_OF_FEATURES:
            raise RuntimeError(
                f"Dataset '{forest_type}' should contain "
                f"{NUMBER_OF_FEATURES} conditional attributes, but contains "
                f"{X.shape[1]}."
            )

        split_datasets[forest_type] = {
            "df": subset_df,
            "names": names,
            "X": X,
            "y": y,
        }

    return split_datasets


def save_prepared_dataset(df, output_file):
    """
    Save a prepared DataFrame to an Excel or CSV file.

    Parameters
    ----------
    df : pandas.DataFrame
        Prepared DataFrame containing Name, 30 attributes and Klasa.

    output_file : str or pathlib.Path
        Destination path ending with .xlsx or .csv.

    Raises
    ------
    ValueError
        If the requested output format is not XLSX or CSV.
    """

    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    if output_file.suffix.lower() == ".xlsx":
        df.to_excel(output_file, index=False, engine="openpyxl")
    elif output_file.suffix.lower() == ".csv":
        df.to_csv(output_file, index=False, encoding="utf-8-sig")
    else:
        raise ValueError(
            "Prepared datasets can be saved only as XLSX or CSV files."
        )


def prepare_forest_datasets(data_file=EXCEL_PATH, classes_dir=PROJECT_ROOT, forest_file=FOREST_SHARE_PATH,
                            output_dir=PREPARED_DATASETS_DIR, output_format="xlsx", ):
    """
    Prepare separate LS and NL datasets for all biological groups.

    First, the existing complete preparation workflow is executed. Next, rows
    are divided using the LS/NL value from the forest classification file.
    Both subsets retain all 30 conditional attributes and are ready for use by
    ReliefF. Each DataFrame is also saved in a separate file.

    Parameters
    ----------
    data_file : str or pathlib.Path, optional
        Path to the Excel file containing the source feature datasets.

    classes_dir : str or pathlib.Path, optional
        Directory containing woda.csv, rosliny.csv, ssaki.csv, ptaki.csv and
        bezkregowce.csv with decision classes.

    forest_file : str or pathlib.Path, optional
        Path to the Excel file containing Name, forest share and LS/NL type.

    output_dir : str or pathlib.Path or None, optional
        Directory for prepared files. If None, files are not saved.

    output_format : str, optional
        Output format: xlsx or csv.

    Returns
    -------
    dict
        Flat dictionary with keys such as woda_LS, woda_NL, rosliny_LS and
        rosliny_NL. Every value contains df, names, X and y.
    """

    normalized_format = output_format.lower().lstrip(".")

    if normalized_format not in {"xlsx", "csv"}:
        raise ValueError("output_format must be 'xlsx' or 'csv'.")

    complete_datasets = prepare_all_datasets(
        data_file=data_file,
        classes_dir=classes_dir,
    )

    df_forest = load_forest_classification(forest_file=forest_file)
    forest_datasets = {}

    for dataset_name, complete_dataset in complete_datasets.items():
        split_datasets = split_dataset_by_forest_type(
            df_result=complete_dataset["df"],
            df_forest=df_forest,
        )

        for forest_type, prepared_dataset in split_datasets.items():
            result_name = f"{dataset_name}_{forest_type}"
            forest_datasets[result_name] = prepared_dataset

            if output_dir is not None:
                output_file = (
                        Path(output_dir) /
                        f"{result_name}.{normalized_format}"
                )

                save_prepared_dataset(
                    df=prepared_dataset["df"],
                    output_file=output_file,
                )

            print(
                f"Prepared dataset '{result_name}': "
                f"{len(prepared_dataset['X'])} observations, "
                f"{prepared_dataset['X'].shape[1]} conditional attributes."
            )

    return forest_datasets


def load_prepared_dataset(prepared_file):
    """
    Load a saved LS or NL dataset for a ReliefF experiment.

    Parameters
    ----------
    prepared_file : str or pathlib.Path
        Path to a prepared XLSX or CSV file.

    Returns
    -------
    dict
        Dictionary containing df, names, X and y.

    Raises
    ------
    FileNotFoundError
        If the prepared file does not exist.

    ValueError
        If the file format or dataset structure is invalid.
    """

    prepared_file = Path(prepared_file)

    if not prepared_file.exists():
        raise FileNotFoundError(
            f"Prepared dataset file not found: {prepared_file}"
        )

    if prepared_file.suffix.lower() == ".xlsx":
        df = pd.read_excel(prepared_file, engine="openpyxl")
    elif prepared_file.suffix.lower() == ".csv":
        df = pd.read_csv(prepared_file, encoding="utf-8-sig")
    else:
        raise ValueError(
            "Prepared datasets can be loaded only from XLSX or CSV files."
        )

    expected_columns = NUMBER_OF_FEATURES + 2

    if df.shape[1] != expected_columns:
        raise ValueError(
            "Prepared dataset should contain Name, exactly "
            f"{NUMBER_OF_FEATURES} conditional attributes and Klasa. "
            f"Current number of columns: {df.shape[1]}"
        )

    if df.columns[0] != "Name" or df.columns[-1] != "Klasa":
        raise ValueError(
            "Prepared dataset must start with the Name column and end "
            "with the Klasa column."
        )

    names = df["Name"].copy()
    X = df.iloc[:, 1:1 + NUMBER_OF_FEATURES].copy()
    y = df["Klasa"].copy()

    return {
        "df": df,
        "names": names,
        "X": X,
        "y": y,
    }
