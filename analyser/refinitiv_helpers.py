import re


def cleaner(text: str):
    if text.isupper():
        text = text.title()
    elif re.search(r"[A-Z]{3}(?<![A-Z]{4})(?![A-Z])", text) != None:
        pass
    else:
        text = re.sub(
            r"(\w)([A-Z])", r"\1 \2", text
        )  # searches for company name with one uppercase character
    return text


def search_fund_name(sub_fund_name: str, main_fund_names: list):
    for main_fund_name in main_fund_names:
        if main_fund_name.lower() in sub_fund_name.lower():
            return main_fund_name
    return ""
