# sleep_music_generator_gui.py

import sys
import os

# scripts 폴더가 현재 스크립트(sleep_music_generator_gui.py)와 같은 레벨에 있다고 가정
script_dir = os.path.dirname(__file__)
sys.path.append(os.path.join(script_dir, 'scripts'))

import utils
# 이제 utils.py의 함수들을 utils.함수명() 형태로 사용할 수 있습니다.
# 예: timestamp = utils.get_current_timestamp()
#     config_data = utils.load_json('config.json')

# --- 이 아래에 기존 sleep_music_generator_gui.py의 코드를 유지합니다 ---

from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QComboBox, QTextEdit, QFileDialog, QProgressBar
)
from PyQt5.QtCore import Qt
import torch
from audiocraft.models import MusicGen
import torchaudio
import time
import subprocess
import glob

class SleepMusicGenerator(QWidget):
    def __init__(self):
        super().__init__()
        self.model = None  # MusicGen 모델은 프로그램 실행 중 1회만 로딩
        self.init_ui()

        # 기존 init_ui(), select_folder(), log()는 유지

    def init_ui(self):
        main_layout = QVBoxLayout()

        # 1. 프롬프트 입력창
        self.prompt_label = QLabel('GPTS로 생성한 프롬프트를 입력하세요:')
        main_layout.addWidget(self.prompt_label)

        self.prompt_text = QTextEdit()
        main_layout.addWidget(self.prompt_text)

        # 2. 수면 총 시간 선택
        self.duration_label = QLabel('수면 총 시간 선택:')
        main_layout.addWidget(self.duration_label)

        self.duration_combo = QComboBox()
        self.duration_combo.addItems(['7h', '8h', '9h', '10h'])
        main_layout.addWidget(self.duration_combo)

        # 3. 저장 폴더 선택
        folder_layout = QHBoxLayout()
        self.folder_label = QLabel('저장 폴더 경로:')
        folder_layout.addWidget(self.folder_label)

        self.folder_path = QTextEdit()
        self.folder_path.setFixedHeight(30)
        folder_layout.addWidget(self.folder_path)

        self.folder_button = QPushButton('폴더 선택')
        self.folder_button.clicked.connect(self.select_folder)
        folder_layout.addWidget(self.folder_button)

        main_layout.addLayout(folder_layout)

        # 4. 버튼 구역
        button_layout = QHBoxLayout()

        self.generate_button = QPushButton('2분 단위 생성 (WAV)')
        self.generate_button.clicked.connect(self.generate_music)
        button_layout.addWidget(self.generate_button)

        self.convert_button = QPushButton('WAV → MP3 변환')
        self.convert_button.clicked.connect(self.convert_wav_to_mp3)
        button_layout.addWidget(self.convert_button)

        self.concat_stage_button = QPushButton('구간별 이어붙이기')
        self.concat_stage_button.clicked.connect(self.concat_stage_mp3)
        button_layout.addWidget(self.concat_stage_button)

        self.concat_final_button = QPushButton('최종 이어붙이기')
        self.concat_final_button.clicked.connect(self.concat_final_mp3)
        button_layout.addWidget(self.concat_final_button)

        self.make_video_button = QPushButton('MP4 영상 만들기')
        self.make_video_button.clicked.connect(self.make_mp4_video)
        button_layout.addWidget(self.make_video_button)

        main_layout.addLayout(button_layout)

        # 5. 진행 상황 표시
        self.progress_bar = QProgressBar()
        main_layout.addWidget(self.progress_bar)

        # 6. 로그 출력창
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFixedHeight(150)
        main_layout.addWidget(self.log_text)

        self.setLayout(main_layout)
        self.setWindowTitle('수면 음악 생성기 (Sleep Music Generator)')
        self.resize(900, 800)
        self.show()

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "저장 폴더 선택")
        if folder:
            self.folder_path.setText(folder)

    def generate_music(self):
        self.log('2분 단위 WAV 생성 시작합니다...')
        # 1. 프롬프트 받기
        prompt_text = self.prompt_text.toPlainText().strip()
        if not prompt_text:
            self.log('❗ 프롬프트가 입력되지 않았습니다.')
            return

        # 2. 저장 폴더 설정
        folder = self.folder_path.toPlainText().strip()
        if not folder:
            self.log('❗ 저장 폴더를 선택해주세요.')
            return
        if not os.path.exists(folder):
            os.makedirs(folder)

        # 3. 수면 시간 읽기
        duration_hours = int(self.duration_combo.currentText().replace('h', ''))
        total_minutes = duration_hours * 60

        # 4. MusicGen medium 모델 로딩
        if self.model is None:
            self.log('MusicGen medium 모델 로딩 중...')
            self.model = MusicGen.get_pretrained('medium')
            self.model.set_generation_params(duration=120)  # 항상 2분 설정
            self.log('모델 로딩 완료.')

        # 5. Sleep 구간 설계
        segments = []

        # (1) Sleep onset
        segments.append(('SleepOnset', 1))  # 2분짜리 1개

        # (2) NREM 숙면
        nrem_total_minutes = 360  # 6시간 기준 (3x 90분)
        nrem_cycles = nrem_total_minutes // 90  # 90분 x 3회
        for cycle in range(nrem_cycles):
            for _ in range(45):  # 90분 / 2분 = 45개
                segments.append((f'NREM{cycle+1}', 1))

        # (3) REM 구간
        rem_minutes = total_minutes - (15 + nrem_total_minutes)  # 남은 시간 REM 할당
        rem_segments = rem_minutes // 2  # 2분 단위 나누기
        for idx in range(int(rem_segments)):
            segments.append((f'REM{idx+1}', 1))

        self.log(f'총 {len(segments)}개 WAV 파일을 생성합니다...')

        # 6. 실제 생성
        counter = 1
        for section, repeat in segments:
            for _ in range(repeat):
                filename = f"{counter:03d}_{section}.wav"
                filepath = os.path.join(folder, filename)

                self.log(f'[{counter}/{len(segments)}] {filename} 생성 중...')
                wav = self.model.generate([prompt_text])
                torchaudio.save(filepath, wav[0].cpu(), 32000)

                self.progress_bar.setValue(int((counter/len(segments))*100))
                counter += 1

        self.log('✅ 2분 단위 WAV 파일 생성 완료!')
        

    def convert_wav_to_mp3(self):
        self.log('WAV → MP3 변환 시작합니다...')
        folder = self.folder_path.toPlainText().strip()
        if not folder:
            self.log('❗ 저장 폴더를 먼저 선택해주세요.')
            return

        wav_files = [f for f in os.listdir(folder) if f.endswith('.wav')]
        total_files = len(wav_files)

        if total_files == 0:
            self.log('❗ 변환할 WAV 파일이 없습니다.')
            return

        for idx, wav_file in enumerate(wav_files, start=1):
            wav_path = os.path.join(folder, wav_file)
            mp3_filename = os.path.splitext(wav_file)[0] + ".mp3"
            mp3_path = os.path.join(folder, mp3_filename)

            command = [
                'ffmpeg', '-y', '-i', wav_path,
                '-codec:a', 'libmp3lame', '-qscale:a', '2', mp3_path
            ]

            try:
                subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                self.log(f"[{idx}/{total_files}] {mp3_filename} 변환 완료.")
                self.progress_bar.setValue(int((idx/total_files)*100))
            except subprocess.CalledProcessError:
                self.log(f"❗ {wav_file} 변환 실패!")

        self.log('✅ 모든 WAV 파일이 MP3로 변환 완료되었습니다.')
        

    def concat_stage_mp3(self):
        self.log('구간별 이어붙이기 시작합니다...')

        folder = self.folder_path.toPlainText().strip()
        if not folder:
            self.log('❗ 저장 폴더를 먼저 선택해주세요.')
            return

        mp3_files = sorted(glob.glob(os.path.join(folder, '*.mp3')))
        if not mp3_files:
            self.log('❗ 이어붙일 MP3 파일이 없습니다.')
            return

        # 구간별로 묶기
        stages = {}
        for mp3_file in mp3_files:
            filename = os.path.basename(mp3_file)
            parts = filename.split('_')
            if len(parts) >= 2:
                stage = parts[1].split('.')[0]  # SleepOnset, NREM1, REM1 등
                stages.setdefault(stage, []).append(mp3_file)

        total_stages = len(stages)
        self.log(f'총 {total_stages}개 구간을 이어붙입니다.')

        for idx, (stage, files) in enumerate(stages.items(), start=1):
            list_path = os.path.join(folder, f'concat_list_{stage}.txt')
            output_path = os.path.join(folder, f'{stage}_merged.mp3')

            # 리스트 파일 작성
            with open(list_path, 'w', encoding='utf-8') as f:
                for filepath in files:
                    f.write(f"file '{filepath}'\n")

            # ffmpeg로 이어붙이기
            command = [
                'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
                '-i', list_path, '-c', 'copy', output_path
            ]

            try:
                subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                self.log(f"[{idx}/{total_stages}] {stage} 구간 이어붙이기 완료: {output_path}")
            except subprocess.CalledProcessError:
                self.log(f"❗ {stage} 구간 이어붙이기 실패!")

            self.progress_bar.setValue(int((idx/total_stages)*100))

        self.log('✅ 구간별 MP3 이어붙이기 완료!')
        

    def concat_final_mp3(self):
        self.log('최종 전체 이어붙이기 시작합니다...')
        folder = self.folder_path.toPlainText().strip()
        if not folder:
            self.log('❗ 저장 폴더를 먼저 선택해주세요.')
            return

        # 구간별 이어붙인 파일 검색
        merged_files = sorted(glob.glob(os.path.join(folder, '*_merged.mp3')))

        if not merged_files:
            self.log('❗ 이어붙일 *_merged.mp3 파일이 없습니다.')
            return

        # SleepOnset → NREM1 → NREM2 → NREM3 → REM1 순으로 정렬 필요
        priority_order = ['SleepOnset', 'NREM1', 'NREM2', 'NREM3', 'REM1', 'REM2', 'REM3', 'REM4', 'REM5']

        # 실제 파일 순서 정렬
        sorted_files = []
        for stage in priority_order:
            for file in merged_files:
                if stage in file:
                    sorted_files.append(file)

        if not sorted_files:
            self.log('❗ 최종 이어붙일 파일을 찾을 수 없습니다.')
            return

        list_path = os.path.join(folder, 'final_concat_list.txt')
        final_output = os.path.join(folder, 'final_sleep_music.mp3')

        # 리스트 파일 작성
        with open(list_path, 'w', encoding='utf-8') as f:
            for filepath in sorted_files:
                f.write(f"file '{filepath}'\n")

        # ffmpeg로 최종 이어붙이기
        command = [
            'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
            '-i', list_path, '-c', 'copy', final_output
        ]

        try:
            subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            self.log(f'✅ 최종 수면 음악 파일 완성: {final_output}')
            self.progress_bar.setValue(100)
        except subprocess.CalledProcessError:
            self.log(f'❗ 최종 이어붙이기 실패!')
        

    def make_mp4_video(self):
        self.log('MP4 영상 만들기 시작합니다...')

        folder = self.folder_path.toPlainText().strip()
        if not folder:
            self.log('❗ 저장 폴더를 먼저 선택해주세요.')
            return

        audio_path = os.path.join(folder, 'final_sleep_music.mp3')
        if not os.path.exists(audio_path):
            self.log('❗ final_sleep_music.mp3 파일이 없습니다.')
            return

        # 배경 이미지 선택
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        image_path, _ = QFileDialog.getOpenFileName(self, "배경 이미지 선택", "", "Image Files (*.png *.jpg *.jpeg)", options=options)

        if not image_path:
            self.log('❗ 배경 이미지가 선택되지 않았습니다.')
            return

        output_video = os.path.join(folder, 'final_sleep_music_video.mp4')

        command = [
            'ffmpeg', '-y',
            '-loop', '1',
            '-i', image_path,
            '-i', audio_path,
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-pix_fmt', 'yuv420p',
            '-shortest',
            output_video
        ]

        try:
            subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            self.log(f'✅ MP4 영상 생성 완료: {output_video}')
            self.progress_bar.setValue(100)
        except subprocess.CalledProcessError:
            self.log(f'❗ MP4 영상 생성 실패!')
        

    def log(self, message):
        self.log_text.append(f"[LOG] {message}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SleepMusicGenerator()
    sys.exit(app.exec_())
