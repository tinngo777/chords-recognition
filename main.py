import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog, QFrame, QSlider
from PyQt5.QtCore import Qt, QUrl, QTimer
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtGui import QFont, QIcon
from chord_detector import analyze_song
from spectrum_widget import SpectrumWidget


class ChordPlayer(QWidget):
    def __init__(self):
        # Init app 
        super().__init__()
        self.setWindowTitle("Chord Recognition")
        self.resize(900, 600)
        self.setStyleSheet("background-color: #f5e5b4;") 


        # init tempo
        self.tempo_timeline = []
        self.previous_tempo = None
      

        # Layout setup
        main_layout = QVBoxLayout()

        # Title
        self.title_label = QLabel("CHORD RECOGNITION PLAYER")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFont(QFont("Arial", 24, QFont.Bold))
        self.title_label.setStyleSheet("color: #bc4908")
        main_layout.addWidget(self.title_label)

        # 'Load Song' button
        self.load_button = QPushButton("Load Song")
        self.load_button.setFixedWidth(200)
        self.load_button.setFont(QFont("Arial", 12))
        self.load_button.setCursor(Qt.PointingHandCursor)
        self.load_button.setStyleSheet
        ("""
            color: #bc4908;
            margin-left: 20px;
            padding: 5px;
        """)
        main_layout.addWidget(self.load_button, alignment=Qt.AlignLeft)


        # Music player frame
        self.music_player_frame = QFrame()
        self.music_player_frame.setStyleSheet("background-color: #ffffff; border-radius: 10px;")
        music_player_layout = QVBoxLayout(self.music_player_frame)

        # File name label
        self.file_label = QLabel("No song loaded")
        self.file_label.setAlignment(Qt.AlignCenter)
        self.file_label.setFont(QFont("Arial", 12, QFont.Bold))
        music_player_layout.addWidget(self.file_label)

        # Spectrum visualizer
        self.spectrum = SpectrumWidget()
        self.spectrum.setMinimumHeight(200)
        music_player_layout.addWidget(self.spectrum)

        # Timeline for music player
        timeline_layout = QHBoxLayout()

        # Start time
        self.start_time = QLabel("0:00")
        self.start_time.setFont(QFont("Arial", 10))
        self.start_time.setFixedWidth(50)
        self.start_time.setAlignment(Qt.AlignLeft)

        self.timeline = QSlider(Qt.Horizontal)
        self.timeline.setRange(0, 100)
        self.timeline.setStyleSheet
        ("""
            QSlider::groove:horizontal {
                height: 8px;
                background: transparent;   
                border-radius: 4px;
            }
            QSlider::sub-page:horizontal {
                background: #b4ceff;        
                border-radius: 4px;
            }
            QSlider::add-page:horizontal {
                background: #cccccc;        
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: white;
                border: 1px solid #0078d7;
                width: 12px;
                height: 12px;
                margin: -3px 0;
                border-radius: 6px;
            }
        """)
        self.timeline.setCursor(Qt.PointingHandCursor)

        # End time
        self.end_time = QLabel("0:00")
        self.end_time.setFont(QFont("Arial", 10))
        self.end_time.setFixedWidth(50)
        self.end_time.setAlignment(Qt.AlignRight)

        timeline_layout.addWidget(self.start_time)
        timeline_layout.addWidget(self.timeline)
        timeline_layout.addWidget(self.end_time)
        music_player_layout.addLayout(timeline_layout)


        # Play/Pause and Stop buttons
        control_layout = QHBoxLayout()
        control_layout.setAlignment(Qt.AlignCenter)

        self.play_icon = QIcon.fromTheme("media-playback-start")
        self.pause_icon = QIcon.fromTheme("media-playback-pause")
        self.stop_icon = QIcon.fromTheme("media-playback-stop")

        # Customize Play/Pause button
        self.play_button = QPushButton()
        self.play_button.setIcon(self.play_icon)
        self.play_button.setFixedSize(30, 30)
        self.play_button.setStyleSheet
        ("""
            QPushButton 
            {
                background-color: #28a745;   
                border-radius: 10px;
            }
            QPushButton:hover 
            {
                background-color: #34d058;
            }
        """)

        # Customize Stop button
        self.stop_button = QPushButton()
        self.stop_button.setIcon(self.stop_icon)
        self.stop_button.setFixedSize(30, 30)
        self.stop_button.setStyleSheet
        ("""
            QPushButton 
            {
                background-color: #dc3545;   
                border-radius: 10px;
            }
            QPushButton:hover 
            {
                background-color: #ff4d5e;
            }
        """)
        control_layout.addWidget(self.play_button)
        control_layout.addWidget(self.stop_button)
        music_player_layout.addLayout(control_layout)
        main_layout.addWidget(self.music_player_frame)


        # Tempo and chord labels
        self.tempo_label = QLabel("Tempo Detected: -")
        self.current_label = QLabel("Current Chord: -")
        self.next_label = QLabel("Next Chord: -")

        for label in (self.tempo_label, self.current_label, self.next_label):
            label.setFont(QFont("Arial", 12))
            label.setStyleSheet("color: #bc4908")
            main_layout.addWidget(label)

        # Apply layout
        self.setLayout(main_layout)


        # Media player 
        self.player = QMediaPlayer()
        self.player.positionChanged.connect(self.update_timeline)
        self.player.durationChanged.connect(self.set_duration)
        self.timeline.sliderReleased.connect(self.seek_audio)


        # Update chord timer 
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_chord_display)

        # Button action
        self.load_button.clicked.connect(self.load_song)
        self.play_button.clicked.connect(self.toggle_play_pause)
        self.stop_button.clicked.connect(self.stop_audio)

        # Set variables
        self.chords = []
        self.beats = []
        self.file_path = None
        self.duration = 0
        self.current_index = 0
        self.is_playing = False

    
    # Function to load song
    def load_song(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Song", "", "Audio Files (*.mp3 *.wav *.mp4)")
        if not file_path:
            return

        self.file_path = file_path
        filename = os.path.basename(file_path)
        # Split text 
        name_only = os.path.splitext(filename)[0] 
        self.file_label.setText(name_only)
        url = QUrl.fromLocalFile(file_path)
        self.player.setMedia(QMediaContent(url))
        self.spectrum.load_audio(file_path)


        # Analyze song
        chords, beats, tempo, tempo_timeline = analyze_song(file_path)
        self.chords = chords
        self.beats = beats
        self.tempo_timeline = tempo_timeline
        self.tempo_label.setText(f"Tempo Detected: {int(tempo)} BPM")
        self.current_label.setText("Current Chord: -")
        self.next_label.setText("Next Chord: -")
        self.start_time.setText("0:00")
        self.end_time.setText("0:00")
        self.timeline.setValue(0)

    # Toggle between play/pause
    def toggle_play_pause(self):
        if not self.file_path:
            return
        if self.is_playing:
            self.player.pause()
            self.timer.stop()
            self.spectrum.stop()
            self.play_button.setIcon(self.play_icon)
            self.is_playing = False
        else:
            self.player.play()
            self.timer.start(200)
            self.spectrum.start()
            self.play_button.setIcon(self.pause_icon)
            self.is_playing = True

    # Toggle stop button
    def stop_audio(self):
        self.player.stop()
        self.timer.stop()
        self.spectrum.stop()
        self.play_button.setIcon(self.play_icon)
        self.is_playing = False
        self.timeline.setValue(0)
        self.start_time.setText("0:00")

    # Song duration
    def set_duration(self, duration):
        self.duration = duration
        self.timeline.setRange(0, duration)
        total_secs = duration // 1000
        mins, secs = divmod(total_secs, 60)
        self.end_time.setText(f"{mins}:{secs:02d}")


    # Update song elapsed and remaining time
    def update_timeline(self, position):
        if self.duration == 0:
            return

        self.timeline.blockSignals(True)
        self.timeline.setValue(position)
        self.timeline.blockSignals(False)

        # Elapsed time
        elapsed_secs = position // 1000
        elapsed_mins, elapsed_secs = divmod(elapsed_secs, 60)
        self.start_time.setText(f"{elapsed_mins}:{elapsed_secs:02d}")
        self.spectrum.set_position(position / 1000.0)


        # Remaining time
        remaining_ms = self.duration - position
        if remaining_ms < 0:
            remaining_ms = 0
        remaining_secs = remaining_ms // 1000
        remaining_mins, remaining_secs = divmod(remaining_secs, 60)
        self.end_time.setText(f"{remaining_mins}:{remaining_secs:02d}")


    def seek_audio(self):
        if self.duration > 0:
            new_pos = self.timeline.value()
            self.player.setPosition(new_pos)


    # Update chords and tempo
    def update_chord_display(self):
        if not self.chords:
            return

        current_time = self.player.position() / 1000.0

        # Update chords
        while (self.current_index + 1 < len(self.chords)
            and self.chords[self.current_index + 1]["time"] <= current_time):
            self.current_index += 1
        current_chord = self.chords[self.current_index]["chord"]
        next_chord = "-"
        if self.current_index + 1 < len(self.chords):
            next_chord = self.chords[self.current_index + 1]["chord"]
        self.current_label.setText(f"Current Chord: {current_chord}")
        self.next_label.setText(f"Next Chord: {next_chord}")

        # Update tempo
        if self.tempo_timeline:
            for i in range(len(self.tempo_timeline) - 1):
                t1 = self.tempo_timeline[i]["time"]
                t2 = self.tempo_timeline[i + 1]["time"]
                if t1 <= current_time < t2:
                    current_tempo = self.tempo_timeline[i]["tempo"]
                    break
            else:
                current_tempo = self.tempo_timeline[-1]["tempo"]

            if current_tempo != self.previous_tempo:
                self.tempo_label.setText(f"Tempo Detected: {int(current_tempo)} BPM")
                self.previous_tempo = current_tempo




if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChordPlayer()
    window.show()
    sys.exit(app.exec_())
