import json
import datetime
import os

def load_json(filepath):
    """
    JSON 파일을 로드하여 Python 객체로 반환합니다.

    Args:
        filepath (str): 로드할 JSON 파일의 경로.

    Returns:
        dict or list: 로드된 JSON 데이터. 파일이 없거나 유효하지 않으면 None 반환.
    """
    if not os.path.exists(filepath):
        print(f"경고: 파일이 존재하지 않습니다 - {filepath}")
        return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError:
        print(f"오류: 유효하지 않은 JSON 형식입니다 - {filepath}")
        return None
    except Exception as e:
        print(f"JSON 파일 로드 중 오류 발생 ({filepath}): {e}")
        return None

def save_json(data, filepath):
    """
    Python 객체를 JSON 파일로 저장합니다.

    Args:
        data (dict or list): 저장할 Python 객체.
        filepath (str): 저장할 JSON 파일의 경로.
    """
    try:
        # 디렉토리가 없으면 생성
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"데이터가 성공적으로 저장되었습니다: {filepath}")
    except Exception as e:
        print(f"JSON 파일 저장 중 오류 발생 ({filepath}): {e}")

def get_current_timestamp(format="%Y%m%d_%H%M%S"):
    """
    현재 시간을 지정된 형식의 문자열로 반환합니다.

    Args:
        format (str): 시간 형식 문자열 (기본값: YYYYMMDD_HHMMSS).

    Returns:
        str: 형식화된 현재 시간 문자열.
    """
    return datetime.datetime.now().strftime(format)

if __name__ == '__main__':
    # --- 함수 테스트 예시 ---

    # 1. JSON 파일 저장 테스트
    # test_filepath를 현재 스크립트가 실행되는 폴더 기준으로 설정
    test_filepath = os.path.join(os.path.dirname(__file__), "test_config.json") # 이 줄을 수정
    test_data = {
        "project_name": "Jiobi_music",
        "version": "1.0.0",
        "creation_date": get_current_timestamp(),
        "settings": {
            "output_directory": "./output_music",
            "default_bpm": 120
        },
        "recent_files": ["music1.wav", "music2.wav"]
    }
    save_json(test_data, test_filepath)

    # 2. JSON 파일 로드 테스트
    loaded_data = load_json(test_filepath)
    if loaded_data:
        print("\n로드된 데이터:")
        print(json.dumps(loaded_data, indent=4, ensure_ascii=False))

    # 3. 존재하지 않는 파일 로드 테스트
    print("\n존재하지 않는 파일 로드 테스트:")
    non_existent_data = load_json("non_existent_file.json")
    print(f"결과: {non_existent_data}")

    # 4. 잘못된 JSON 파일 로드 테스트 (수동으로 test_invalid.json 파일을 생성하여 테스트 가능)
    # with open("test_invalid.json", "w", encoding="utf-8") as f:
    #     f.write("{'key': 'value'") # 유효하지 않은 JSON
    # print("\n잘못된 JSON 파일 로드 테스트:")
    # invalid_data = load_json("test_invalid.json")
    # print(f"결과: {invalid_data}")

    # 5. 타임스탬프 생성 테스트
    print(f"\n현재 타임스탬프 (기본 형식): {get_current_timestamp()}")
    print(f"현재 타임스탬프 (다른 형식): {get_current_timestamp(format='%Y-%m-%d %H:%M:%S')}")