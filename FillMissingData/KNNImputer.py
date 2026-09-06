from __future__ import annotations

import math
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterable, Literal, Optional

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT_FILE = PROJECT_ROOT / "dane.xlsx"
DEFAULT_FOREST_FILE = PROJECT_ROOT / "Udzial_lasu.xlsx"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "results_knn_imputer"

DatasetScope = Literal["ALL", "LS", "NL"]
MetricDirection = Literal["min", "max"]
MetricFunction = Callable[[np.ndarray, np.ndarray], float]

FEATURE_PATTERN = re.compile(r"^R[123]W[1-5](?:_|\s+|-)?(LS|NL)$", re.IGNORECASE)


@dataclass
class ImputationSummary:
    """Store a summary of one dataset/scope generated during a KNN run.

    :param run_signature: Shared date/time signature identifying the run.
    :param run_datetime: Human-readable date and time of the run.
    :param dataset: Stable dataset name, e.g. ``ptaki`` or ``ssaki``.
    :param sheet_name: Original Excel worksheet name.
    :param scope: Output scope: ``ALL``, ``LS`` or ``NL``.
    :param output_file: Name of the workbook generated for the scope.
    :param number_of_objects: Number of objects saved in the scope.
    :param number_of_features: Number of ecological features used by KNN.
    :param missing_before: Number of missing cells before imputation in the
        complete biological group.
    :param imputed_values: Number of cells filled during imputation of the
        complete biological group.
    :param missing_after: Number of missing feature cells remaining in the
        saved scope.
    :param n_neighbors: Number of neighbours used by KNN.
    :param metric: Metric name recorded for the run.
    :param metric_direction: ``min`` when smaller metric values are better or
        ``max`` when larger values are better.
    """

    run_signature: str
    run_datetime: str
    dataset: str
    sheet_name: str
    scope: DatasetScope
    output_file: str
    number_of_objects: int
    number_of_features: int
    missing_before: int
    imputed_values: int
    missing_after: int
    n_neighbors: int
    metric: str
    metric_direction: MetricDirection


class KNNDataImputer:
    """Impute missing ecosystem data using the k-nearest-neighbours method.

    The imputer operates on original ecological feature values, e.g.
    ``R3W1_LS`` or ``R1W5_NL``, before decision weights and decision intervals
    are applied by the existing project code.

    Even when LS or NL output files are requested, neighbour search is always
    performed using **all objects from a given biological group**. LS/NL
    splitting is performed only after the full group has been imputed.

    A custom metric can be supplied as any callable accepting two one-
    dimensional :class:`numpy.ndarray` objects and returning a single numeric
    distance or similarity value.

    :param n_neighbors: Number of nearest neighbours used to estimate a
        missing value.
    :type n_neighbors: int
    :param metric: Built-in metric name (``"euclidean"`` or ``"manhattan"``)
        or a custom callable metric.
    :type metric: str or Callable[[numpy.ndarray, numpy.ndarray], float]
    :param metric_direction: Defines which metric values represent better
        neighbours. Use ``"min"`` for distances and ``"max"`` for
        similarities.
    :type metric_direction: {"min", "max"}
    :param output_directory: Directory in which KNN result files are saved.
    :type output_directory: str or pathlib.Path
    :raises ValueError: If ``n_neighbors`` or ``metric_direction`` is invalid.
    """

    def __init__(
            self,
            n_neighbors: int = 5,
            metric: str | MetricFunction = "euclidean",
            metric_direction: MetricDirection = "min",
            output_directory: str | Path = DEFAULT_OUTPUT_DIR,
    ) -> None:
        if n_neighbors < 1:
            raise ValueError("n_neighbors must be >= 1")
        if metric_direction not in {"min", "max"}:
            raise ValueError("metric_direction must be either 'min' or 'max'")

        self.n_neighbors = int(n_neighbors)
        self.metric = metric
        self.metric_direction = metric_direction
        self.output_directory = Path(output_directory)
        self.output_directory.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _create_run_signature(run_datetime: datetime) -> str:
        """Create the date/time signature used in all files from one run.

        :param run_datetime: Date and time at which the run started.
        :type run_datetime: datetime.datetime
        :return: Signature in ``YYYYMMDD_HHMMSS_ffffff`` format.
        :rtype: str
        """
        return run_datetime.strftime("%Y%m%d_%H%M%S_%f")

    @staticmethod
    def _dataset_name(sheet_name: str) -> str:
        """Return a stable dataset name based on an Excel worksheet name.

        :param sheet_name: Original Excel worksheet name.
        :type sheet_name: str
        :return: Normalized dataset name.
        :rtype: str
        """
        normalized = sheet_name.lower()
        mapping = {
            "woda": "woda",
            "roślin": "rosliny",
            "roslin": "rosliny",
            "ssaki": "ssaki",
            "ptaki": "ptaki",
            "bezkreg": "bezkregowce",
            "bezkręg": "bezkregowce",
            "korytar": "korytarze",
        }
        for token, name in mapping.items():
            if token in normalized:
                return name
        return re.sub(r"[^a-zA-Z0-9_-]+", "_", sheet_name).strip("_").lower()

    @staticmethod
    def feature_columns(df: pd.DataFrame) -> list[str]:
        """Return ecological indicator columns used for KNN imputation.

        The matcher accepts both the standard form, e.g. ``R1W4_LS``, and
        variants already present in project data such as ``R1W4 LS``.

        :param df: DataFrame whose columns should be inspected.
        :type df: pandas.DataFrame
        :return: Ecological feature column names in their original order.
        :rtype: list[str]
        """
        return [
            str(col)
            for col in df.columns
            if isinstance(col, str) and FEATURE_PATTERN.fullmatch(col)
        ]

    def _metric_name(self) -> str:
        """Return a readable metric name for reports and parameter files.

        :return: Built-in or custom metric name.
        :rtype: str
        """
        if isinstance(self.metric, str):
            return self.metric.lower()
        return getattr(self.metric, "__name__", self.metric.__class__.__name__)

    def _metric_metadata(self) -> dict[str, Any]:
        """Return serializable information describing the configured metric.

        Built-in metrics leave custom-metric fields empty. For a user-defined
        callable, the function object itself is not written to the parameter
        workbook; instead its module and qualified name are stored.

        :return: Metric metadata suitable for ``KNN_parameters.xlsx``.
        :rtype: dict[str, Any]
        """
        if isinstance(self.metric, str):
            return {
                "Metric": self._metric_name(),
                "Metric_Direction": self.metric_direction,
                "Custom_Metric_Module": "",
                "Custom_Metric_Qualified_Name": "",
            }

        return {
            "Metric": self._metric_name(),
            "Metric_Direction": self.metric_direction,
            "Custom_Metric_Module": getattr(self.metric, "__module__", ""),
            "Custom_Metric_Qualified_Name": getattr(
                self.metric,
                "__qualname__",
                self._metric_name(),
            ),
        }

    def _distance(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate metric value on coordinates observed in both objects.

        :param a: Feature vector of the first object.
        :type a: numpy.ndarray
        :param b: Feature vector of the second object.
        :type b: numpy.ndarray
        :return: Metric value or ``numpy.nan`` when no comparison is possible.
        :rtype: float
        :raises ValueError: If an unsupported built-in metric name is used.
        """
        valid = ~np.isnan(a) & ~np.isnan(b)
        if not np.any(valid):
            return np.nan

        a_valid = a[valid]
        b_valid = b[valid]

        if callable(self.metric):
            value = float(self.metric(a_valid, b_valid))
        else:
            metric = self.metric.lower()
            if metric in {"euclidean", "l2"}:
                value = float(np.linalg.norm(a_valid - b_valid, ord=2))
            elif metric in {"manhattan", "cityblock", "l1"}:
                value = float(np.linalg.norm(a_valid - b_valid, ord=1))
            else:
                raise ValueError(
                    "Unsupported metric. Use 'euclidean', 'manhattan' or pass "
                    "a custom callable metric."
                )

        if not math.isfinite(value):
            return np.nan
        return value

    def impute_dataframe(self, df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
        """Impute missing ecological feature values in one complete group.

        Additional non-feature columns are preserved unchanged. Missing values
        are estimated as the arithmetic mean of the target feature among the
        selected neighbours. The result is deliberately **not rounded**.

        :param df: DataFrame containing object identifiers and ecological
            features.
        :type df: pandas.DataFrame
        :return: Copy of ``df`` with imputed feature values and the number of
            cells filled.
        :rtype: tuple[pandas.DataFrame, int]
        :raises ValueError: If an entire feature column is missing and no value
            can be estimated.
        """
        result = df.copy(deep=True)
        features = self.feature_columns(result)

        if not features:
            return result, 0

        # Wybór kolumn z pliku zawierających atrybuty warunkowe
        numeric = result[features].apply(pd.to_numeric, errors="coerce")
        original_missing = numeric.isna()
        missing_count = int(original_missing.sum().sum())

        if missing_count == 0:
            result.loc[:, features] = numeric
            return result, 0

        values = numeric.to_numpy(dtype=float)
        n_rows, _ = values.shape

        for row_idx in range(n_rows):
            missing_feature_indexes = np.where(np.isnan(values[row_idx]))[0]

            for feature_idx in missing_feature_indexes:
                candidates: list[tuple[float, float]] = []

                # Wartości w atrybucie uzupełnianym nie są uwzględniane przy porównaniu najbliższych obiektów.
                row_for_distance = values[row_idx].copy()
                row_for_distance[feature_idx] = np.nan

                for candidate_idx in range(n_rows):
                    if candidate_idx == row_idx:
                        continue

                    target_value = values[candidate_idx, feature_idx]
                    if np.isnan(target_value):
                        continue

                    candidate_for_distance = values[candidate_idx].copy()
                    candidate_for_distance[feature_idx] = np.nan
                    score = self._distance(row_for_distance, candidate_for_distance)

                    if np.isnan(score):
                        continue
                    candidates.append((score, float(target_value)))

                if not candidates:
                    # Jeśli brak podobnych obiektów, zastosować średnią z całej kolumny docelowej.
                    observed = values[:, feature_idx]
                    observed = observed[~np.isnan(observed)]
                    if len(observed) == 0:
                        raise ValueError(
                            f"Cannot impute column '{features[feature_idx]}': "
                            "the entire feature is missing."
                        )
                    values[row_idx, feature_idx] = float(np.mean(observed))
                    continue

                reverse = self.metric_direction == "max"
                candidates.sort(key=lambda item: item[0], reverse=reverse)
                neighbours = candidates[: min(self.n_neighbors, len(candidates))]

                # Zachowana rzeczywista średnia bez zaokrągleń.
                values[row_idx, feature_idx] = float(np.mean([target for _, target in neighbours]))

        result.loc[:, features] = values
        imputed_count = missing_count - int(np.isnan(values).sum())
        return result, imputed_count

    @staticmethod
    def _load_membership(forest_file: str | Path) -> pd.DataFrame:
        """Load the ``Name -> LS/NL`` mapping Names of frames as forest(LS) or no forest(NL).

        :param forest_file: Path to ``Udzial_lasu.xlsx`` or an equivalent file.
        :type forest_file: str or pathlib.Path
        :return: DataFrame containing normalized ``Name`` and ``LS/NL`` columns.
        :rtype: pandas.DataFrame
        :raises FileNotFoundError: If the membership file does not exist.
        :raises ValueError: If required columns are missing.
        """
        path = Path(forest_file)
        if not path.exists():
            raise FileNotFoundError(
                f"LS/NL file not found: {path}. "
                "ALL output can still be generated without this file."
            )

        membership = pd.read_excel(path, sheet_name=0, engine="openpyxl")
        required = {"Name", "LS/NL"}
        missing = required.difference(membership.columns)
        if missing:
            raise ValueError(
                f"The LS/NL file must contain columns {sorted(required)}. "
                f"Missing: {sorted(missing)}"
            )

        membership = membership[["Name", "LS/NL"]].copy()
        membership["LS/NL"] = membership["LS/NL"].astype(str).str.upper().str.strip()
        return membership

    @staticmethod
    def _filter_scope(df: pd.DataFrame, scope: DatasetScope, membership: Optional[pd.DataFrame], ) -> pd.DataFrame:
        """Filter an already-imputed DataFrame to ALL, LS or NL objects.

        :param df: Fully imputed DataFrame for one biological group.
        :type df: pandas.DataFrame
        :param scope: Requested output scope.
        :type scope: {"ALL", "LS", "NL"}
        :param membership: ``Name -> LS/NL`` mapping for LS/NL filtering.
        :type membership: pandas.DataFrame or None
        :return: DataFrame filtered to the requested scope.
        :rtype: pandas.DataFrame
        :raises ValueError: If LS/NL filtering is requested without membership
            data or without a ``Name`` column.
        """
        if scope == "ALL":
            return df.copy()

        if membership is None:
            raise ValueError("membership is required for LS/NL output")
        if "Name" not in df.columns:
            raise ValueError("Dataset does not contain the required 'Name' column")

        wanted = set(
            membership.loc[membership["LS/NL"] == scope, "Name"].astype(str)
        )
        mask = df["Name"].astype(str).isin(wanted)
        return df.loc[mask].copy()

    def _save_run_parameters(
            self,
            run_datetime: datetime,
            input_path: Path,
            forest_file: str | Path | None,
            scopes: tuple[DatasetScope, ...],
            output_files: dict[DatasetScope, Path],
    ) -> Path:
        """Append run parameters to the shared ``KNN_parameters.xlsx`` file.

        The workbook is created only once. Every subsequent execution appends
        one row for every generated output scope. The concrete output filename
        contains the date/time signature, so every parameter row can be linked
        directly to the generated imputed workbook.

        :param run_datetime: Date and time at which the run started.
        :type run_datetime: datetime.datetime
        :param input_path: Source workbook used by the run.
        :type input_path: pathlib.Path
        :param forest_file: Optional LS/NL membership file.
        :type forest_file: str or pathlib.Path or None
        :param scopes: Scopes requested during the run.
        :type scopes: tuple[DatasetScope, ...]
        :param output_files: Mapping from scope to generated workbook path.
        :type output_files: dict[DatasetScope, pathlib.Path]
        :return: Path to the shared parameter workbook.
        :rtype: pathlib.Path
        """
        metric_data = self._metric_metadata()
        parameter_columns = [
            "Run_DateTime",
            "Algorithm",
            "Input_File",
            "Forest_File",
            "Output_File",
            "Scope",
            "Requested_Scopes",
            "Metric",
            "Metric_Direction",
            "Custom_Metric_Module",
            "Custom_Metric_Qualified_Name",
            "Keep_Real_Values",
            "Rounding",
            "k_Neighbour",
        ]

        records: list[dict[str, Any]] = []
        for scope, output_path in output_files.items():
            records.append(
                {
                    "Run_DateTime": run_datetime.strftime("%Y-%m-%d %H:%M:%S.%f"),
                    "Algorithm": "KNN Imputer",
                    "Input_File": str(input_path.resolve()),
                    "Forest_File": (
                        str(Path(forest_file).resolve()) if forest_file is not None else ""
                    ),
                    "Output_File": str(output_path.resolve()),
                    "Scope": scope,
                    "Requested_Scopes": ",".join(scopes),
                    **metric_data,
                    "Keep_Real_Values": True,
                    "Rounding": "none",
                    # Number of nearest neighbours used during imputation.
                    "k_Neighbour": self.n_neighbors,
                }
            )

        parameter_path = self.output_directory / "KNN_parameters.xlsx"
        new_records = pd.DataFrame(records, columns=parameter_columns)

        if parameter_path.exists():
            previous_records = pd.read_excel(
                parameter_path,
                sheet_name="Parameters",
                engine="openpyxl",
            )

            previous_records = previous_records.reindex(columns=parameter_columns)
            records_to_save = pd.concat(
                [previous_records, new_records],
                ignore_index=True,
            )
        else:
            records_to_save = new_records

        with pd.ExcelWriter(parameter_path, engine="openpyxl") as writer:
            records_to_save.to_excel(
                writer,
                sheet_name="Parameters",
                index=False,
            )

        return parameter_path

    def impute_workbook(
            self,
            input_file: str | Path = DEFAULT_INPUT_FILE,
            forest_file: str | Path | None = DEFAULT_FOREST_FILE,
            scopes: Iterable[DatasetScope] = ("ALL", "LS", "NL"),
    ) -> list[ImputationSummary]:
        """Impute ecological datasets and save project-compatible workbooks.

        Every biological sheet is imputed exactly once using all objects from
        that sheet. LS/NL workbooks are created afterwards by filtering the
        completed data. One date/time signature is generated for the whole run
        and appended to all output files produced by that run.

        Example file names for one run are::

            KNN_ALL_dane_20260906_223500_418327.xlsx
            KNN_LS_dane_20260906_223500_418327.xlsx
            KNN_NL_dane_20260906_223500_418327.xlsx
            KNN_parameters.xlsx

        ``KNN_parameters.xlsx`` is shared by all runs. New parameter rows are
        appended instead of creating a new parameter file for each execution.

        :param input_file: Source Excel workbook containing ecological datasets.
        :type input_file: str or pathlib.Path
        :param forest_file: File containing ``Name`` and ``LS/NL`` columns.
            It is required only when LS or NL output is requested.
        :type forest_file: str or pathlib.Path or None
        :param scopes: Output scopes to generate.
        :type scopes: Iterable[{"ALL", "LS", "NL"}]
        :return: Summary records for all generated dataset/scope combinations.
        :rtype: list[ImputationSummary]
        :raises FileNotFoundError: If ``input_file`` does not exist.
        :raises ValueError: If scopes are invalid or LS/NL membership data is
            required but unavailable.
        """
        input_path = Path(input_file)
        if not input_path.exists():
            raise FileNotFoundError(f"Input workbook not found: {input_path}")

        run_datetime = datetime.now()
        run_signature = self._create_run_signature(run_datetime)

        normalized_scopes = tuple(str(scope).upper() for scope in scopes)
        invalid = [scope for scope in normalized_scopes if scope not in {"ALL", "LS", "NL"}]
        if invalid:
            raise ValueError(f"Unsupported scopes: {invalid}")
        scopes_tuple: tuple[DatasetScope, ...] = tuple(normalized_scopes)  # type: ignore[assignment]

        membership: Optional[pd.DataFrame] = None
        if any(scope in {"LS", "NL"} for scope in scopes_tuple):
            if forest_file is None:
                raise ValueError("forest_file is required when LS or NL is requested")
            membership = self._load_membership(forest_file)

        excel = pd.ExcelFile(input_path, engine="openpyxl")
        original_sheets: dict[str, pd.DataFrame] = {
            sheet: pd.read_excel(input_path, sheet_name=sheet, engine="openpyxl")
            for sheet in excel.sheet_names
        }

        completed_sheets: dict[str, pd.DataFrame] = {}
        per_sheet_info: dict[str, tuple[str, int, int, int, int]] = {}

        for sheet_name, df in original_sheets.items():
            features = self.feature_columns(df)

            # Kopiowanie arkuszy bez dancyh (INFO)
            if not features:
                completed_sheets[sheet_name] = df.copy()
                continue

            numeric = df[features].apply(pd.to_numeric, errors="coerce")
            missing_before = int(numeric.isna().sum().sum())
            completed, imputed_values = self.impute_dataframe(df)
            missing_after = int(
                completed[features]
                .apply(pd.to_numeric, errors="coerce")
                .isna()
                .sum()
                .sum()
            )

            dataset = self._dataset_name(sheet_name)
            completed_sheets[sheet_name] = completed
            per_sheet_info[sheet_name] = (
                dataset,
                len(df),
                len(features),
                missing_before,
                imputed_values,
            )

            print(
                f"[{dataset}] objects={len(df)}, features={len(features)}, "
                f"missing before={missing_before}, imputed={imputed_values}, "
                f"missing after={missing_after}"
            )

        summaries: list[ImputationSummary] = []
        output_files: dict[DatasetScope, Path] = {}
        stem = input_path.stem

        for scope in scopes_tuple:
            output_path = self.output_directory / (f"KNN_{scope}_{stem}_{run_signature}.xlsx")
            output_files[scope] = output_path

            with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
                for sheet_name in excel.sheet_names:
                    completed = completed_sheets[sheet_name]
                    features = self.feature_columns(completed)

                    if not features:
                        output_df = completed.copy()
                    else:
                        output_df = self._filter_scope(completed, scope, membership)

                    output_df.to_excel(writer, sheet_name=sheet_name, index=False)

                    if features:
                        dataset, _, number_of_features, missing_before, imputed_values = (per_sheet_info[sheet_name])
                        missing_after = int(
                            output_df[features].apply(pd.to_numeric, errors="coerce").isna().sum().sum())
                        summaries.append(
                            ImputationSummary(
                                run_signature=run_signature,
                                run_datetime=run_datetime.isoformat(timespec="seconds"),
                                dataset=dataset,
                                sheet_name=sheet_name,
                                scope=scope,
                                output_file=output_path.name,
                                number_of_objects=len(output_df),
                                number_of_features=number_of_features,
                                missing_before=missing_before,
                                imputed_values=imputed_values,
                                missing_after=missing_after,
                                n_neighbors=self.n_neighbors,
                                metric=self._metric_name(),
                                metric_direction=self.metric_direction,
                            )
                        )

            print(f"Saved: {output_path}")

        parameter_path = self._save_run_parameters(
            run_datetime=run_datetime,
            input_path=input_path,
            forest_file=forest_file,
            scopes=scopes_tuple,
            output_files=output_files,
        )
        print(f"Saved parameters: {parameter_path}")

        return summaries

    def evaluate_missingness(self, df: pd.DataFrame, missing_percentages: Iterable[float] = (0.05, 0.25, 0.50),
                             allow_zero_values: bool = False, random_state: int = 42, ) -> pd.DataFrame:
        """Evaluate KNN by hiding one known value in selected objects.

        The requested percentage refers to the percentage of objects. Exactly
        one feature is hidden in every selected object. By default, only values
        greater than zero may be hidden. Set ``allow_zero_values=True`` to also
        allow zero-valued features to become artificial missing values.

        :param df: Complete DataFrame used for the evaluation experiment.
        :type df: pandas.DataFrame
        :param missing_percentages: Fractions of objects in which one feature
            should be hidden, e.g. ``(0.05, 0.25, 0.50)``.
        :type missing_percentages: Iterable[float]
        :param allow_zero_values: Whether zero-valued features may be hidden.
        :type allow_zero_values: bool
        :param random_state: Seed controlling reproducible random selection.
        :type random_state: int
        :return: DataFrame containing MAE, MSE and RMSE for each missing-data
            percentage.
        :rtype: pandas.DataFrame
        :raises ValueError: If no ecological features are found or an invalid
            missing percentage is supplied.
        """
        features = self.feature_columns(df)
        if not features:
            raise ValueError("No ecological feature columns found")

        original = df.copy(deep=True)
        original.loc[:, features] = original[features].apply(
            pd.to_numeric,
            errors="coerce",
        )
        rng = np.random.default_rng(random_state)
        rows: list[dict[str, float | int | str | bool]] = []

        for percentage in missing_percentages:
            if not 0 < percentage <= 1:
                raise ValueError("Each missing percentage must be in the interval (0, 1]")

            candidates: list[tuple[int, int]] = []
            values = original[features].to_numpy(dtype=float)

            for row_idx in range(len(original)):
                valid_features = np.where(~np.isnan(values[row_idx]))[0]
                if not allow_zero_values:
                    valid_features = np.array(
                        [idx for idx in valid_features if values[row_idx, idx] > 0],
                        dtype=int,
                    )
                if len(valid_features) > 0:
                    candidates.append((row_idx, int(rng.choice(valid_features))))

            n_objects = max(1, int(round(len(original) * percentage)))
            if n_objects > len(candidates):
                raise ValueError(
                    f"Not enough eligible objects for missing_percentage={percentage:.2f}"
                )

            selected_indices = rng.choice(
                len(candidates),
                size=n_objects,
                replace=False,
            )
            selected = [candidates[int(i)] for i in selected_indices]

            damaged = original.copy(deep=True)
            expected: list[float] = []
            positions: list[tuple[int, str]] = []

            for row_idx, feature_idx in selected:
                feature = features[feature_idx]
                expected.append(float(damaged.at[damaged.index[row_idx], feature]))
                positions.append((row_idx, feature))
                damaged.at[damaged.index[row_idx], feature] = np.nan

            restored, _ = self.impute_dataframe(damaged)
            predicted = [
                float(restored.at[restored.index[row_idx], feature])
                for row_idx, feature in positions
            ]

            expected_np = np.asarray(expected, dtype=float)
            predicted_np = np.asarray(predicted, dtype=float)
            errors = predicted_np - expected_np

            rows.append(
                {
                    "missing_percentage": percentage,
                    "number_of_objects": len(original),
                    "number_of_hidden_values": n_objects,
                    "n_neighbors": self.n_neighbors,
                    "metric": self._metric_name(),
                    "metric_direction": self.metric_direction,
                    "allow_zero_values": allow_zero_values,
                    "MAE": float(np.mean(np.abs(errors))),
                    "MSE": float(np.mean(errors ** 2)),
                    "RMSE": float(np.sqrt(np.mean(errors ** 2))),
                }
            )

        return pd.DataFrame(rows)


def main() -> None:
    """Run default project imputation for ALL, LS and NL scopes.

    Edit the constructor parameters below to change ``k``, the built-in metric,
    metric direction or output directory. A custom callable metric may be passed
    in exactly the same place as the metric string.

    :return: None
    :rtype: None
    """
    imputer = KNNDataImputer(
        n_neighbors=5,
        metric="euclidean",
        metric_direction="min",
        output_directory=DEFAULT_OUTPUT_DIR,
    )

    # Wyniki ALL/LS/NL pochodzą z jednej imputacji przeprowadzonej na wszystkich obiektach dla każdej grupy (woda itp).
    # All uzupełnianie z całym zbiorze danych, obiektów leśnych (LS) lub nie leśnych (NL)
    imputer.impute_workbook(
        input_file=DEFAULT_INPUT_FILE,
        forest_file=DEFAULT_FOREST_FILE,
        scopes=("ALL", "LS", "NL"),
    )


if __name__ == "__main__":
    main()
