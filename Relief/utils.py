from __future__ import annotations

import ast
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

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


def load_data(data_file: str | Path = EXCEL_PATH) -> dict[str, pd.DataFrame]:
    """Load all ecological datasets from the source Excel workbook.

    Each dataset is loaded from the worksheet specified in :data:`SHEETS`.
    Pandas uses zero-based worksheet indexes, therefore indexes 1-5 correspond
    to Excel worksheets 2-6.

    :param data_file: Path to the Excel workbook containing all datasets.
    :type data_file: str or pathlib.Path
    :return: Mapping from dataset names to loaded DataFrames.
    :rtype: dict[str, pandas.DataFrame]
    :raises FileNotFoundError: If the Excel workbook does not exist.
    """

    data_file = Path(data_file)

    if not data_file.exists():
        raise FileNotFoundError(f"Excel file not found: {data_file}")

    dataframes: dict[str, pd.DataFrame] = {}

    for dataset_name, sheet_number in SHEETS.items():
        # Wczytanie zbioru z wcześniej zdefiniowanego arkusza Excela.
        df = pd.read_excel(data_file, sheet_name=sheet_number, engine="openpyxl", )
        dataframes[dataset_name] = df

    return dataframes


def load_classes(class_file: str | Path) -> pd.DataFrame:
    """Load object identifiers and decision classes from one CSV file.

    Only two columns are used: position 0 contains the object identifier and
    position 32 contains the decision class. All remaining CSV columns are
    ignored.

    :param class_file: Path to the CSV file containing object identifiers and
        decision classes.
    :type class_file: str or pathlib.Path
    :return: DataFrame containing exactly ``Name`` and ``Klasa`` columns.
    :rtype: pandas.DataFrame
    :raises FileNotFoundError: If the CSV file does not exist.
    :raises ValueError: If the CSV file contains fewer than 33 columns or
        duplicated object identifiers.
    """

    class_file = Path(class_file)

    if not class_file.exists():
        raise FileNotFoundError(f"Class file not found: {class_file}")

    df_classes = pd.read_csv(class_file, sep=",", encoding="utf-8-sig", )

    required_columns = CSV_CLASS_COLUMN_POSITION + 1

    if df_classes.shape[1] < required_columns:
        raise ValueError(
            f"Class file '{class_file}' contains {df_classes.shape[1]} columns, "
            f"but at least {required_columns} columns are required."
        )

    # Wybór kolumn zawierających identyfikatory i klasy decyzji.
    df_classes = df_classes.iloc[:, [CSV_NAME_COLUMN_POSITION, CSV_CLASS_COLUMN_POSITION]].copy()
    df_classes.columns = ["Name", "Klasa"]

    df_classes["Name"] = df_classes["Name"].astype(str).str.strip()

    duplicated_names = df_classes[df_classes["Name"].duplicated(keep=False)]

    if not duplicated_names.empty:
        duplicate_values = (duplicated_names["Name"].drop_duplicates().tolist())
        raise ValueError(
            f"Duplicated object identifiers found in class file "
            f"'{class_file}': {duplicate_values}"
        )

    return df_classes


def prepare_dataset(df: pd.DataFrame, df_classes: pd.DataFrame, ) -> tuple[
    pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
    """Prepare one ecological dataset for the ReliefF algorithm.

    The Excel table supplies object identifiers and exactly 30 conditional
    attributes. Decision classes are read from the corresponding CSV table and
    matched to observations using object identifiers.

    :param df: Dataset loaded from the Excel workbook.
    :type df: pandas.DataFrame
    :param df_classes: DataFrame containing standardized ``Name`` and ``Klasa``
        columns loaded from the corresponding CSV file.
    :type df_classes: pandas.DataFrame
    :return: Tuple containing the complete prepared DataFrame, object names,
        feature matrix ``X`` and decision vector ``y``.
    :rtype: tuple[pandas.DataFrame, pandas.Series, pandas.DataFrame,
        pandas.Series]
    :raises ValueError: If the input structure is invalid, identifiers are
        duplicated or decision classes cannot be matched.
    :raises RuntimeError: If the final dataset structure is inconsistent.
    """

    minimum_required_columns = (EXCEL_FEATURE_START_POSITION + NUMBER_OF_FEATURES)

    if df.shape[1] < minimum_required_columns:
        raise ValueError(
            "The Excel dataset contains too few columns. "
            f"Found {df.shape[1]} columns, but at least "
            f"{minimum_required_columns} columns are required."
        )

    # Id obiektów z pierwszej kolumny arkusza
    names = (df.iloc[:, EXCEL_NAME_COLUMN_POSITION].copy().astype(str).str.strip())

    feature_end_position = (EXCEL_FEATURE_START_POSITION + NUMBER_OF_FEATURES)

    # Wybór 30 atrybutów.
    X = df.iloc[:, EXCEL_FEATURE_START_POSITION:feature_end_position].copy()

    if X.shape[1] != NUMBER_OF_FEATURES:
        raise ValueError(
            "The number of extracted conditional attributes is incorrect. "
            f"Expected {NUMBER_OF_FEATURES}, but extracted {X.shape[1]}."
        )

    # Sprawdzenie, czy atr sa liczbowe.
    non_numeric_columns = X.select_dtypes(exclude="number").columns.tolist()
    if non_numeric_columns:
        raise TypeError(
            "All conditional attributes must be numeric. "
            f"Non-numeric columns: {non_numeric_columns}"
        )

    df_excel = pd.concat([names.rename("Name"), X], axis=1)

    duplicated_excel_names = df_excel[df_excel["Name"].duplicated(keep=False)]

    if not duplicated_excel_names.empty:
        duplicate_values = (duplicated_excel_names["Name"].drop_duplicates().tolist())
        raise ValueError(
            "Duplicated object identifiers found in the Excel dataset: "
            f"{duplicate_values}"
        )

    class_mapping = df_classes.set_index("Name")["Klasa"]
    y = names.map(class_mapping)

    missing_mask = y.isna()

    if missing_mask.any():
        missing_names = names[missing_mask].tolist()
        raise ValueError(
            "Decision classes were not found for the following object "
            f"identifiers: {missing_names}"
        )

    df_result = df_excel.copy()
    df_result["Klasa"] = y.values

    if X.shape[1] != NUMBER_OF_FEATURES:
        raise RuntimeError(
            "CRITICAL ERROR: X does not contain exactly "
            f"{NUMBER_OF_FEATURES} conditional attributes. "
            f"Current number of attributes: {X.shape[1]}"
        )

    if len(X) != len(y):
        raise RuntimeError(
            "CRITICAL ERROR: X and y contain different numbers of observations."
        )

    if len(names) != len(X):
        raise RuntimeError(
            "CRITICAL ERROR: names and X contain different numbers of observations."
        )

    return df_result, names, X, y


def prepare_all_datasets(data_file: str | Path = EXCEL_PATH, classes_dir: str | Path = PROJECT_ROOT, ) -> dict[
    str, dict[str, Any]]:
    """Load and prepare all five complete ecological datasets.

    For every biological group, the function loads feature values from the
    corresponding Excel worksheet and decision classes from the CSV file with
    the same dataset name.

    :param data_file: Path to ``dane.xlsx``.
    :type data_file: str or pathlib.Path
    :param classes_dir: Directory containing ``woda.csv``, ``rosliny.csv``,
        ``ssaki.csv``, ``ptaki.csv`` and ``bezkregowce.csv``.
    :type classes_dir: str or pathlib.Path
    :return: Mapping containing ``df``, ``names``, ``X`` and ``y`` for every
        biological group.
    :rtype: dict[str, dict[str, typing.Any]]
    :raises FileNotFoundError: If a required decision-class CSV file is absent.
    :raises RuntimeError: If a prepared dataset does not contain exactly 30
        conditional attributes.
    """

    raw_data = load_data(data_file=data_file)
    classes_dir = Path(classes_dir)
    datasets: dict[str, dict[str, Any]] = {}

    for dataset_name, df in raw_data.items():
        class_file = classes_dir / f"{dataset_name}.csv"

        if not class_file.exists():
            raise FileNotFoundError(
                f"Class file for dataset '{dataset_name}' was not found: "
                f"{class_file}"
            )

        df_classes = load_classes(class_file=class_file)

        df_result, names, X, y = prepare_dataset(df=df, df_classes=df_classes, )

        if X.shape[1] != NUMBER_OF_FEATURES:
            raise RuntimeError(
                f"ERROR in dataset '{dataset_name}': expected "
                f"{NUMBER_OF_FEATURES} conditional attributes, but received "
                f"{X.shape[1]}."
            )

        datasets[dataset_name] = {"df": df_result, "names": names, "X": X, "y": y, }

        print(
            f"Prepared dataset '{dataset_name}': "
            f"{len(X)} observations, "
            f"{X.shape[1]} conditional attributes."
        )

    return datasets


def load_forest_classification(forest_file: str | Path = FOREST_SHARE_PATH, ) -> pd.DataFrame:
    """Load the LS/NL forest classification for all objects.

    The first three columns of the first worksheet are interpreted as object
    identifier, percentage of forest area and final LS/NL classification.

    :param forest_file: Path to the Excel file containing forest information.
    :type forest_file: str or pathlib.Path
    :return: DataFrame with standardized ``Name``, ``Forest_share`` and
        ``Forest_type`` columns.
    :rtype: pandas.DataFrame
    :raises FileNotFoundError: If the forest classification file is absent.
    :raises ValueError: If the input structure, identifiers or LS/NL values are
        invalid.
    """

    forest_file = Path(forest_file)

    if not forest_file.exists():
        raise FileNotFoundError(
            f"Forest classification file not found: {forest_file}"
        )

    df_forest = pd.read_excel(forest_file, sheet_name=0, engine="openpyxl", )

    minimum_required_columns = FOREST_TYPE_COLUMN_POSITION + 1

    if df_forest.shape[1] < minimum_required_columns:
        raise ValueError(
            f"Forest classification file '{forest_file}' contains "
            f"{df_forest.shape[1]} columns, but at least "
            f"{minimum_required_columns} columns are required."
        )

    df_forest = df_forest.iloc[
        :, [FOREST_NAME_COLUMN_POSITION, FOREST_SHARE_COLUMN_POSITION, FOREST_TYPE_COLUMN_POSITION, ],].copy()

    df_forest.columns = ["Name", "Forest_share", "Forest_type"]

    df_forest["Name"] = df_forest["Name"].astype(str).str.strip()
    df_forest["Forest_type"] = (df_forest["Forest_type"].astype("string").str.strip().str.upper())

    duplicated_names = df_forest[df_forest["Name"].duplicated(keep=False)]

    if not duplicated_names.empty:
        duplicate_values = (duplicated_names["Name"].drop_duplicates().tolist())
        raise ValueError(
            "Duplicated object identifiers found in forest classification "
            f"file '{forest_file}': {duplicate_values}"
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
        invalid_values = (df_forest.loc[invalid_type_mask, "Forest_type"].drop_duplicates().tolist())
        raise ValueError(
            "Forest type must contain only LS or NL. "
            f"Invalid values: {invalid_values}"
        )

    return df_forest


def split_dataset_by_forest_type(df_result: pd.DataFrame, df_forest: pd.DataFrame, ) -> dict[str, dict[str, Any]]:
    """Divide one prepared dataset into LS and NL observations.

    Only rows are filtered. Both resulting datasets retain the same 30
    conditional attributes as the original complete dataset.

    :param df_result: Prepared dataset containing ``Name``, exactly 30
        conditional attributes and ``Klasa``.
    :type df_result: pandas.DataFrame
    :param df_forest: Forest classification returned by
        :func:`load_forest_classification`.
    :type df_forest: pandas.DataFrame
    :return: Dictionary with ``LS`` and ``NL`` entries. Each entry contains
        ``df``, ``names``, ``X`` and ``y``.
    :rtype: dict[str, dict[str, typing.Any]]
    :raises ValueError: If an observation has no LS/NL classification or a
        resulting subset is empty.
    :raises RuntimeError: If the input or resulting feature matrices do not
        contain exactly 30 conditional attributes.
    """

    expected_columns = NUMBER_OF_FEATURES + 2

    if df_result.shape[1] != expected_columns:
        raise RuntimeError(
            "Prepared dataset must contain Name, exactly "
            f"{NUMBER_OF_FEATURES} conditional attributes and Klasa. "
            f"Current number of columns: {df_result.shape[1]}"
        )

    forest_type_mapping = df_forest.set_index("Name")["Forest_type"]

    # Dopasuj informacje LS/NL bez zmiany kolejności obserwacji.
    working_df = df_result.copy()
    working_df["Forest_type"] = working_df["Name"].map(forest_type_mapping)

    missing_mask = working_df["Forest_type"].isna()

    if missing_mask.any():
        missing_names = working_df.loc[missing_mask, "Name"].tolist()
        raise ValueError(
            "Forest classification was not found for the following object "
            f"identifiers: {missing_names}"
        )

    split_datasets: dict[str, dict[str, Any]] = {}

    for forest_type in VALID_FOREST_TYPES:
        # Filtrowanie wierszy
        subset_df = (
            working_df.loc[working_df["Forest_type"] == forest_type].drop(columns="Forest_type").reset_index(drop=True))

        if subset_df.empty:
            raise ValueError(
                f"The prepared dataset contains no {forest_type} objects."
            )

        names = subset_df["Name"].copy()
        X = subset_df.iloc[:, EXCEL_FEATURE_START_POSITION: EXCEL_FEATURE_START_POSITION + NUMBER_OF_FEATURES,].copy()
        y = subset_df["Klasa"].copy()

        if X.shape[1] != NUMBER_OF_FEATURES:
            raise RuntimeError(
                f"Dataset '{forest_type}' should contain "
                f"{NUMBER_OF_FEATURES} conditional attributes, but contains "
                f"{X.shape[1]}."
            )

        split_datasets[forest_type] = {"df": subset_df, "names": names, "X": X, "y": y, }

    return split_datasets


def save_prepared_dataset(df: pd.DataFrame, output_file: str | Path, ) -> None:
    """Save a prepared dataset as an XLSX or CSV file.

    :param df: Prepared DataFrame containing ``Name``, conditional attributes
        and ``Klasa``.
    :type df: pandas.DataFrame
    :param output_file: Destination file ending with ``.xlsx`` or ``.csv``.
    :type output_file: str or pathlib.Path
    :return: None.
    :rtype: None
    :raises ValueError: If the requested output format is unsupported.
    """

    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    if output_file.suffix.lower() == ".xlsx":
        df.to_excel(output_file, index=False, engine="openpyxl", )
    elif output_file.suffix.lower() == ".csv":
        df.to_csv(output_file, index=False, encoding="utf-8-sig", )
    else:
        raise ValueError(
            "Prepared datasets can be saved only as XLSX or CSV files."
        )


def prepare_forest_datasets(data_file: str | Path = EXCEL_PATH, classes_dir: str | Path = PROJECT_ROOT,
                            forest_file: str | Path = FOREST_SHARE_PATH,
                            output_dir: str | Path | None = PREPARED_DATASETS_DIR,
                            output_format: str = "xlsx", ) -> dict[str, dict[str, Any]]:
    """Prepare separate LS and NL datasets for all biological groups.

    The complete five datasets are prepared first. Their observations are then
    divided according to the LS/NL forest classification. The row filtering
    does not remove any conditional attributes, therefore every LS/NL feature
    matrix still contains exactly 30 attributes.

    :param data_file: Path to the Excel workbook containing source features.
    :type data_file: str or pathlib.Path
    :param classes_dir: Directory containing the five decision-class CSV files.
    :type classes_dir: str or pathlib.Path
    :param forest_file: Path to the LS/NL forest classification workbook.
    :type forest_file: str or pathlib.Path
    :param output_dir: Directory for prepared LS/NL files. ``None`` disables
        saving prepared datasets.
    :type output_dir: str or pathlib.Path or None
    :param output_format: Output format, either ``xlsx`` or ``csv``.
    :type output_format: str
    :return: Flat mapping with keys such as ``woda_LS``, ``woda_NL``,
        ``rosliny_LS`` and ``rosliny_NL``.
    :rtype: dict[str, dict[str, typing.Any]]
    :raises ValueError: If ``output_format`` is unsupported.
    """

    normalized_format = output_format.lower().lstrip(".")

    if normalized_format not in {"xlsx", "csv"}:
        raise ValueError("output_format must be 'xlsx' or 'csv'.")

    complete_datasets = prepare_all_datasets(data_file=data_file, classes_dir=classes_dir, )

    df_forest = load_forest_classification(forest_file=forest_file)
    forest_datasets: dict[str, dict[str, Any]] = {}

    for dataset_name, complete_dataset in complete_datasets.items():
        split_datasets = split_dataset_by_forest_type(df_result=complete_dataset["df"], df_forest=df_forest, )

        for forest_type, prepared_dataset in split_datasets.items():
            result_name = f"{dataset_name}_{forest_type}"
            forest_datasets[result_name] = prepared_dataset

            if output_dir is not None:
                output_file = (Path(output_dir) / f"{result_name}.{normalized_format}")
                save_prepared_dataset(df=prepared_dataset["df"], output_file=output_file, )

            print(
                f"Prepared dataset '{result_name}': "
                f"{len(prepared_dataset['X'])} observations, "
                f"{prepared_dataset['X'].shape[1]} conditional attributes."
            )

    return forest_datasets


def _validate_prepared_dataframe(df: pd.DataFrame, source_label: str, ) -> dict[str, pd.DataFrame | pd.Series]:
    """Validate and decompose one prepared ecological dataset.

    A prepared dataset must contain ``Name`` as the first column, exactly
    30 conditional attributes and ``Klasa`` as the final column.

    :param df: Prepared dataset loaded from an Excel worksheet or CSV file.
    :type df: pandas.DataFrame
    :param source_label: Human-readable source description used in errors.
    :type source_label: str
    :return: Mapping containing ``df``, ``names``, ``X`` and ``y``.
    :rtype: dict[str, pandas.DataFrame | pandas.Series]
    :raises ValueError: If the dataset structure is invalid.
    :raises TypeError: If at least one conditional attribute is non-numeric.
    """

    expected_columns = NUMBER_OF_FEATURES + 2

    if df.shape[1] != expected_columns:
        raise ValueError(
            f"Prepared dataset '{source_label}' should contain Name, exactly "
            f"{NUMBER_OF_FEATURES} conditional attributes and Klasa. "
            f"Current number of columns: {df.shape[1]}"
        )

    if str(df.columns[0]).strip() != "Name" or str(df.columns[-1]).strip() != "Klasa":
        raise ValueError(
            f"Prepared dataset '{source_label}' must start with the Name "
            "column and end with the Klasa column."
        )

    # Normalizacja identyfikatorów obiektów bez zmiany kolejności wierszy.
    df = df.copy()
    df["Name"] = df["Name"].astype(str).str.strip()

    duplicated_names = df[df["Name"].duplicated(keep=False)]
    if not duplicated_names.empty:
        duplicate_values = duplicated_names["Name"].drop_duplicates().tolist()
        raise ValueError(
            f"Duplicated object identifiers found in '{source_label}': "
            f"{duplicate_values}"
        )

    X = df.iloc[:, 1:1 + NUMBER_OF_FEATURES].copy()

    # Kontrola typów atrybutów przed ich późniejszą selekcją.
    non_numeric_columns = X.select_dtypes(exclude="number").columns.tolist()
    if non_numeric_columns:
        raise TypeError(
            f"All conditional attributes in '{source_label}' must be numeric. "
            f"Non-numeric columns: {non_numeric_columns}"
        )

    names = df["Name"].copy()
    y = df["Klasa"].copy()

    return {
        "df": df,
        "names": names,
        "X": X,
        "y": y,
    }


def load_prepared_dataset(prepared_file: str | Path, sheet_name: str | int = 0, ) -> dict[
    str, pd.DataFrame | pd.Series]:
    """Load one previously saved prepared ecological dataset.

    XLSX files may contain several worksheets. ``sheet_name`` selects the
    worksheet that should be interpreted as one prepared dataset. CSV files
    ignore the worksheet argument.

    :param prepared_file: Path to a prepared XLSX or CSV file.
    :type prepared_file: str or pathlib.Path
    :param sheet_name: Excel worksheet name or zero-based worksheet index.
    :type sheet_name: str or int
    :return: Mapping containing ``df``, ``names``, ``X`` and ``y``.
    :rtype: dict[str, pandas.DataFrame | pandas.Series]
    :raises FileNotFoundError: If the prepared file does not exist.
    :raises ValueError: If the file format or dataset structure is invalid.
    """

    prepared_file = Path(prepared_file)

    if not prepared_file.exists():
        raise FileNotFoundError(
            f"Prepared dataset file not found: {prepared_file}"
        )

    if prepared_file.suffix.lower() == ".xlsx":
        df = pd.read_excel(prepared_file, sheet_name=sheet_name, engine="openpyxl", )
        source_label = f"{prepared_file.name}, sheet {sheet_name!r}"
    elif prepared_file.suffix.lower() == ".csv":
        df = pd.read_csv(prepared_file, encoding="utf-8-sig")
        source_label = prepared_file.name
    else:
        raise ValueError(
            "Prepared datasets can be loaded only from XLSX or CSV files."
        )

    return _validate_prepared_dataframe(df=df, source_label=source_label)


def _parse_feature_order(value: Any) -> list[str]:
    """Convert one ``Feature_order`` cell into an ordered feature list.

    ReliefF result files store ``Feature_order`` as the string representation
    of a Python list. The value is reconstructed safely with
    :func:`ast.literal_eval`.

    :param value: Value read from a ``Feature_order`` Excel cell.
    :type value: typing.Any
    :return: Feature names ordered from highest to lowest ReliefF importance.
    :rtype: list[str]
    :raises ValueError: If the cell is empty or does not contain a valid list.
    """

    if isinstance(value, (list, tuple)):
        feature_order = [str(feature).strip() for feature in value if str(feature).strip()]
    else:
        if pd.isna(value):
            raise ValueError("Feature_order contains an empty value.")

        text = str(value).strip()
        if not text:
            raise ValueError("Feature_order contains an empty value.")

        try:
            parsed_value = ast.literal_eval(text)
        except (ValueError, SyntaxError) as error:
            raise ValueError(
                f"Invalid Feature_order value: {text}"
            ) from error

        if not isinstance(parsed_value, (list, tuple)):
            raise ValueError(
                "Feature_order must contain a string representation "
                "of a Python list."
            )

        feature_order = [
            str(feature).strip()
            for feature in parsed_value
            if str(feature).strip()
        ]

    if not feature_order:
        raise ValueError("Feature_order contains an empty list.")

    if len(feature_order) != len(set(feature_order)):
        raise ValueError("Feature_order contains duplicated feature names.")

    return feature_order


def _extract_relief_run_timestamp(results_directory: str | Path, ) -> tuple[str, str]:
    """Extract date and time from a ReliefF run directory name.

    Expected directory format::

        2026-09-07_13-12-14

    :param results_directory: ReliefF run directory.
    :type results_directory: str or pathlib.Path
    :return: Date and time strings.
    :rtype: tuple[str, str]
    :raises ValueError: If the directory name does not match the expected form.
    """

    directory_name = Path(results_directory).name

    try:
        run_date, run_time = directory_name.split("_", maxsplit=1)
        datetime.strptime(f"{run_date}_{run_time}", "%Y-%m-%d_%H-%M-%S", )
    except ValueError as error:
        raise ValueError(
            "ReliefF results directory must have the format "
            "'YYYY-MM-DD_HH-MM-SS'. "
            f"Current value: '{directory_name}'."
        ) from error

    return run_date, run_time


def get_relief_run_files(results_directory: str | Path, ) -> dict[str, Path]:
    """Return the three primary Excel files belonging to one ReliefF run.

    The run directory is expected to contain one result workbook and two data
    workbooks created for the same timestamp::

        result_relief_YYYY-MM-DD_HH-MM-SS.xlsx
        data_LS_relief_YYYY-MM-DD_HH-MM-SS.xlsx
        data_NL_relief_YYYY-MM-DD_HH-MM-SS.xlsx

    :param results_directory: Directory of one ReliefF execution.
    :type results_directory: str or pathlib.Path
    :return: Mapping with ``results``, ``LS`` and ``NL`` file paths.
    :rtype: dict[str, pathlib.Path]
    :raises FileNotFoundError: If the directory or one of the required files
        does not exist.
    :raises NotADirectoryError: If the supplied path is not a directory.
    """

    results_directory = Path(results_directory)

    if not results_directory.exists():
        raise FileNotFoundError(
            f"ReliefF results directory not found: {results_directory}"
        )

    if not results_directory.is_dir():
        raise NotADirectoryError(
            f"The provided path is not a directory: {results_directory}"
        )

    run_date, run_time = _extract_relief_run_timestamp(results_directory)
    timestamp = f"{run_date}_{run_time}"

    run_files = {
        "results": results_directory / f"result_relief_{timestamp}.xlsx",
        "LS": results_directory / f"data_LS_relief_{timestamp}.xlsx",
        "NL": results_directory / f"data_NL_relief_{timestamp}.xlsx",
    }

    missing_files = [file_path for file_path in run_files.values() if not file_path.exists()]

    if missing_files:
        missing_names = [file_path.name for file_path in missing_files]
        raise FileNotFoundError(
            "The ReliefF run directory does not contain all required files. "
            f"Missing files: {missing_names}"
        )

    return run_files


def load_relief_run_datasets(results_directory: str | Path, ) -> dict[str, dict[str, Any]]:
    """Load all LS and NL datasets saved during one ReliefF execution.

    Two workbooks are read: one for LS observations and one for NL
    observations. In each workbook, worksheet 1 is metadata (``INFO``) and
    worksheets 2-6 contain the five biological groups. Pandas uses zero-based
    worksheet indexes, therefore only worksheet indexes 1-5 are loaded as
    datasets.

    Returned keys follow the ReliefF ranking convention, for example
    ``woda_LS``, ``rosliny_NL`` and ``ptaki_LS``.

    :param results_directory: Directory of one ReliefF execution.
    :type results_directory: str or pathlib.Path
    :return: Mapping containing ten prepared LS/NL datasets.
    :rtype: dict[str, dict[str, typing.Any]]
    :raises ValueError: If a source workbook does not contain six worksheets
        or if one of the biological worksheets has an invalid structure.
    """

    run_files = get_relief_run_files(results_directory)
    datasets: dict[str, dict[str, Any]] = {}

    for forest_type in VALID_FOREST_TYPES:
        source_file = run_files[forest_type]
        excel_file = pd.ExcelFile(source_file, engine="openpyxl")

        if len(excel_file.sheet_names) < 6:
            raise ValueError(
                f"File '{source_file.name}' should contain at least six "
                f"worksheets (INFO + 5 datasets), but contains "
                f"{len(excel_file.sheet_names)}."
            )

        # Pominięcie pierwszego arkusza INFO i odczyt arkuszy 2-6.
        for dataset_name, sheet_index in SHEETS.items():
            df = pd.read_excel(
                source_file,
                sheet_name=sheet_index,
                engine="openpyxl",
            )

            dataset_key = f"{dataset_name}_{forest_type}"
            source_label = (
                f"{source_file.name}, sheet "
                f"'{excel_file.sheet_names[sheet_index]}'"
            )

            datasets[dataset_key] = _validate_prepared_dataframe(df=df, source_label=source_label, )

            print(
                f"Loaded dataset '{dataset_key}': "
                f"{len(datasets[dataset_key]['X'])} observations, "
                f"{datasets[dataset_key]['X'].shape[1]} conditional attributes."
            )

    return datasets


def load_feature_orders(results_directory: str | Path, recursive: bool = False, ) -> dict[str, list[str]]:
    """Load all ReliefF feature rankings from one run result workbook.

    The current result format stores every biological group and both forest
    types in one ``result_relief_...xlsx`` workbook. Dataset identifiers are
    reconstructed from ``Data_group`` and ``Forest_type``. Only rows with
    ``Result_type == 'Weight'`` are used because ``Feature_order`` is stored
    in weight rows.

    :param results_directory: Directory of one ReliefF execution.
    :type results_directory: str or pathlib.Path
    :param recursive: Retained for backward API compatibility and ignored by
        the current single-workbook format.
    :type recursive: bool
    :return: Mapping such as ``ptaki_LS -> [feature1, feature2, ...]``.
    :rtype: dict[str, list[str]]
    :raises ValueError: If required columns, rankings or dataset identifiers
        are missing or duplicated.
    """

    _ = recursive
    result_file = get_relief_run_files(results_directory)["results"]
    results = pd.read_excel(result_file, engine="openpyxl")

    required_columns = {"Data_group", "Forest_type", "Feature_order", "Result_type", }
    missing_columns = sorted(required_columns - set(results.columns))

    if missing_columns:
        raise ValueError(
            f"File '{result_file.name}' does not contain required columns: "
            f"{missing_columns}"
        )

    # Ranking cech pobierany jest wyłącznie z wierszy Weight.
    weight_rows = results.loc[
        (results["Result_type"].astype(str).str.strip() == "Weight") & results["Feature_order"].notna()].copy()

    if weight_rows.empty:
        raise ValueError(
            f"File '{result_file.name}' does not contain any valid "
            "Weight rows with Feature_order."
        )

    feature_orders: dict[str, list[str]] = {}

    for _, result_row in weight_rows.iterrows():
        data_group = str(result_row["Data_group"]).strip()
        forest_type = str(result_row["Forest_type"]).strip().upper()

        if not data_group or data_group.lower() == "nan":
            raise ValueError(
                f"File '{result_file.name}' contains an empty Data_group value."
            )

        if forest_type not in VALID_FOREST_TYPES:
            raise ValueError(
                f"Invalid Forest_type '{forest_type}' in "
                f"'{result_file.name}'. Expected LS or NL."
            )

        dataset_key = f"{data_group}_{forest_type}"

        if dataset_key in feature_orders:
            raise ValueError(
                f"More than one ReliefF ranking was found for dataset "
                f"'{dataset_key}'."
            )

        feature_orders[dataset_key] = _parse_feature_order(result_row["Feature_order"])

    return feature_orders


def select_top_k_features(X: pd.DataFrame, results_directory: str | Path, dataset_name: str, k: int, ) -> tuple[
    pd.DataFrame, list[str]]:
    """Select the ``k`` best attributes according to a ReliefF ranking.

    :param X: Complete feature matrix containing all candidate attributes.
    :type X: pandas.DataFrame
    :param results_directory: Directory of one ReliefF execution.
    :type results_directory: str or pathlib.Path
    :param dataset_name: Dataset key, for example ``woda_LS`` or ``ptaki_NL``.
    :type dataset_name: str
    :param k: Number of highest-ranked attributes to retain.
    :type k: int
    :return: Selected feature DataFrame and ordered selected feature names.
    :rtype: tuple[pandas.DataFrame, list[str]]
    :raises KeyError: If the requested dataset or ranked features are absent.
    :raises ValueError: If ``k`` is outside the valid range.
    """

    feature_orders = load_feature_orders(results_directory)

    if dataset_name not in feature_orders:
        raise KeyError(
            f"Dataset '{dataset_name}' was not found in ReliefF results. "
            f"Available datasets: {list(feature_orders.keys())}"
        )

    feature_order = feature_orders[dataset_name]

    if not isinstance(k, int):
        raise TypeError("k must be an integer.")

    if k < 1:
        raise ValueError("k must be greater than zero.")

    if k > len(feature_order):
        raise ValueError(
            f"k={k} is greater than the number of ranked features "
            f"({len(feature_order)}) for dataset '{dataset_name}'."
        )

    top_k_features = feature_order[:k]
    missing_features = [feature for feature in top_k_features if feature not in X.columns]

    if missing_features:
        raise KeyError(
            "The following ReliefF-ranked features are missing from X: "
            f"{missing_features}"
        )

    return X.loc[:, top_k_features].copy(), top_k_features


def create_top_k_datasets(X: pd.DataFrame, results_directory: str | Path, dataset_name: str,
                          k_values: Iterable[int], ) -> dict[int, pd.DataFrame]:
    """Create several top-k feature datasets from one ReliefF ranking.

    :param X: Complete feature matrix containing all candidate attributes.
    :type X: pandas.DataFrame
    :param results_directory: Directory of one ReliefF execution.
    :type results_directory: str or pathlib.Path
    :param dataset_name: Dataset key, for example ``woda_LS``.
    :type dataset_name: str
    :param k_values: Numbers of highest-ranked attributes to retain.
    :type k_values: collections.abc.Iterable[int]
    :return: Mapping from k values to selected feature DataFrames.
    :rtype: dict[int, pandas.DataFrame]
    :raises KeyError: If the requested dataset or ranked features are absent.
    :raises ValueError: If one of the requested k values is invalid.
    """

    requested_k_values = list(k_values)

    if not requested_k_values:
        raise ValueError("k_values must contain at least one value.")

    feature_orders = load_feature_orders(results_directory)

    if dataset_name not in feature_orders:
        raise KeyError(
            f"Dataset '{dataset_name}' was not found in ReliefF results. "
            f"Available datasets: {list(feature_orders.keys())}"
        )

    feature_order = feature_orders[dataset_name]
    missing_ranked_features = [feature for feature in feature_order if feature not in X.columns]

    if missing_ranked_features:
        raise KeyError(
            "The following ReliefF-ranked features are missing from X: "
            f"{missing_ranked_features}"
        )

    top_k_datasets: dict[int, pd.DataFrame] = {}

    for k in requested_k_values:
        if not isinstance(k, int):
            raise TypeError(
                f"Every k value must be an integer. Invalid value: {k!r}"
            )

        if k < 1:
            raise ValueError(
                f"Every k value must be greater than zero. Invalid value: {k}"
            )

        if k > len(feature_order):
            raise ValueError(
                f"k={k} is greater than the number of ranked features "
                f"({len(feature_order)}) for dataset '{dataset_name}'."
            )

        top_k_features = feature_order[:k]
        top_k_datasets[k] = X.loc[:, top_k_features].copy()

    return top_k_datasets


def _build_top_k_dataframe(dataset: dict[str, Any], X_selected: pd.DataFrame, ) -> pd.DataFrame:
    """Build a complete top-k dataset containing Name, features and Klasa.

    :param dataset: Prepared dataset containing ``names``, ``X`` and ``y``.
    :type dataset: dict[str, typing.Any]
    :param X_selected: Selected top-k conditional attributes.
    :type X_selected: pandas.DataFrame
    :return: DataFrame containing Name, selected features and Klasa.
    :rtype: pandas.DataFrame
    """

    names = dataset["names"].reset_index(drop=True).rename("Name")
    X_selected = X_selected.reset_index(drop=True)
    y = dataset["y"].reset_index(drop=True).rename("Klasa")

    return pd.concat([names, X_selected, y], axis=1)


def _load_info_sheet(source_file: str | Path) -> pd.DataFrame:
    """Load the first INFO worksheet while preserving its original layout.

    :param source_file: LS or NL ReliefF source-data workbook.
    :type source_file: str or pathlib.Path
    :return: INFO worksheet without interpreting its first row as a header.
    :rtype: pandas.DataFrame
    """

    return pd.read_excel(
        source_file,
        sheet_name=0,
        header=None,
        engine="openpyxl",
    )


def save_top_k_dataset_workbooks(results_directory: str | Path, k_values: Iterable[int],
                                 output_directory: str | Path | None = None, ) -> dict[int, dict[str, Path]]:
    """Create LS and NL top-k workbooks from one completed ReliefF run.

    The function reads the two source-data workbooks already saved in the run
    directory. Only worksheets 2-6 are used as biological datasets; worksheet
    1 (``INFO``) is copied to every generated workbook. ReliefF rankings are
    loaded from the single ``result_relief_...xlsx`` file using
    ``Data_group`` and ``Forest_type`` identifiers.

    For every requested ``k`` value, two files are generated::

        dane_top10_LS_2026-09-07_13-12-14.xlsx
        dane_top10_NL_2026-09-07_13-12-14.xlsx

    Each generated workbook contains six worksheets in the original order:
    ``INFO``, ``woda``, ``rosliny``, ``ssaki``, ``ptaki`` and
    ``bezkregowce``.

    :param results_directory: Directory of one completed ReliefF execution.
    :type results_directory: str or pathlib.Path
    :param k_values: Numbers of highest-ranked ReliefF attributes to retain.
    :type k_values: collections.abc.Iterable[int]
    :param output_directory: Destination directory. ``None`` saves files
        directly in ``results_directory``.
    :type output_directory: str or pathlib.Path or None
    :return: Mapping from k values to generated LS and NL workbook paths.
    :rtype: dict[int, dict[str, pathlib.Path]]
    :raises ValueError: If rankings, source datasets or k values are invalid.
    """

    results_directory = Path(results_directory)
    output_directory = (Path(output_directory) if output_directory is not None else results_directory)

    requested_k_values = list(k_values)
    if not requested_k_values:
        raise ValueError("k_values must contain at least one value.")

    output_directory.mkdir(parents=True, exist_ok=True)

    run_date, run_time = _extract_relief_run_timestamp(results_directory)
    run_files = get_relief_run_files(results_directory)
    forest_datasets = load_relief_run_datasets(results_directory)
    feature_orders = load_feature_orders(results_directory)

    required_dataset_keys = [f"{dataset_name}_{forest_type}" for dataset_name in SHEETS for forest_type in
                             VALID_FOREST_TYPES]

    missing_datasets = [dataset_key for dataset_key in required_dataset_keys if dataset_key not in forest_datasets]
    if missing_datasets:
        raise ValueError(
            "The ReliefF source-data workbooks do not contain all required "
            f"datasets. Missing datasets: {missing_datasets}"
        )

    missing_rankings = [dataset_key for dataset_key in required_dataset_keys if dataset_key not in feature_orders]
    if missing_rankings:
        raise ValueError(
            "The ReliefF result workbook does not contain all required LS/NL "
            f"rankings. Missing rankings: {missing_rankings}"
        )

    # Wczytanie arkuszy INFO osobno dla danych LS i NL.
    info_sheets = {forest_type: _load_info_sheet(run_files[forest_type]) for forest_type in VALID_FOREST_TYPES}

    # Przygotowanie wybranych atrybutów tylko raz dla każdego zbioru i wartości k.
    top_k_cache: dict[str, dict[int, pd.DataFrame]] = {}

    for dataset_key in required_dataset_keys:
        dataset = forest_datasets[dataset_key]
        feature_order = feature_orders[dataset_key]

        missing_ranked_features = [feature for feature in feature_order if feature not in dataset["X"].columns]
        if missing_ranked_features:
            raise KeyError(
                f"Dataset '{dataset_key}' does not contain ReliefF-ranked "
                f"features: {missing_ranked_features}"
            )

        top_k_cache[dataset_key] = {}

        for k in requested_k_values:
            if not isinstance(k, int):
                raise TypeError(
                    f"Every k value must be an integer. Invalid value: {k!r}"
                )
            if k < 1:
                raise ValueError(
                    f"Every k value must be greater than zero. Invalid value: {k}"
                )
            if k > len(feature_order):
                raise ValueError(
                    f"k={k} is greater than the number of ranked features "
                    f"({len(feature_order)}) for dataset '{dataset_key}'."
                )

            top_features = feature_order[:k]
            top_k_cache[dataset_key][k] = dataset["X"].loc[:, top_features].copy()

    saved_files: dict[int, dict[str, Path]] = {}

    for k in requested_k_values:
        output_files = {forest_type: (output_directory / f"dane_top{k}_{forest_type}_{run_date}_{run_time}.xlsx")
                        for forest_type in VALID_FOREST_TYPES
                        }

        for forest_type, output_file in output_files.items():
            with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
                info_sheets[forest_type].to_excel(writer, sheet_name="INFO", index=False, header=False, )

                # Zapis pięciu grup biologicznych w kolejności zgodnej z dane.xlsx.
                for dataset_name in SHEETS:
                    dataset_key = f"{dataset_name}_{forest_type}"
                    source_dataset = forest_datasets[dataset_key]
                    X_selected = top_k_cache[dataset_key][k]
                    output_df = _build_top_k_dataframe(dataset=source_dataset, X_selected=X_selected, )
                    output_df.to_excel(writer, sheet_name=dataset_name, index=False, )

            print(f"Saved top-{k} {forest_type} dataset: {output_file}")

        saved_files[k] = output_files

    return saved_files


if __name__ == "__main__":
    # Wskazanie katalogu jednego konkretnego uruchomienia ReliefF.
    results_directory = (PROJECT_ROOT / "result_Relief" / "2026-09-07_13-12-14")

    # Lista liczby najlepszych atrybutów, dla których mają powstać pliki.
    k_values = [10, 15]

    # Pliki top-k są zapisywane bezpośrednio obok wyników danego uruchomienia.
    saved_files = save_top_k_dataset_workbooks(results_directory=results_directory, k_values=k_values,
                                               output_directory=results_directory, )

    print()
    print("=" * 80)
    print("GENERATED TOP-K LS/NL DATASETS")
    print("=" * 80)

    for k, files in saved_files.items():
        print()
        print(f"TOP-{k}")
        print(f"  LS: {files['LS']}")
        print(f"  NL: {files['NL']}")
