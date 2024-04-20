import re


def preprocess_text(text):
    # 한글, 영문, 숫자를 제외한 모든 문자 및 특수 문자 제거
    text = re.sub("[^ㄱ-ㅎㅏ-ㅣ가-힣a-zA-Z0-9]", " ", text)
    # 연속된 공백을 하나의 공백으로 변환
    text = re.sub("\s+", " ", text)
    # 양쪽 공백 제거
    text = text.strip()
    return text


def extract_prefix(text):
    text = text.split()[0]
    if "(" in text:
        text = text.split("(")[0]
    if "[" in text:
        text = text.split("[")[0]
    return text.strip()


def remove_prefix(string):
    return re.sub(r"^\d+:\s*", "", string)
