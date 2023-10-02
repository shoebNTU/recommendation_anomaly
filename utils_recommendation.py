import itertools
import logging

import numpy as np
import pandas as pd

from config_logging import setup_logging

# setup logging
setup_logging(logging, logging.DEBUG)
_logger = logging.getLogger(__name__)


def get_anomaly_recommendation(
    anomaly: pd.DataFrame,
    defect: pd.DataFrame,
    proximity: float = 0,
    min_percentage: float = 0.5,
    min_severity_improvement: int = 1,
    min_overlap_extent: float = 0.1,
    anomaly_recommendation_id_start: int = 0,
):
    """Returns anomaly_recommendation dataframe

    Args:
        anomaly (pd.DataFrame): content of anomaly table
        defect (pd.DataFrame): content of defect table
        proximity (float): proximity tolerance of anomaly to defect. Defaults to 0.
        min_percentage (float): anomaly-length/defect range minimum percentage. Defaults to 0.5.
        min_severity_improvement (int): minimum severity improvement to create a new Defect. Defaults to 1.
        min_overlap_extent (float): overlap extent in percentage. Defaults to 0.1, i.e. 10%.
        anomaly_recommendation_id_start (int, optional): last index of anomaly recommendation table. Defaults to 0.

    Returns:
        anomaly_recommendation (pd.DataFrame): to be ingested into the anomaly_recommendation table
    """
    anomaly_recommendation = pd.DataFrame(
        columns=[
            "anomaly_recommendation_id",
            "anomaly_id",
            "recommended_action_id",
            "recommended_defect_id",
            "user",
            "modified_dttm",
        ]
    )

    if anomaly.shape[0] == 0:
        return anomaly_recommendation

    # fill values in anomaly recommendation dataframe
    anomaly_recommendation["anomaly_id"] = anomaly.anomaly_id.values
    anomaly_recommendation["anomaly_recommendation_id"] = (
        anomaly_recommendation_id_start + anomaly_recommendation.index
    )

    recommendations = []
    recommended_defect_id = []

    if len(defect) == 0:  # if defect doesn't exist
        _logger.debug("No past defects exist. Let's create new defects.")
        anomaly_recommendation["recommended_action_id"] = "Create New Defect"
        return anomaly_recommendation

    # this section will be executed if defects exist
    _logger.debug("past defects exist")
    defect["length"] = defect["end_pos"] - defect["start_pos"]

    for _, row in anomaly.iterrows():

        overlapping_index = defect[
            (
                (
                    (defect.start_pos <= row.end_pos + proximity)
                    & (defect.start_pos >= row.start_pos - proximity)
                )
                | (
                    (defect.end_pos <= row.end_pos + proximity)
                    & (defect.end_pos >= row.start_pos - proximity)
                )
            )
        ].index.values

        if len(overlapping_index) > 1:
            # if no. of associated defects > 1,
            # check for min_overlap_extent as well
            overlapping_index = defect[
                (
                    (
                        (defect.start_pos <= row.end_pos + proximity)
                        & (defect.start_pos >= row.start_pos - proximity)
                    )
                    | (
                        (defect.end_pos <= row.end_pos + proximity)
                        & (defect.end_pos >= row.start_pos - proximity)
                    )
                )
                & (
                    (
                        defect["end_pos"].apply(lambda x: min(x, row.end_pos))
                        - defect["start_pos"].apply(lambda x: max(x, row.start_pos))
                    )
                    / row.length
                    >= min_overlap_extent
                )
            ].index.values

        if (len(overlapping_index) == 1) and (
            row.defect_code_id
            - defect.loc[overlapping_index]["defect_code_id"].values[0]
            >= min_severity_improvement
        ):  # severity has improved

            # create new defect
            create_string = "Create New Defect"
            _logger.debug(create_string)
            recommendations.append(create_string)
            recommended_defect_id.append(np.nan)

        elif (len(overlapping_index) == 1) and (
            row.length / defect.loc[overlapping_index]["length"].values[0]
            < min_percentage
        ):
            create_string = "Create New Defect"
            _logger.debug(create_string)
            recommendations.append(create_string)
            recommended_defect_id.append(np.nan)

        elif len(overlapping_index) == 1:  # default scenario
            past_tag = "Tag to past defect/s"
            _logger.debug(past_tag)
            recommendations.append(past_tag)
            recommended_defect_id.append(
                list(defect.loc[overlapping_index]["defect_id"])
            )

        elif (len(overlapping_index) > 1) and (
            (row.defect_code_id - defect.loc[overlapping_index]["defect_code_id"])
            >= min_severity_improvement
        ).all():
            # all associated defects have severity improvements >= min_severity_improvement

            # create new defects
            create_string = "Create New Defect"
            _logger.debug(create_string)
            recommendations.append(create_string)
            recommended_defect_id.append(np.nan)

        elif (
            (len(overlapping_index) > 1)
            and (
                (
                    (
                        row.defect_code_id
                        - defect.loc[overlapping_index]["defect_code_id"]
                        < min_severity_improvement
                    )
                ).sum()
                == 1
            )
            and row.length
            / defect.loc[
                (
                    (
                        row.defect_code_id
                        - defect.loc[overlapping_index]["defect_code_id"]
                        < min_severity_improvement
                    )[
                        row.defect_code_id
                        - defect.loc[overlapping_index]["defect_code_id"]
                        < min_severity_improvement
                    ].index
                ),
                "length",
            ].values[0]
            < min_percentage
        ):
            # only one defect < min_sev_improvement and anomaly/defect_range < min_percentage
            create_string = "Create New Defect"
            _logger.debug(create_string)
            recommendations.append(create_string)
            recommended_defect_id.append(np.nan)

        elif (
            (len(overlapping_index) > 1)
            and (
                (
                    (
                        row.defect_code_id
                        - defect.loc[overlapping_index]["defect_code_id"]
                        < min_severity_improvement
                    )
                ).sum()
                == 1
            )
            and row.length
            / defect.loc[
                (
                    (
                        row.defect_code_id
                        - defect.loc[overlapping_index]["defect_code_id"]
                        < min_severity_improvement
                    )[
                        row.defect_code_id
                        - defect.loc[overlapping_index]["defect_code_id"]
                        < min_severity_improvement
                    ].index
                ),
                "length",
            ].values[0]
            >= min_percentage
        ):
            # only one defect < min_sev_improvement and anomaly/defect_range >= min_percentage
            # add to existing defects
            past_tag = "Tag to past defect/s"
            _logger.debug(past_tag)
            recommendations.append(past_tag)
            past_defects_list = defect.loc[
                (
                    row.defect_code_id - defect.loc[overlapping_index]["defect_code_id"]
                    < min_severity_improvement
                )[
                    row.defect_code_id - defect.loc[overlapping_index]["defect_code_id"]
                    < min_severity_improvement
                ].index
            ]["defect_id"].to_list()
            recommended_defect_id.append(past_defects_list)

        elif (len(overlapping_index) > 1) and (
            (
                (
                    row.defect_code_id - defect.loc[overlapping_index]["defect_code_id"]
                    < min_severity_improvement
                )
            ).sum()
            > 1
        ):
            # more than one defect < min_sev_improvement
            # add those defects to recommendation whose anomaly-length/defect-range >= min_percentage
            anomaly_to_defect_ratio = (
                row.length
                / defect.loc[
                    (
                        (
                            row.defect_code_id
                            - defect.loc[overlapping_index]["defect_code_id"]
                            < min_severity_improvement
                        )[
                            (
                                row.defect_code_id
                                - defect.loc[overlapping_index]["defect_code_id"]
                                < min_severity_improvement
                            )
                        ].index
                    ),
                    "length",
                ]
            ) >= min_percentage
            past_defects_list = (
                defect.loc[overlapping_index]["defect_id"]
                .loc[(anomaly_to_defect_ratio[anomaly_to_defect_ratio == True]).index]
                .to_list()
            )

            past_tag_dict = {0: "Create New Defect"}
            past_tag = past_tag_dict.get(len(past_defects_list), "Tag to past defect/s")
            _logger.debug(past_tag)
            recommendations.append(past_tag)
            past_defects_list_dict = {0: np.nan}
            recommended_defect_id.append(
                past_defects_list_dict.get(len(past_defects_list), past_defects_list)
            )

        else:
            create_string = "Create New Defect"
            _logger.debug(create_string)
            recommendations.append(create_string)
            recommended_defect_id.append(np.nan)

    anomaly_recommendation["recommended_action_id"] = recommendations
    anomaly_recommendation["recommended_defect_id"] = recommended_defect_id

    return anomaly_recommendation


def get_defect_recommendation(
    anomaly_recommendation: pd.DataFrame, defect: pd.DataFrame
):
    """Returns defect_recommendation

    Args:
        anomaly_recommendation (pd.DataFrame): anomaly recommendations from latest inspection run
        defect (pd.DataFrame): contents of defect able

    Returns:
        defect_recommendation (pd.DataFrame): defect recommendation dataframe primarily to close non-existent defects
    """

    recommended_defects = set(
        list(
            itertools.chain(
                *list(anomaly_recommendation.recommended_defect_id.dropna())
            )
        )
    )
    existing_defects = set(defect.defect_id)
    defect_recommendation = pd.DataFrame(
        columns=[
            "defect_recommendation_id",
            "defect_id",
            "recommended_action_id",
            "review_status_id",
            "user",
            "modified_dttm",
        ]
    )
    defect_recommendation.defect_id = list(existing_defects - recommended_defects)
    defect_recommendation.recommended_action_id = "Close"
    defect_recommendation.defect_recommendation_id = defect_recommendation.index

    return defect_recommendation
