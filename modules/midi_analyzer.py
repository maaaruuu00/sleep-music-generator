import mido
import music21
import os
import traceback
import time
from collections import Counter

def get_midi_bpm(midi_filepath):
    # 이 함수는 이전과 동일하게 유지합니다.
    print(f"DEBUG: get_midi_bpm 함수 시작. 파일 경로: {midi_filepath}")
    if not os.path.exists(midi_filepath):
        print(f"오류: MIDI 파일이 존재하지 않습니다 - {midi_filepath}")
        return None

    try:
        print(f"DEBUG: music21.converter.parse 실행 직전. 경로: {midi_filepath}")
        score = music21.converter.parse(midi_filepath)
        print(f"DEBUG: music21.converter.parse 성공.")
        
        metronome_marks = score.flatten().getElementsByClass(music21.tempo.MetronomeMark)
        
        if metronome_marks:
            bpm = metronome_marks[0].number
            print(f"MIDI 파일 '{os.path.basename(midi_filepath)}'에서 BPM 추출 (music21): {bpm}")
            return bpm
        else:
            print(f"경고: MIDI 파일 '{os.path.basename(midi_filepath)}'에서 템포 정보(BPM)를 찾을 수 없습니다.")
            return None
            
    except music21.midi.base.MidiException as e:
        print(f"music21 MIDI 파싱 오류 ({midi_filepath}): {e}")
        traceback.print_exc()
        return None
    except Exception as e:
        print(f"MIDI 파일 분석 중 알 수 없는 오류 발생 ({midi_filepath}): {e}")
        traceback.print_exc()
        return None

def get_midi_key_and_scale(midi_filepath):
    # 이 함수는 이전과 동일하게 유지합니다.
    print(f"DEBUG: get_midi_key_and_scale 함수 시작. 파일 경로: {midi_filepath}")
    if not os.path.exists(midi_filepath):
        print(f"오류: MIDI 파일이 존재하지 않습니다 - {midi_filepath}")
        return None, None

    try:
        score = music21.converter.parse(midi_filepath)
        key = score.analyze('key') 
        
        key_name = str(key)
        scale_type = key.mode

        print(f"MIDI 파일 '{os.path.basename(midi_filepath)}'에서 키 및 스케일 추출: {key_name} ({scale_type})")
        return key_name, scale_type
        
    except music21.midi.base.MidiException as e:
        print(f"music21 MIDI 파싱 오류 ({midi_filepath}) [키/스케일]: {e}")
        traceback.print_exc()
        return None, None
    except Exception as e:
        print(f"키/스케일 분석 중 알 수 없는 오류 발생 ({midi_filepath}): {e}")
        traceback.print_exc()
        return None, None

def get_midi_chord_progression(midi_filepath):
    # 이 함수는 이전과 동일하게 유지합니다.
    print(f"DEBUG: get_midi_chord_progression 함수 시작. 파일 경로: {midi_filepath}")
    if not os.path.exists(midi_filepath):
        print(f"오류: MIDI 파일이 존재하지 않습니다 - {midi_filepath}")
        return []

    identified_chords = []
    try:
        score = music21.converter.parse(midi_filepath)
        
        for element in score.flatten().notesAndRests:
            if isinstance(element, music21.chord.Chord):
                identified_chords.append(element.fullName) 

        print(f"MIDI 파일 '{os.path.basename(midi_filepath)}'에서 화음 진행 추출: {identified_chords}")
        return identified_chords
        
    except music21.midi.base.MidiException as e:
        print(f"music21 MIDI 파싱 오류 ({midi_filepath}) [화음]: {e}")
        traceback.print_exc()
        return []
    except Exception as e:
        print(f"화음 진행 분석 중 알 수 없는 오류 발생 ({midi_filepath}): {e}")
        traceback.print_exc()
        return []

def get_midi_melody_patterns(midi_filepath, pattern_length=4, top_n=3):
    # 이 함수는 이전과 동일하게 유지합니다.
    print(f"DEBUG: get_midi_melody_patterns 함수 시작. 파일 경로: {midi_filepath}")
    if not os.path.exists(midi_filepath):
        print(f"오류: MIDI 파일이 존재하지 않습니다 - {midi_filepath}")
        return []

    try:
        score = music21.converter.parse(midi_filepath)
        
        note_sequences = []
        for p in score.flatten().notesAndRests:
            if p.isNote:
                note_sequences.append((p.pitch.nameWithOctave, p.quarterLength))
            elif p.isRest: 
                note_sequences.append(('Rest', p.quarterLength))
        
        patterns = []
        for i in range(len(note_sequences) - pattern_length + 1):
            pattern = tuple(note_sequences[i : i + pattern_length])
            patterns.append(pattern)
        
        pattern_counts = Counter(patterns)
        
        most_common_patterns = pattern_counts.most_common(top_n)

        print(f"MIDI 파일 '{os.path.basename(midi_filepath)}'에서 멜로디 패턴 추출 (상위 {top_n}개): {most_common_patterns}")
        return most_common_patterns
        
    except music21.midi.base.MidiException as e:
        print(f"music21 MIDI 파싱 오류 ({midi_filepath}) [멜로디 패턴]: {e}")
        traceback.print_exc()
        return []
    except Exception as e:
        print(f"멜로디 패턴 분석 중 알 수 없는 오류 발생 ({midi_filepath}): {e}")
        traceback.print_exc()
        return []

def get_midi_instrument_info(midi_filepath):
    print(f"DEBUG: get_midi_instrument_info 함수 시작. 파일 경로: {midi_filepath}")
    if not os.path.exists(midi_filepath):
        print(f"오류: MIDI 파일이 존재하지 않습니다 - {midi_filepath}")
        return []

    identified_instruments = []
    try:
        score = music21.converter.parse(midi_filepath)
        
        for part in score.parts:
            instruments_in_part = part.getElementsByClass(music21.instrument.Instrument)
            if instruments_in_part:
                inst = instruments_in_part[0]
                # instrumentName과 midiProgram을 사용
                identified_instruments.append((inst.instrumentName, inst.midiProgram))
            else:
                # 명시적 Instrument 객체가 없는 경우 Part의 MIDI 채널을 확인
                # Part 객체에 직접 midiChannel 속성이 설정되어 있을 수 있음
                part_midi_channel = getattr(part, 'midiChannel', None)
                
                if part_midi_channel == 10: # MIDI 채널 10은 드럼 트랙
                    identified_instruments.append(('Drum Kit (Channel 10)', 0)) # 드럼은 프로그램 번호가 의미 없음
                else:
                    # 음표가 있는지 확인하여 Unknown Instrument (Pitched) 또는 Empty Part 분류
                    notes = part.flatten().getElementsByClass(music21.note.Note)
                    if notes:
                        identified_instruments.append(('Unknown Instrument (Pitched)', -1))
                    else:
                        identified_instruments.append(('Empty Part', -1))

        # 중복 제거
        identified_instruments = list(set(identified_instruments))
        
        print(f"MIDI 파일 '{os.path.basename(midi_filepath)}'에서 악기 정보 추출: {identified_instruments}")
        return identified_instruments
        
    except music21.midi.base.MidiException as e:
        print(f"music21 MIDI 파싱 오류 ({midi_filepath}) [악기]: {e}")
        traceback.print_exc()
        return []
    except Exception as e:
        print(f"악기 정보 분석 중 알 수 없는 오류 발생 ({midi_filepath}): {e}")
        traceback.print_exc()
        return []


if __name__ == '__main__':
    print("--- 분석 모듈 테스트 시작 ---")
    test_midi_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'example.mid')

    if os.path.exists(test_midi_file_path):
        try:
            os.remove(test_midi_file_path)
            print(f"DEBUG: 기존 파일 '{test_midi_file_path}' 삭제됨.")
        except Exception as e:
            print(f"DEBUG: 기존 파일 삭제 실패 '{test_midi_file_path}': {e}")
            
    print(f"DEBUG: 테스트용 MIDI 파일 생성 시도: {test_midi_file_path}")
    try:
        s = music21.stream.Stream()
        s.insert(0, music21.tempo.MetronomeMark(number=100)) # BPM 100 설정
        
        # 피아노 파트
        piano_part = music21.stream.Part()
        # instrument.Piano() 객체를 삽입하고, midiInstrument 속성도 명시적으로 설정
        piano_part.insert(0, music21.instrument.Piano()) 
        piano_part.midiInstrument = music21.instrument.Piano() # 악기 객체 자체를 할당
        for _ in range(2):
            for pitch_name, ql in [('C4', 1), ('E4', 1), ('G4', 1), ('C5', 1)]:
                piano_part.append(music21.note.Note(pitch_name, quarterLength=ql))
        s.append(piano_part)

        # 바이올린 파트
        violin_part = music21.stream.Part()
        violin_part.insert(0, music21.instrument.Violin()) 
        violin_part.midiInstrument = music21.instrument.Violin() # 악기 객체 자체를 할당
        for _ in range(2):
            for pitch_name, ql in [('G4', 1), ('F4', 1), ('E4', 1), ('D4', 1)]:
                violin_part.append(music21.note.Note(pitch_name, quarterLength=ql))
        s.append(violin_part)

        # 드럼 파트 (타악기)
        drum_part = music21.stream.Part()
        drum_part.insert(0, music21.instrument.Percussion()) 
        # 드럼 파트는 channel 10을 사용함을 명시적으로 알려줌
        drum_part.midiChannel = 10 
        drum_part.partName = 'Drum Track' 

        for _ in range(4): 
            snare_drum_note = music21.note.Note('D2', quarterLength=0.5) 
            snare_drum_note.volume.velocity = 100 
            drum_part.append(snare_drum_note)

            hi_hat_note = music21.note.Note('G2', quarterLength=0.5) 
            hi_hat_note.volume.velocity = 80
            drum_part.append(hi_hat_note)
            
        s.append(drum_part)


        # MIDI 파일로 저장
        s.write('midi', fp=test_midi_file_path)
        
        time.sleep(0.5) 

        print(f"테스트용 music21 더미 MIDI 파일 생성됨: {test_midi_file_path}")
    except Exception as e:
        print(f"테스트용 MIDI 파일 생성 중 오류 발생 (music21): {e}")
        traceback.print_exc()

    print("\n--- BPM 추출 테스트 ---")
    bpm = get_midi_bpm(test_midi_file_path)
    if bpm is not None:
        print(f"추출된 BPM: {bpm}")
    else:
        print("BPM 추출 실패.")

    print("\n--- 키(Key) 및 스케일(Scale) 추출 테스트 ---")
    key_name, scale_type = get_midi_key_and_scale(test_midi_file_path)
    if key_name is not None and scale_type is not None:
        print(f"추출된 키: {key_name}, 스케일: {scale_type}")
    else:
        print("키/스케일 추출 실패.")

    print("\n--- 화음 진행 (Chord Progression) 추출 테스트 ---")
    chord_progression = get_midi_chord_progression(test_midi_file_path)
    if chord_progression:
        print(f"추출된 화음 진행: {', '.join(chord_progression)}")
    else:
        print("화음 진행 추출 실패 또는 화음이 없습니다.")

    print("\n--- 멜로디 패턴 추출 테스트 ---")
    melody_patterns = get_midi_melody_patterns(test_midi_file_path, pattern_length=4, top_n=3)
    if melody_patterns:
        print("추출된 멜로디 패턴 (패턴, 빈도):")
        for pattern, count in melody_patterns:
            print(f"  {pattern} (빈도: {count})")
    else:
        print("멜로디 패턴 추출 실패 또는 패턴이 없습니다.")

    # --- 악기 구성 및 음색 추출 테스트 ---
    print("\n--- 악기 구성 및 음색 추출 테스트 ---")
    instrument_info = get_midi_instrument_info(test_midi_file_path)
    if instrument_info:
        print("추출된 악기 정보 (악기 이름, MIDI 프로그램 번호):")
        for inst_name, midi_id in instrument_info:
            print(f"  {inst_name} (ID: {midi_id})")
    else:
        print("악기 정보 추출 실패 또는 악기가 없습니다.")

    print("\n--- 존재하지 않는 MIDI 파일 테스트 ---")
    bpm_none = get_midi_bpm("non_existent.mid")
    print(f"BPM 결과: {bpm_none}")
    key_none, scale_none = get_midi_key_and_scale("non_existent.mid")
    print(f"키/스케일 결과: {key_none}, {scale_none}")
    chord_none = get_midi_chord_progression("non_existent.mid")
    print(f"화음 진행 결과: {chord_none}")
    melody_none = get_midi_melody_patterns("non_existent.mid")
    print(f"멜로디 패턴 결과: {melody_none}")
    instrument_none = get_midi_instrument_info("non_existent.mid")
    print(f"악기 정보 결과: {instrument_none}")
    print("\n--- 분석 모듈 테스트 종료 ---")