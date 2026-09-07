from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd
from skrebate import ReliefF

try:
    from .utils import prepare_all_datasets, prepare_forest_datasets
except ImportError:
    from utils import prepare_all_datasets, prepare_forest_datasets

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXCEL_PATH = PROJECT_ROOT / "dane.xlsx"
FOREST_SHARE_PATH = PROJECT_ROOT / "Udzial lasu.xlsx"
RESULTS_PATH = PROJECT_ROOT / "result_Relief"

BIOLOGICAL_GROUPS = (
    "woda",
    "rosliny",
    "ssaki",
    "ptaki",
    "bezkregowce",
)

RELIEF_FEATURE_COLUMNS = (
    "R3W1_LS", "R3W2_LS", "R3W3_LS", "R3W4_LS", "R3W5_LS",
    "R3W1_NL", "R3W2_NL", "R3W3_NL", "R3W4_NL", "R3W5_NL",
    "R2W1_LS", "R2W2_LS", "R2W3_LS", "R2W4_LS", "R2W5_LS",
    "R2W1_NL", "R2W2_NL", "R2W3_NL", "R2W4_NL", "R2W5_NL",
    "R1W1_LS", "R1W2_LS", "R1W3_LS", "R1W4_LS", "R1W5_LS",
    "R1W1_NL", "R1W2_NL", "R1W3_NL", "R1W4_NL", "R1W5_NL",
)


class ReliefFExperiment:
    """Represent one ReliefF feature-selection experiment.

    Each instance stores one dataset, the ReliefF configuration, the trained
    model, feature weights and metadata required to reproduce the experiment.

    :ivar X: Copy of the conditional-attribute matrix used by ReliefF.
    :vartype X: pandas.DataFrame
    :ivar y: Copy of the decision-class vector.
    :vartype y: pandas.Series
    :ivar names: Optional object identifiers corresponding to rows in ``X``.
    :vartype names: pandas.Series or None
    :ivar dataframe_name: Name identifying the biological group and LS/NL subset.
    :vartype dataframe_name: str
    :ivar model: Trained ``skrebate.ReliefF`` model, or None before execution.
    :vartype model: ReliefF or None
    :ivar weights_series: Feature weights sorted from highest to lowest.
    :vartype weights_series: pandas.Series or None
    :ivar experiment_id: Unique time-based experiment identifier.
    :vartype experiment_id: str
    :ivar dataset_hash: SHA-256 hash identifying the exact ``X`` and ``y``.
    :vartype dataset_hash: str
    """

    def __init__(
            self,
            X: pd.DataFrame,
            y: pd.Series,
            dataframe_name: str,
            names: Optional[pd.Series] = None,
            n_neighbors: int = 10,
            n_features_to_select: Optional[int] = None,
            n_jobs: int = -1,
            verbose: bool = True,
            output_directory: str | Path = "result_Relief",
    ):
        """Initialize a ReliefF experiment.

        :param X: Numeric conditional attributes used by ReliefF.
        :type X: pandas.DataFrame
        :param y: Decision classes corresponding to rows in ``X``.
        :type y: pandas.Series
        :param dataframe_name: Dataset name, for example ``woda``,
            ``woda_LS`` or ``woda_NL``.
        :type dataframe_name: str
        :param names: Optional object identifiers corresponding to rows in
            ``X``.
        :type names: pandas.Series or None
        :param n_neighbors: Number of nearest neighbors used by ReliefF.
        :type n_neighbors: int
        :param n_features_to_select: Number of features selected by ReliefF.
            None retains weights for every feature.
        :type n_features_to_select: int or None
        :param n_jobs: Number of CPU cores used by ReliefF. The value -1 uses
            all available cores.
        :type n_jobs: int
        :param verbose: Whether progress messages should be displayed.
        :type verbose: bool
        :param output_directory: Directory in which result workbooks are
            stored.
        :type output_directory: str or pathlib.Path
        :raises TypeError: If ``X`` is not a DataFrame or ``y`` is not a Series.
        :raises ValueError: If the dataset or ReliefF parameters are invalid.
        """

        self.X = X.copy()
        self.y = y.copy()
        self.names = names.copy() if names is not None else None
        self.dataframe_name = dataframe_name
        self.n_neighbors = n_neighbors
        self.n_features_to_select = n_features_to_select
        self.n_jobs = n_jobs
        self.verbose = verbose
        self.output_directory = Path(output_directory)

        self.model = None
        self.weights_series = None
        self.start_time = None
        self.execution_time = None
        self.execution_duration_ms = None

        self.experiment_id = self._generate_experiment_id()
        self.dataset_hash = self._generate_dataset_hash()

        self._validate_input()

    def _generate_dataset_hash(self) -> str:
        """Generate a deterministic hash for the exact input dataset.

        The hash includes feature names, feature dtypes, values and indexes of
        both ``X`` and ``y``. It therefore identifies the precise data version
        used in the experiment.

        :return: SHA-256 hexadecimal digest representing ``X`` and ``y``.
        :rtype: str
        """

        hasher = hashlib.sha256()
        hasher.update("|".join(map(str, self.X.columns)).encode("utf-8"))
        hasher.update("|".join(map(str, self.X.dtypes)).encode("utf-8"))

        x_hashes = pd.util.hash_pandas_object(self.X, index=True)
        hasher.update(x_hashes.values.tobytes())

        y_hashes = pd.util.hash_pandas_object(self.y, index=True)
        hasher.update(y_hashes.values.tobytes())

        return hasher.hexdigest()

    @staticmethod
    def _generate_experiment_id() -> str:
        """Generate a unique identifier based on date, time and microseconds.

        :return: Identifier in ``YYYYMMDD_HHMMSS_microseconds`` format.
        :rtype: str
        """

        return datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    def _validate_input(self) -> None:
        """Validate the dataset and all ReliefF parameters.

        :return: None.
        :rtype: None
        :raises TypeError: If ``X`` is not a DataFrame or ``y`` is not a Series.
        :raises ValueError: If data dimensions, names or ReliefF parameters are
            inconsistent.
        """

        if not isinstance(self.X, pd.DataFrame):
            raise TypeError("X must be a pandas DataFrame.")
        if not isinstance(self.y, pd.Series):
            raise TypeError("y must be a pandas Series.")
        if self.X.empty:
            raise ValueError("The input feature dataset cannot be empty.")
        if not isinstance(self.dataframe_name, str) or not self.dataframe_name.strip():
            raise ValueError("The dataframe name must be a non-empty string.")
        if len(self.X) != len(self.y):
            raise ValueError("X and y must contain the same number of observations.")
        if self.names is not None and len(self.names) != len(self.X):
            raise ValueError("names and X must contain the same number of observations.")
        if self.X.shape[1] < 1:
            raise ValueError("X must contain at least one feature.")
        if self.n_neighbors < 1:
            raise ValueError("The number of neighbors must be greater than zero.")
        if self.n_neighbors >= len(self.X):
            raise ValueError(
                "The number of neighbors must be smaller than the number "
                f"of observations. Dataset '{self.dataframe_name}' contains "
                f"{len(self.X)} observations, but n_neighbors={self.n_neighbors}."
            )
        if self.n_features_to_select is not None:
            if self.n_features_to_select < 1:
                raise ValueError(
                    "n_features_to_select must be greater than zero or None."
                )
            if self.n_features_to_select > self.X.shape[1]:
                raise ValueError(
                    "n_features_to_select cannot be greater than the number "
                    "of features."
                )

        self._validate_numeric_features()

    def _validate_numeric_features(self) -> None:
        """Check whether every feature passed to ReliefF is numeric.

        :return: None.
        :rtype: None
        :raises ValueError: If at least one column in ``X`` is non-numeric.
        """

        non_numeric_columns = self.X.select_dtypes(exclude="number").columns.tolist()
        if not non_numeric_columns:
            return

        if self.verbose:
            print("\nNon-numeric feature columns:")
            for column in non_numeric_columns:
                print(f"\nColumn: {column}")
                print(self.X[column].loc[self.X[column].notna()].head(10).to_string())

        raise ValueError(
            "All features used by ReliefF must be numeric. Non-numeric "
            f"columns: {non_numeric_columns}"
        )

    def run(self) -> pd.Series:
        """Run ReliefF and calculate feature-importance weights.

        The method creates the model, measures execution time, fits ReliefF to
        ``X`` and ``y``, and stores weights sorted from highest to lowest.

        :return: Feature weights indexed by feature name and sorted in
            descending order.
        :rtype: pandas.Series
        """

        if self.verbose:
            print("=" * 60)
            print("STARTING RELIEFF EXPERIMENT")
            print("=" * 60)
            print(f"Dataset name: {self.dataframe_name}")
            print(f"Number of observations: {len(self.X)}")
            print(f"Number of features: {self.X.shape[1]}")
            print("Creating ReliefF model...")

        self.model = ReliefF(
            n_features_to_select=self.n_features_to_select,
            n_neighbors=self.n_neighbors,
            verbose=self.verbose,
            n_jobs=self.n_jobs,
        )

        self.start_time = datetime.now()
        start_timer = time.perf_counter()
        self.model.fit(self.X.values, self.y.values)
        self.execution_duration_ms = (time.perf_counter() - start_timer) * 1000
        self.execution_time = datetime.now()

        self.weights_series = pd.Series(
            self.model.feature_importances_,
            index=self.X.columns,
            name="Weight",
        ).sort_values(ascending=False)

        if self.verbose:
            print("ReliefF experiment completed successfully.")
            print(f"Execution duration: {self.execution_duration_ms:.3f} ms")
            print("=" * 60)

        return self.weights_series

    def print_results(self) -> None:
        """Display experiment metadata, feature weights and ranking.

        :return: None.
        :rtype: None
        :raises RuntimeError: If :meth:`run` has not been called.
        """

        self._check_if_executed()

        print()
        print("=" * 60)
        print("RELIEFF RESULTS")
        print("=" * 60)
        print(f"Experiment ID: {self.experiment_id}")
        print(f"Dataset: {self.dataframe_name}")
        print(f"Execution duration: {self.execution_duration_ms:.3f} ms")
        print("\nFeature importance vector:")
        print(self.weights_series)
        print("\nFeature ranking:")

        for rank, (feature, weight) in enumerate(self.weights_series.items(), start=1):
            print(f"{rank}. {feature}: {weight:.6f}")

    @staticmethod
    def _split_dataset_name(dataframe_name: str) -> tuple[Optional[str], str]:
        """Separate the LS/NL suffix from a prepared dataset name.

        For example, ``woda_LS`` is converted to ``("LS", "woda")``. A name
        without a recognised suffix is returned as ``(None, name)``.

        :param dataframe_name: Complete, LS or NL dataset name.
        :type dataframe_name: str
        :return: Forest-type prefix and biological group name.
        :rtype: tuple[str or None, str]
        """

        stripped_name = dataframe_name.strip()
        for forest_type in ("LS", "NL"):
            suffix = f"_{forest_type}"
            if stripped_name.upper().endswith(suffix):
                return forest_type, stripped_name[:-len(suffix)]

        return None, stripped_name

    @staticmethod
    def _safe_file_name(value: str) -> str:
        """Replace characters that may be problematic in a file name.

        :param value: Raw value used as part of a file name.
        :type value: str
        :return: Sanitized file-name component.
        :rtype: str
        """

        return value.strip().replace(" ", "_").replace("/", "_").replace("\\", "_")

    @staticmethod
    def create_run_directory(base_directory: str | Path) -> Path:
        """Create and return a unique timestamped directory for one program run.

        The basic directory name uses the ``YYYY-MM-DD_HH-MM-SS`` format. If
        another run is started within the same second, a numeric suffix is
        added so that results are never appended to a directory from an older
        run. The directory is intended to contain both the ReliefF workbook
        and datasets prepared by ``utils.py`` during the same execution.

        :param base_directory: Parent directory for ReliefF result runs.
        :type base_directory: str or pathlib.Path
        :return: Newly created unique run directory.
        :rtype: pathlib.Path
        """

        base_directory = Path(base_directory)
        base_directory.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        run_directory = base_directory / timestamp
        suffix = 1

        while run_directory.exists():
            run_directory = base_directory / f"{timestamp}_{suffix:02d}"
            suffix += 1

        run_directory.mkdir(parents=False, exist_ok=False)
        return run_directory

    def _get_output_file(self) -> Path:
        """Return the shared ReliefF workbook path for the current run.

        All datasets processed during one program execution use the same
        ``output_directory`` and therefore the same workbook. For a run
        directory named ``2026-09-07_12-31-45`` the workbook is named
        ``result_relief_2026-09-07_12-31-45.xlsx``.

        :return: Complete path to the shared ReliefF result workbook.
        :rtype: pathlib.Path
        """

        self.output_directory.mkdir(parents=True, exist_ok=True)
        run_identifier = self._safe_file_name(self.output_directory.name)
        file_name = f"result_relief_{run_identifier}.xlsx"
        return self.output_directory / file_name

    def _get_parameters(self) -> dict:
        """Return the ReliefF configuration saved with experiment results.

        :return: Dictionary containing the algorithm name and parameters.
        :rtype: dict
        """

        return {
            "algorithm": "ReliefF",
            "n_neighbors": self.n_neighbors,
            "n_features_to_select": self.n_features_to_select,
            "n_jobs": self.n_jobs,
        }

    def save_results(self) -> Path:
        """Save experiment results using the existing Excel layout.

        All experiments from one program execution are stored in one workbook.
        Each experiment uses a weight row followed by a rank row. ``Data_group``
        identifies the biological group (for example ``ptaki`` or ``ssaki``),
        while ``Forest_type`` identifies ``LS``, ``NL`` or ``ALL``. Feature
        columns retain their input order and ``Feature_order`` stores feature
        names sorted from the highest to the lowest ReliefF weight. A completely
        empty row separates consecutive experiments.

        :return: Path to the created or updated Excel workbook.
        :rtype: pathlib.Path
        :raises RuntimeError: If :meth:`run` has not been called.
        """

        self._check_if_executed()
        output_file = self._get_output_file()

        forest_type, group_name = self._split_dataset_name(self.dataframe_name)
        forest_type = forest_type or "ALL"

        base_result = {
            "Experiment_ID": self.experiment_id,
            "Data_group": group_name,
            "Forest_type": forest_type,
            "Algorithm": "ReliefF",
            "Number_of_observations": len(self.X),
            "Number_of_features": self.X.shape[1],
            "Target_column": "Klasa",
            "n_neighbors": self.n_neighbors,
            "n_features_to_select": self.n_features_to_select,
            "n_jobs": self.n_jobs,
            "Parameters_JSON": json.dumps(
                self._get_parameters(), ensure_ascii=False
            ),
        }

        weight_row = base_result.copy()
        weight_row["Result_type"] = "Weight"

        # Zapisz pełną kolejność cech od najsilniejszej do najsłabszej zgodnie z wagą ReliefF jako lista do pliku.
        feature_order = self.weights_series.index.tolist()
        weight_row["Feature_order"] = str(feature_order)

        rank_row = {column: None for column in base_result}
        rank_row["Experiment_ID"] = self.experiment_id
        rank_row["Data_group"] = group_name
        rank_row["Forest_type"] = forest_type
        rank_row["Result_type"] = "Rank"
        rank_row["Feature_order"] = None

        feature_ranks = {
            feature: rank
            for rank, feature in enumerate(self.weights_series.index, start=1)
        }

        # Zachowaj dokładną kolejność cech z wejściowego obiektu DataFrame.
        for feature in self.X.columns:
            weight_row[feature] = self.weights_series[feature]
            rank_row[feature] = feature_ranks[feature]

        experiment_rows = pd.DataFrame([weight_row, rank_row])

        if output_file.exists():
            if self.verbose:
                print(f"Loading previous results from: {output_file}")

            existing_results = pd.read_excel(output_file)

            for column in experiment_rows.columns:
                if column not in existing_results.columns:
                    existing_results[column] = None
            for column in existing_results.columns:
                if column not in experiment_rows.columns:
                    experiment_rows[column] = None

            experiment_rows = experiment_rows[existing_results.columns]
            final_results = pd.concat(
                [existing_results, experiment_rows],
                ignore_index=True,
            )

            # Wstaw jeden całkowicie pusty wiersz przed nowym eksperymentem.
            # Ponowne indeksowanie pozwala uniknąć ostrzeżeń dotyczących typu danych (dtype) spowodowanych
            # dołączeniem dodatkowego DataFrame’a zawierającego wyłącznie wartości NA.
            insertion_position = len(existing_results)
            rows_with_separator = (
                    list(range(insertion_position))
                    + ["__empty_row__"]
                    + list(range(insertion_position, len(final_results)))
            )
            final_results = final_results.reindex(rows_with_separator).reset_index(drop=True)
        else:
            if self.verbose:
                print(f"Creating a new results file: {output_file}")
            final_results = experiment_rows

        base_columns = [
            "Experiment_ID",
            "Data_group",
            "Forest_type",
            "Algorithm",
            "Number_of_observations",
            "Number_of_features",
            "Target_column",
            "n_neighbors",
            "n_features_to_select",
            "n_jobs",
            "Parameters_JSON",
            "Feature_order",
            "Result_type",
        ]

        # Ułóż cechy w stałej kolejności zgodnej z plikiem dane.xlsx.
        feature_columns = [
            column
            for column in RELIEF_FEATURE_COLUMNS
            if column in final_results.columns
        ]
        remaining_feature_columns = [
            column
            for column in final_results.columns
            if column not in base_columns and column not in feature_columns
        ]
        ordered_columns = (
                [column for column in base_columns if column in final_results.columns]
                + feature_columns
                + remaining_feature_columns
        )

        final_results = final_results[ordered_columns]
        final_results.to_excel(output_file, index=False)

        if self.verbose:
            print("=" * 60)
            print("RESULTS SAVED SUCCESSFULLY")
            print("=" * 60)
            print(f"Experiment ID: {self.experiment_id}")
            print(f"Dataset hash: {self.dataset_hash[:12]}...")
            print(f"Output file: {output_file}")

        return output_file

    def _check_if_executed(self) -> None:
        """Check whether the current experiment has already been executed.

        :return: None.
        :rtype: None
        :raises RuntimeError: If :meth:`run` has not been called.
        """

        if self.weights_series is None:
            raise RuntimeError(
                "The experiment has not been executed yet. Call run() before "
                "accessing or saving results."
            )


def save_forest_data_workbooks(
        datasets: dict,
        source_data_file: str | Path,
        output_directory: str | Path,
) -> dict[str, Path]:
    """Save complete LS and NL observations in two Excel workbooks.

    The function creates one workbook for LS observations and one workbook for
    NL observations. Both workbooks follow the six-sheet structure of the
    original ecological data workbook: the first sheet is ``INFO`` and the next
    five sheets correspond to water, plants, mammals, birds and invertebrates.
    Every biological worksheet contains ``Name``, all 30 conditional
    attributes and ``Klasa`` for the selected forest type.

    :param datasets: Flat LS/NL mapping returned by
        :func:`prepare_forest_datasets`.
    :type datasets: dict
    :param source_data_file: Original ``dane.xlsx`` workbook used to copy the
        INFO sheet and biological worksheet names.
    :type source_data_file: str or pathlib.Path
    :param output_directory: Directory created for the current ReliefF run.
    :type output_directory: str or pathlib.Path
    :return: Mapping containing paths to the generated ``LS`` and ``NL``
        workbooks.
    :rtype: dict[str, pathlib.Path]
    :raises FileNotFoundError: If the source workbook does not exist.
    :raises ValueError: If the source workbook has fewer than six worksheets or
        a required LS/NL dataset is missing.
    """

    source_data_file = Path(source_data_file)
    output_directory = Path(output_directory)

    if not source_data_file.exists():
        raise FileNotFoundError(
            f"Source Excel file not found: {source_data_file}"
        )

    output_directory.mkdir(parents=True, exist_ok=True)

    excel_file = pd.ExcelFile(source_data_file, engine="openpyxl")
    source_sheet_names = excel_file.sheet_names

    if len(source_sheet_names) < 6:
        raise ValueError(
            "The source ecological workbook must contain at least six "
            "worksheets: INFO and five biological datasets."
        )

    # Odczytaj zawartość pierwszego arkusza bez interpretowania jego nagłówków.
    info_df = pd.read_excel(
        source_data_file,
        sheet_name=0,
        header=None,
        engine="openpyxl",
    )

    # Zachowaj nazwy pięciu arkuszy biologicznych z oryginalnego dane.xlsx.
    biological_sheet_names = dict(
        zip(BIOLOGICAL_GROUPS, source_sheet_names[1:6])
    )

    run_identifier = ReliefFExperiment._safe_file_name(output_directory.name)
    output_files = {
        "LS": output_directory / f"data_LS_relief_{run_identifier}.xlsx",
        "NL": output_directory / f"data_NL_relief_{run_identifier}.xlsx",
    }

    for forest_type, output_file in output_files.items():
        with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
            # Pierwszy arkusz ma zawsze nazwę INFO, zgodnie z plikiem źródłowym.
            info_df.to_excel(
                writer,
                sheet_name="INFO",
                index=False,
                header=False,
            )

            for group_name in BIOLOGICAL_GROUPS:
                dataset_name = f"{group_name}_{forest_type}"

                if dataset_name not in datasets:
                    raise ValueError(
                        f"Required prepared dataset '{dataset_name}' is missing."
                    )

                prepared_df = datasets[dataset_name]["df"].copy()

                # Zapisz Name, komplet 30 atrybutów i klasę bez zmiany kolejności kolumn.
                prepared_df.to_excel(
                    writer,
                    sheet_name=biological_sheet_names[group_name],
                    index=False,
                )

        print(f"Prepared {forest_type} workbook saved: {output_file}")

    return output_files


def basic_run_example() -> ReliefFExperiment:
    """Run a small example using the current X/y constructor interface.

    :return: Executed experiment containing the example results.
    :rtype: ReliefFExperiment
    """

    X = pd.DataFrame(
        {
            "Age": [25, 25, 26, 35, 40, 45, 50, 55],
            "BloodPressure": [120, 118, 130, 140, 135, 150, 155, 160],
            "Cholesterol": [180, 190, 200, 230, 220, 250, 260, 270],
            "BMI": [31.5, 22.0, 24.0, 28.0, 27.0, 30.0, 31.0, 33.0],
        }
    )
    y = pd.Series([1, 0, 0, 1, 1, 1, 1, 1], name="Class")

    experiment = ReliefFExperiment(
        X=X,
        y=y,
        dataframe_name="X",
        n_neighbors=2,
        n_features_to_select=None,
        n_jobs=-1,
        verbose=True,
    )
    experiment.run()
    experiment.print_results()
    experiment.save_results()
    return experiment


def run_relief_for_dataset(datasets: dict, dataset_name: str, n_neighbors: int = 10,
                           n_features_to_select: Optional[int] = None, n_jobs: int = -1, verbose: bool = True,
                           output_directory: str | Path = "result_Relief", ) -> ReliefFExperiment:
    """Run and save ReliefF for one prepared dataset.

    :param datasets: Mapping returned by ``prepare_all_datasets`` or
        ``prepare_forest_datasets``.
    :type datasets: dict
    :param dataset_name: Selected dataset key, for example ``woda``,
        ``woda_LS`` or ``woda_NL``.
    :type dataset_name: str
    :param n_neighbors: Number of nearest neighbors used by ReliefF.
    :type n_neighbors: int
    :param n_features_to_select: Number of features selected by ReliefF, or
        None to retain all weights.
    :type n_features_to_select: int or None
    :param n_jobs: Number of CPU cores. The value -1 uses all cores.
    :type n_jobs: int
    :param verbose: Whether progress and results should be printed.
    :type verbose: bool
    :param output_directory: Run directory containing the shared result workbook.
    :type output_directory: str or pathlib.Path
    :return: Executed and saved ReliefF experiment.
    :rtype: ReliefFExperiment
    :raises ValueError: If ``dataset_name`` is not present in ``datasets``.
    """

    if dataset_name not in datasets:
        raise ValueError(
            f"Unknown dataset: '{dataset_name}'. Available datasets: "
            f"{list(datasets.keys())}"
        )

    dataset = datasets[dataset_name]
    experiment = ReliefFExperiment(
        X=dataset["X"],
        y=dataset["y"],
        names=dataset["names"],
        dataframe_name=dataset_name,
        n_neighbors=n_neighbors,
        n_features_to_select=n_features_to_select,
        n_jobs=n_jobs,
        verbose=verbose,
        output_directory=output_directory,
    )
    experiment.run()
    experiment.print_results()
    experiment.save_results()
    return experiment


def run_relief_for_datasets(datasets: dict, dataset_names: Optional[Iterable[str]] = None, n_neighbors: int = 10,
                            n_features_to_select: Optional[int] = None, n_jobs: int = -1, verbose: bool = True,
                            output_directory: str | Path = "result_Relief", ) -> dict[str, ReliefFExperiment]:
    """Run ReliefF for all or selected prepared datasets.

    :param datasets: Mapping returned by ``prepare_all_datasets`` or
        ``prepare_forest_datasets``.
    :type datasets: dict
    :param dataset_names: Names to run. None selects every available dataset.
    :type dataset_names: collections.abc.Iterable[str] or None
    :param n_neighbors: Number of nearest neighbors used by every experiment.
    :type n_neighbors: int
    :param n_features_to_select: Number of features selected by ReliefF, or
        None to retain all weights.
    :type n_features_to_select: int or None
    :param n_jobs: Number of CPU cores. The value -1 uses all cores.
    :type n_jobs: int
    :param verbose: Whether progress and results should be printed.
    :type verbose: bool
    :param output_directory: Run directory containing the shared result workbook.
    :type output_directory: str or pathlib.Path
    :return: Mapping from dataset names to completed experiment objects.
    :rtype: dict[str, ReliefFExperiment]
    :raises ValueError: If any selected name is absent from ``datasets``.
    """

    selected_names = list(dataset_names) if dataset_names is not None else list(datasets)
    experiments = {}

    for dataset_name in selected_names:
        experiments[dataset_name] = run_relief_for_dataset(
            datasets=datasets,
            dataset_name=dataset_name,
            n_neighbors=n_neighbors,
            n_features_to_select=n_features_to_select,
            n_jobs=n_jobs,
            verbose=verbose,
            output_directory=output_directory,
        )

    return experiments


if __name__ == "__main__":
    # Ustaw wartość „True”, aby przeprowadzić 10 oddzielnych eksperymentów LS/NL.
    # Ustaw wartość „False”, aby zachować 5 eksperymentów na pełnym zbiorze danych.
    USE_FOREST_SPLIT = True

    # Jeden katalog odpowiada dokładnie jednemu uruchomieniu programu.
    # Trafiają do niego zarówno plik wynikowy ReliefF, jak i pliki danych
    # przygotowane przez utils.py podczas tego samego uruchomienia.
    current_run_results_path = ReliefFExperiment.create_run_directory(
        RESULTS_PATH
    )

    if USE_FOREST_SPLIT:
        datasets = prepare_forest_datasets(
            data_file=EXCEL_PATH,
            classes_dir=PROJECT_ROOT,
            forest_file=FOREST_SHARE_PATH,
            output_dir=None,
            output_format="xlsx",
        )

        # Dostępne nazwy: woda_LS, woda_NL, rosliny_LS, rosliny_NL,
        # ssaki_LS, ssaki_NL, ptaki_LS, ptaki_NL, bezkregowce_LS
        # i bezkregowce_NL.
        datasets_to_run = None  # None oznacza: uruchom wszystkie dostępne zbiory.
    else:
        datasets = prepare_all_datasets(
            data_file=EXCEL_PATH,
            classes_dir=PROJECT_ROOT,
        )
        datasets_to_run = None

    run_relief_for_datasets(
        datasets=datasets,
        dataset_names=datasets_to_run,
        n_neighbors=10,
        n_features_to_select=None,
        n_jobs=-1,
        verbose=True,
        output_directory=current_run_results_path,
    )

    if USE_FOREST_SPLIT:
        # Po zakończeniu ReliefF utwórz dwa zbiorcze pliki danych: LS i NL.
        save_forest_data_workbooks(
            datasets=datasets,
            source_data_file=EXCEL_PATH,
            output_directory=current_run_results_path,
        )
