import mido
import music21
import os
import traceback
import time

def get_midi_bpm(midi_filepath):
    print(f"DEBUG: get_midi_bpm 함수 시작. 파일 경로: {midi_filepath}") # 추가
    if not os.path.exists(midi_filepath):
        print(f"오류: MIDI 파일이 존재하지 않습니다 - {midi_filepath}")
        return None

    try:
        print(f"DEBUG: music21.converter.parse 실행 직전. 경로: {midi_filepath}") # 추가
        score = music21.converter.parse(midi_filepath)
        print(f"DEBUG: music21.converter.parse 성공.") # 추가
        
        metronome_marks = score.flat.getElementsByClass(music21.tempo.MetronomeMark)
        
        if metronome_marks:
            bpm = metronome_marks[0].number
            print(f"MIDI 파일 '{os.path.basename(midi_filepath)}'에서 BPM 추출 (music21): {bpm}")
            return bpm
        else:
            print(f"경고: MIDI 파일 '{os.path.basename(midi_filepath)}'에서 템포 정보(BPM)를 찾을 수 없습니다.")
            return None
            
    except music21.midi.base.MidiException as e: # music21.midi.base.MidiException으로 더 구체화
        print(f"music21 MIDI 파싱 오류 ({midi_filepath}): {e}")
        traceback.print_exc()
        return None
    except Exception as e:
        print(f"MIDI 파일 분석 중 알 수 없는 오류 발생 ({midi_filepath}): {e}")
        traceback.print_exc()
        return None


if __name__ == '__main__':
    print("--- BPM 추출 테스트 시작 ---")
    test_midi_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'example.mid')

    # 기존 example.mid 파일을 먼저 삭제하고 새로 생성
    if os.path.exists(test_midi_file_path):
        try:
            os.remove(test_midi_file_path)
            print(f"DEBUG: 기존 파일 '{test_midi_file_path}' 삭제됨.")
        except Exception as e:
            print(f"DEBUG: 기존 파일 삭제 실패 '{test_midi_file_path}': {e}")
            # 삭제 실패해도 일단 진행 (다른 프로세스가 잠금을 가지고 있을 수도 있음)


    print(f"DEBUG: 테스트용 MIDI 파일 생성 시도: {test_midi_file_path}")
    try:
        s = music21.stream.Stream()
        s.insert(0, music21.tempo.MetronomeMark(number=100)) # BPM 100 설정
        s.append(music21.note.Note('C4', quarterLength=1)) # C4 음표 1박자 추가
        s.append(music21.note.Note('D4', quarterLength=1)) # D4 음표 1박자 추가
        
        # MIDI 파일로 저장 (music21의 더 명시적이고 견고한 쓰기 방식 재확인)
        mf = music21.midi.translate.streamToMidiFile(s)
        # file.open('wb') 대신 with 문을 직접 사용하여 파일이 확실히 닫히도록 합니다.
        with open(test_midi_file_path, 'wb') as fp:
            mf.write(fp) # fp에 직접 씁니다.
        
        time.sleep(0.5) # 파일이 완전히 기록될 시간을 충분히 기다림 (0.1초에서 0.5초로 늘림)

        print(f"테스트용 music21 더미 MIDI 파일 생성됨: {test_midi_file_path}")
    except Exception as e:
        print(f"테스트용 MIDI 파일 생성 중 오류 발생 (music21): {e}")
        traceback.print_exc()


    bpm = get_midi_bpm(test_midi_file_path)
    if bpm is not None:
        print(f"추출된 BPM: {bpm}")
    else:
        print("BPM 추출 실패.")

    print("\n--- 존재하지 않는 MIDI 파일 테스트 ---")
    bpm_none = get_midi_bpm("non_existent.mid")
    print(f"결과: {bpm_none}")
    print("--- BPM 추출 테스트 종료 ---")