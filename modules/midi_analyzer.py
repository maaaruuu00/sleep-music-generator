import mido
import music21
import os
import traceback
import time
from collections import Counter

# --- BPM 추출 함수 ---
def get_midi_bpm(midi_filepath):
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

# --- 키(Key) 및 스케일(Scale) 추출 함수 ---
def get_midi_key_and_scale(midi_filepath):
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

# --- 화음 진행 (Chord Progression) 추출 함수 ---
def get_midi_chord_progression(midi_filepath):
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

# --- 멜로디 패턴 추출 함수 ---
def get_midi_melody_patterns(midi_filepath, pattern_length=4, top_n=3):
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

# --- 악기 구성 및 음색 추출 함수 ---
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
                identified_instruments.append((inst.instrumentName, inst.midiProgram))
            else:
                part_midi_channel = getattr(part, 'midiChannel', None)

                if part_midi_channel == 10: 
                    identified_instruments.append(('Drum Kit (Channel 10)', 0)) 
                else:
                    notes = part.flatten().getElementsByClass(music21.note.Note)
                    if notes:
                        identified_instruments.append(('Unknown Instrument (Pitched)', -1))
                    else:
                        identified_instruments.append(('Empty Part', -1))

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

# --- 다이내믹스 (Dynamics) 분석 함수 ---
def get_midi_dynamics(midi_filepath):
    print(f"DEBUG: get_midi_dynamics 함수 시작. 파일 경로: {midi_filepath}")
    if not os.path.exists(midi_filepath):
        print(f"오류: MIDI 파일이 존재하지 않습니다 - {midi_filepath}")
        return {}

    all_velocities = []
    try:
        score = music21.converter.parse(midi_filepath)

        for note in score.flatten().getElementsByClass(music21.note.Note):
            if note.volume.velocity is not None:
                all_velocities.append(note.volume.velocity)

        if not all_velocities:
            print(f"경고: MIDI 파일 '{os.path.basename(midi_filepath)}'에서 벨로시티 정보를 찾을 수 없습니다.")
            return {
                'average_velocity': None,
                'min_velocity': None,
                'max_velocity': None,
                'common_velocity_ranges': []
            }

        average_velocity = sum(all_velocities) / len(all_velocities)
        min_velocity = min(all_velocities)
        max_velocity = max(all_velocities)

        velocity_ranges = {
            'ppp-pp (0-31)': 0,
            'p-mp (32-63)': 0,
            'mf-f (64-95)': 0,
            'ff-fff (96-127)': 0
        }
        for vel in all_velocities:
            if 0 <= vel <= 31:
                velocity_ranges['ppp-pp (0-31)'] += 1
            elif 32 <= vel <= 63:
                velocity_ranges['p-mp (32-63)'] += 1
            elif 64 <= vel <= 95:
                velocity_ranges['mf-f (64-95)'] += 1
            elif 96 <= vel <= 127:
                velocity_ranges['ff-fff (96-127)'] += 1

        sorted_ranges = sorted(velocity_ranges.items(), key=lambda item: item[1], reverse=True)
        common_velocity_ranges = [{name: count} for name, count in sorted_ranges if count > 0]


        dynamics_info = {
            'average_velocity': round(average_velocity, 2),
            'min_velocity': min_velocity,
            'max_velocity': max_velocity,
            'common_velocity_ranges': common_velocity_ranges
        }

        print(f"MIDI 파일 '{os.path.basename(midi_filepath)}'에서 다이내믹스 정보 추출: {dynamics_info}")
        return dynamics_info

    except music21.midi.base.MidiException as e:
        print(f"music21 MIDI 파싱 오류 ({midi_filepath}) [다이내믹스]: {e}")
        traceback.print_exc()
        return {}
    except Exception as e:
        print(f"다이내믹스 분석 중 알 수 없는 오류 발생 ({midi_filepath}): {e}")
        traceback.print_exc()
        return {}

# --- 밀도 (Density) 분석 함수 ---
def get_midi_density(midi_filepath, measure_length=4.0):
    print(f"DEBUG: get_midi_density 함수 시작. 파일 경로: {midi_filepath}")
    if not os.path.exists(midi_filepath):
        print(f"오류: MIDI 파일이 존재하지 않습니다 - {midi_filepath}")
        return {}

    try:
        score = music21.converter.parse(midi_filepath)

        all_notes = score.flatten().getElementsByClass(music21.note.Note)
        total_notes = len(all_notes)

        if not all_notes:
            print(f"경고: MIDI 파일 '{os.path.basename(midi_filepath)}'에 음표가 없습니다.")
            return {
                'total_notes': 0,
                'total_quarter_length': 0,
                'average_density_notes_per_quarter': 0,
                'most_dense_segment_density': 0
            }

        total_quarter_length = score.duration.quarterLength
        if total_quarter_length == 0:
            last_note = max(all_notes, key=lambda n: n.offset + n.quarterLength)
            total_quarter_length = last_note.offset + last_note.quarterLength

        average_density_notes_per_quarter = total_notes / total_quarter_length if total_quarter_length > 0 else 0

        segment_notes_counts = {}
        for note in all_notes:
            segment_start = int(note.offset / measure_length) * measure_length
            if segment_start not in segment_notes_counts:
                segment_notes_counts[segment_start] = 0
            segment_notes_counts[segment_start] += 1

        most_dense_segment_density = 0
        if segment_notes_counts:
            most_dense_segment_notes = max(segment_notes_counts.values())
            most_dense_segment_density = most_dense_segment_notes / measure_length 


        density_info = {
            'total_notes': total_notes,
            'total_quarter_length': round(total_quarter_length, 2),
            'average_density_notes_per_quarter': round(average_density_notes_per_quarter, 2),
            'most_dense_segment_density': round(most_dense_segment_density, 2)
        }

        print(f"MIDI 파일 '{os.path.basename(midi_filepath)}'에서 밀도 정보 추출: {density_info}")
        return density_info

    except music21.midi.base.MidiException as e:
        print(f"music21 MIDI 파싱 오류 ({midi_filepath}) [밀도]: {e}")
        traceback.print_exc()
        return {}
    except Exception as e:
        print(f"밀도 분석 중 알 수 없는 오류 발생 ({midi_filepath}): {e}")
        traceback.print_exc()
        return {}


# --- 메인 실행 블록 ---
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

        # 피아노 파트 (다양한 벨로시티 포함)
        piano_part = music21.stream.Part()
        piano_part.insert(0, music21.instrument.Piano()) 
        piano_part.midiInstrument = music21.instrument.Piano()
        for i in range(2):
            # C4 (mf), E4 (p), G4 (f), C5 (fff)
            n_c = music21.note.Note('C4', quarterLength=1)
            n_c.volume.velocity = 80 # mf
            piano_part.append(n_c)

            n_e = music21.note.Note('E4', quarterLength=1)
            n_e.volume.velocity = 50 # p
            piano_part.append(n_e)

            n_g = music21.note.Note('G4', quarterLength=1)
            n_g.volume.velocity = 90 # f
            piano_part.append(n_g)

            n_c5 = music21.note.Note('C5', quarterLength=1)
            n_c5.volume.velocity = 120 # fff
            piano_part.append(n_c5)
        s.append(piano_part)

        # 바이올린 파트 (일관된 벨로시티)
        violin_part = music21.stream.Part()
        violin_part.insert(0, music21.instrument.Violin()) 
        violin_part.midiInstrument = music21.instrument.Violin()
        for _ in range(2):
            for pitch_name, ql in [('G4', 1), ('F4', 1), ('E4', 1), ('D4', 1)]:
                n_v = music21.note.Note(pitch_name, quarterLength=ql)
                n_v.volume.velocity = 70 # mf
                violin_part.append(n_v)
        s.append(violin_part)

        # 드럼 파트 (다양한 벨로시티 포함)
        drum_part = music21.stream.Part()
        drum_part.insert(0, music21.instrument.Percussion()) 
        drum_part.midiChannel = 10 
        drum_part.partName = 'Drum Track' 

        for _ in range(4): 
            snare_drum_note = music21.note.Note('D2', quarterLength=0.5) 
            snare_drum_note.volume.velocity = 100 # 강하게
            drum_part.append(snare_drum_note)

            hi_hat_note = music21.note.Note('G2', quarterLength=0.5) 
            hi_hat_note.volume.velocity = 60 # 보통
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

    print("\n--- 악기 구성 및 음색 추출 테스트 ---")
    instrument_info = get_midi_instrument_info(test_midi_file_path)
    if instrument_info:
        print("추출된 악기 정보 (악기 이름, MIDI 프로그램 번호):")
        for inst_name, midi_id in instrument_info:
            print(f"  {inst_name} (ID: {midi_id})")
    else:
        print("악기 정보 추출 실패 또는 악기가 없습니다.")

    # --- 다이내믹스 분석 테스트 ---
    print("\n--- 다이내믹스 (Dynamics) 분석 테스트 ---")
    dynamics_info = get_midi_dynamics(test_midi_file_path)
    if dynamics_info:
        print(f"추출된 다이내믹스 정보:")
        print(f"  평균 벨로시티: {dynamics_info['average_velocity']}")
        print(f"  최소 벨로시티: {dynamics_info['min_velocity']}")
        print(f"  최대 벨로시티: {dynamics_info['max_velocity']}")
        print(f"  가장 흔한 벨로시티 범위: {dynamics_info['common_velocity_ranges']}")
    else:
        print("다이내믹스 정보 추출 실패.")

    # --- 밀도 분석 테스트 ---
    print("\n--- 밀도 (Density) 분석 테스트 ---")
    density_info = get_midi_density(test_midi_file_path)
    if density_info:
        print(f"추출된 밀도 정보:")
        print(f"  전체 음표 수: {density_info['total_notes']}")
        print(f"  총 쿼터 길이: {density_info['total_quarter_length']}")
        print(f"  평균 밀도 (음표/쿼터): {density_info['average_density_notes_per_quarter']}")
        print(f"  가장 밀집된 구간 밀도: {density_info['most_dense_segment_density']}")
    else:
        print("밀도 정보 추출 실패.")

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
    dynamics_none = get_midi_dynamics("non_existent.mid")
    print(f"다이내믹스 결과: {dynamics_none}")
    density_none = get_midi_density("non_existent.mid")
    print(f"밀도 결과: {density_none}")
    print("\n--- 분석 모듈 테스트 종료 ---")