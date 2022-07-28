import pandas as pd


def process_answers(
    responses: dict,
    questions_mapping: dict,
    multi_choice_columns: list,
    language="english",
    translation_mapping=None,
) -> pd.DataFrame:
    # Parsing of the individual responses (one per person who answered)
    if language != "english" and translation_mapping == None:
        raise ValueError("Error, a translation dictionary is missing.")

    parsed_data = {"create_time": [], "email": []} | {
        value: [] for value in questions_mapping[language].values()
    }

    for response in responses:
        parsed_data["create_time"].append(response["createTime"])
        parsed_data["email"].append(response["respondentEmail"])
        # Parsing of the answers to each question as a list aggregation
        for key, value in response["answers"].items():
            corresponding_column = questions_mapping[language][key]
            # nb_answers = len(value['textAnswers']['answers'])
            match (language, corresponding_column):
                case (
                    language,
                    corresponding_column,
                ) if language == "english" and corresponding_column not in multi_choice_columns:
                    all_answers = value["textAnswers"]["answers"][0]["value"]
                case (
                    language,
                    corresponding_column,
                ) if language == "english" and corresponding_column in multi_choice_columns:
                    all_answers = [
                        answer["value"] for answer in value["textAnswers"]["answers"]
                    ]
                case (
                    language,
                    corresponding_column,
                ) if language == "french" and corresponding_column not in multi_choice_columns:
                    raw_answer = value["textAnswers"]["answers"][0]["value"]
                    all_answers = translation_mapping[corresponding_column][raw_answer]
                case (
                    language,
                    corresponding_column,
                ) if language == "french" and corresponding_column in multi_choice_columns:
                    all_answers = [
                        translation_mapping[corresponding_column][answer["value"]]
                        for answer in value["textAnswers"]["answers"]
                    ]

            parsed_data[corresponding_column].append(all_answers)

        # Handles unanswered questions
        unanswered_questions_ids = list(
            set(questions_mapping[language].keys()) - set(response["answers"].keys())
        )
        for question_id in unanswered_questions_ids:
            corresponding_column = questions_mapping[language][question_id]
            parsed_data[corresponding_column].append(None)

    df = pd.DataFrame(data=parsed_data)
    return df


def generate_exploded_df(
    df: pd.DataFrame,
    cols_to_keep: list,
    multi_choice_columns: list,
    # new_column_names: dict,
) -> pd.DataFrame:
    df_exploded = df.loc[:, cols_to_keep]
    current_multi_choice_columns = list(
        set(cols_to_keep).intersection(set(multi_choice_columns))
    )
    for column in current_multi_choice_columns:
        df_exploded = df_exploded.explode(column=column).reset_index(drop=True)
    # df_exploded = df_exploded.rename(columns=new_column_names)
    return df_exploded


def _generate_value_counts(se: pd.Series, is_multichoice_column: bool) -> pd.Series:
    if is_multichoice_column:
        res_se = se.explode().value_counts(ascending=True)
    else:
        res_se = se.value_counts(ascending=True)
    return res_se


def generate_value_counts_df(
    df: pd.DataFrame, selected_column: str, multi_choice_columns: list
) -> pd.DataFrame:
    if selected_column in multi_choice_columns:
        is_multi_choice_column = True
    else:
        is_multi_choice_column = False

    df_count = (
        _generate_value_counts(df.loc[:, selected_column], is_multi_choice_column)
        .to_frame()
        .reset_index()
        .rename(
            columns={"index": "Possible choices", selected_column: "Number of answers"}
        )
    )

    return df_count



