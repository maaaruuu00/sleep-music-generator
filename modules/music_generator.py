import music21
import os
import random
import time
from pydub import AudioSegment
from pydub.playback import play # 테스트용 (실제 사용 시에는 필요 없을 수 있음)
import traceback

# music_analyzer.py에서 분석 함수들을 임포트 (만약 직접 사용한다면)
# from midi_analyzer import get_midi_bpm, get_midi_key_and_scale, get_midi_dynamics, get_midi_density

# --- 설정값 ---
TARGET_DURATION_MINUTES = 10
BPM = 100 # 고정 BPM (나중에 분석된 값으로 대체 가능)
KEY_NAME = 'C' # 고정 키 (나중에 분석된 값으로 대체 가능)
SCALE_TYPE = 'major' # 고정 스케일 (나중에 분석된 값으로 대체 가능)

# 다이내믹스 범위 (예시: midi_analyzer에서 추출된 common_velocity_ranges를 기반으로 설정)
# 실제 프로젝트에서는 midi_analyzer.py의 get_midi_dynamics 결과에서 가져올 수 있습니다.
VELOCITY_RANGES = [
    (0, 31),   # ppp-pp
    (32, 63),  # p-mp
    (64, 95),  # mf-f
    (96, 127)  # ff-fff
]
# 각 범위에서 무작위로 벨로시티 선택
def get_random_velocity():
    chosen_range = random.choice(VELOCITY_RANGES)
    return random.randint(chosen_range[0], chosen_range[1])

# --- 음악 생성 함수 ---
def generate_music_and_convert_to_mp3(output_filename="generated_music.mp3"):
    print(f"--- 10분 길이 음악 생성 시작 ---")
    
    output_dir = os.path.dirname(os.path.abspath(__file__)) # 현재 스크립트가 있는 modules 폴더
    midi_output_filepath = os.path.join(output_dir, "generated_music_temp.mid")
    mp3_output_filepath = os.path.join(output_dir, output_filename)

    # 이전 임시 파일 삭제 (만약 있다면)
    if os.path.exists(midi_output_filepath):
        os.remove(midi_output_filepath)
        print(f"DEBUG: 기존 임시 MIDI 파일 '{midi_output_filepath}' 삭제됨.")
    if os.path.exists(mp3_output_filepath):
        os.remove(mp3_output_filepath)
        print(f"DEBUG: 기존 MP3 파일 '{mp3_output_filepath}' 삭제됨.")

    s = music21.stream.Stream()
    s.insert(0, music21.tempo.MetronomeMark(number=BPM))

    # 주요 악기 파트 생성
    piano_part = music21.stream.Part()
    piano_part.insert(0, music21.instrument.Piano())
    violin_part = music21.stream.Part()
    violin_part.insert(0, music21.instrument.Violin())
    drum_part = music21.stream.Part()
    drum_part.insert(0, music21.instrument.Percussion()) # 드럼 채널은 10번이므로 별도 설정 필요 없음 (music21에서 자동 처리)

    # C Major 스케일 정의
    scale = music21.scale.MajorScale(KEY_NAME)

    # 전체 재생 시간 (쿼터 길이) 계산
    total_quarter_length = TARGET_DURATION_MINUTES * BPM # 1분 = BPM 쿼터 길이, 10분 = 10 * BPM
    # 1마디 = 4 쿼터 길이 (4/4박자 기준)
    
    print(f"DEBUG: 목표 재생 시간: {TARGET_DURATION_MINUTES}분, 총 쿼터 길이: {total_quarter_length}")

    current_offset = 0.0
    section_length = 8.0 # 8 쿼터 길이 (2마디) 마다 패턴 변화 시도
    
    # 10분 길이까지 음악 생성
    start_time = time.time()
    while current_offset < total_quarter_length:
        # 피아노 파트 (화음 및 저음 멜로디)
        # 간단한 C-F-G-C 진행 반복 (C Major 스케일 내)
        chord_root_pitches = [
            music21.pitch.Pitch('C4'), # C Major
            music21.pitch.Pitch('F4'), # F Major
            music21.pitch.Pitch('G4'), # G Major
            music21.pitch.Pitch('C4')  # C Major
        ]
        
        for i in range(2): # 각 section_length마다 2번의 코드 진행
            root_pitch = random.choice(chord_root_pitches) # 매번 다른 코드 시작
            chord_pitches = [root_pitch, scale.getTonic().transpose(4), scale.getTonic().transpose(7)] # 근음, 3음, 5음
            
            # 화음 (세 음을 동시에, 긴 길이)
            chord_obj = music21.chord.Chord(chord_pitches)
            chord_obj.quarterLength = section_length / len(chord_root_pitches) / 2 # 2번 코드 진행에 맞춤
            chord_obj.volume.velocity = get_random_velocity()
            piano_part.insert(current_offset + i * chord_obj.quarterLength * 2, chord_obj)

            # 베이스 노트 (간단한 베이스 라인)
            bass_note = music21.note.Note(root_pitch.transpose(-12)) # 한 옥타브 아래
            bass_note.quarterLength = chord_obj.quarterLength
            bass_note.volume.velocity = get_random_velocity()
            piano_part.insert(current_offset + i * chord_obj.quarterLength * 2, bass_note)


        # 바이올린 파트 (주요 멜로디)
        melody_notes_in_section = []
        num_melody_notes = random.randint(int(section_length * 1.5), int(section_length * 2.5)) # 밀도 변화
        melody_offset_in_section = 0.0
        
        while melody_offset_in_section < section_length:
            pitch_choice = random.choice(scale.getPitches(f'{KEY_NAME}4', f'{KEY_NAME}5')) # C4~C5 옥타브 내에서 선택
            note_length = random.choice([0.5, 1.0]) # 8분음표, 4분음표

            n = music21.note.Note(pitch_choice, quarterLength=note_length)
            n.volume.velocity = get_random_velocity()
            melody_notes_in_section.append((n, current_offset + melody_offset_in_section))
            
            melody_offset_in_section += note_length
            
        for note, offset in melody_notes_in_section:
            violin_part.insert(offset, note)


        # 드럼 파트 (간단한 비트)
        # 하이햇 (G2), 스네어 (D2), 베이스 드럼 (C2)
        drum_pattern_length = 4.0 # 4분음표 4개
        drum_offset_in_section = 0.0
        while drum_offset_in_section < section_length:
            # 베이스 드럼 (1, 3박에 강하게)
            if drum_offset_in_section % 4.0 == 0.0:
                bd = music21.note.Note('C2', quarterLength=0.5)
                bd.volume.velocity = random.randint(90, 120) # 강하게
                drum_part.insert(current_offset + drum_offset_in_section, bd)
            
            # 스네어 드럼 (2, 4박에 보통)
            if drum_offset_in_section % 4.0 == 2.0:
                sd = music21.note.Note('D2', quarterLength=0.5)
                sd.volume.velocity = random.randint(60, 90) # 보통
                drum_part.insert(current_offset + drum_offset_in_section, sd)

            # 하이햇 (매 8분음표마다)
            hh = music21.note.Note('G2', quarterLength=0.5)
            hh.volume.velocity = random.randint(40, 70) # 약하게
            drum_part.insert(current_offset + drum_offset_in_section, hh)

            drum_offset_in_section += 0.5 # 8분음표 단위로 진행


        current_offset += section_length # 다음 섹션으로 이동
        
        if int(current_offset) % (BPM * 1) == 0: # 1분마다 진행 상황 출력 (BPM 100 기준 100쿼터 = 1분)
            elapsed_minutes = round(current_offset / BPM, 1)
            print(f"DEBUG: {elapsed_minutes}분 길이 생성 중...")

    s.insert(0, piano_part)
    s.insert(0, violin_part)
    s.insert(0, drum_part)

    print(f"DEBUG: 총 {round(s.duration.quarterLength / BPM, 2)}분 길이의 MIDI 스트림 생성 완료.")

    # --- MIDI 파일 저장 ---
    try:
        s.write('midi', fp=midi_output_filepath)
        print(f"MIDI 파일이 생성되었습니다: {midi_output_filepath}")
    except Exception as e:
        print(f"MIDI 파일 저장 중 오류 발생: {e}")
        traceback.print_exc()
        return None

    # --- MIDI to MP3 변환 ---
    print(f"--- MIDI to MP3 변환 시작 (시간이 다소 소요될 수 있습니다) ---")
    try:
        # music21이 직접 MIDI를 WAV로 렌더링하는 기능 (fluidsynth 필요, 설치가 복잡)
        # 대안: 외부 MIDI 렌더러 사용 (SimpleSynth 등) 또는 사운드폰트 설정
        # music21의 show('midi')는 재생만 하고 파일로 저장하는 기능이 제한적

        # 여기서는 music21로 MIDI 파일 생성 후, pydub로 변환을 시도합니다.
        # pydub는 내부적으로 ffmpeg를 사용하며, midi 파일을 직접 다루지 못하므로
        # midi to wav 렌더링 과정이 필요합니다.
        # 이 부분을 위해선 Fluidsynth와 사운드폰트 설치가 권장됩니다.
        # 하지만 일단은 파일을 만들고, 수동으로 렌더링하거나, music21의 임시 재생 기능을 이용하는 것으로 가정합니다.
        # 또는, "pydub.AudioSegment.from_file(midi_output_filepath)" 를 사용해보고 안되면 수동 렌더링을 안내합니다.

        # 임시 MIDI 파일을 로드하여 변환 시도
        # 주의: pydub는 기본적으로 MIDI 파일을 직접 WAV로 렌더링하는 기능을 내장하고 있지 않습니다.
        # 이를 위해선 Fluidsynth 등의 외부 MIDI 렌더링 도구가 필요합니다.
        # 아래 코드는 일단 pydub로 바로 시도하지만, 실패 시 수동 렌더링 안내가 필요합니다.
        
        # music21을 통해 MIDI 파일을 재생하거나 WAV로 렌더링하는 더 일반적인 방법은
        # music21.midi.realtime.StreamPlayer를 사용하는 것이나, 파일 저장까지는 복잡합니다.
        # 따라서, 여기서는 **생성된 MIDI 파일**을 **수동으로 WAV로 변환**하거나
        # Fluidsynth를 설치하여 Python에서 자동화하는 방안을 고려해야 합니다.

        # 편의상, 일단 MIDI 파일만 생성하고, MP3 변환 부분은 다음 단계에서 자세히 다루겠습니다.
        # 현재 코드에서는 music21로 MIDI를 생성까지만 하고, MP3 변환은 주석 처리합니다.
        # MP3 변환을 자동화하려면 Fluidsynth와 사운드폰트 설치가 필수적입니다.
        
        # **********************************************************************
        # 이 부분은 아직 자동화가 불가능하며, Fluidsynth 설치가 필요합니다.
        # 아래 코드는 Fluidsynth가 설치되어 있고 Path에 추가되었음을 가정합니다.
        # **********************************************************************
        
        # 예시: fluidsynth를 사용하여 MIDI -> WAV 변환 (fluidsynth 설치 후)
        # import subprocess
        # soundfont_path = "path/to/your/soundfont.sf2" # 사운드폰트 경로 설정
        # wav_temp_filepath = os.path.join(output_dir, "generated_music_temp.wav")
        # command = f"fluidsynth -ni {soundfont_path} {midi_output_filepath} -F {wav_temp_filepath} -r 44100"
        # subprocess.run(command, shell=True)
        # print(f"MIDI to WAV 변환 완료: {wav_temp_filepath}")

        # if os.path.exists(wav_temp_filepath):
        #     audio = AudioSegment.from_wav(wav_temp_filepath)
        #     audio.export(mp3_output_filepath, format="mp3", bitrate="192k")
        #     print(f"MP3 파일이 생성되었습니다: {mp3_output_filepath}")
        #     os.remove(wav_temp_filepath) # 임시 WAV 파일 삭제
        # else:
        #     print("경고: WAV 파일이 생성되지 않아 MP3 변환을 건너뛰었습니다. Fluidsynth 설치 및 사운드폰트 확인 필요.")

        print(f"\n참고: MP3 파일 자동 생성을 위해서는 'Fluidsynth' 프로그램과 '.sf2' 사운드폰트 파일 설치가 필요합니다.")
        print(f"생성된 MIDI 파일 ({midi_output_filepath})을 사용하여 수동으로 MP3를 변환하거나,")
        print(f"다음 단계에서 Fluidsynth 설치 및 자동화 방법을 안내해 드릴 수 있습니다.")

    except Exception as e:
        print(f"MP3 변환 중 오류 발생 (Fluidsynth 또는 사운드폰트 문제일 수 있습니다): {e}")
        traceback.print_exc()

    print(f"--- 음악 생성 및 변환 프로세스 완료 ---")

# --- 실행 부분 ---
if __name__ == '__main__':
    # 'modules' 디렉토리에서 실행될 것이므로,
    # 출력 파일은 'Jiobi_music/modules/generated_music.mp3'에 생성됩니다.
    generate_music_and_convert_to_mp3()