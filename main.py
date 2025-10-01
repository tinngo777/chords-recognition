import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog
)
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl, QTimer

from chord_detector import analyze_song   # backend functions


class ChordPlayer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chord Recognition Player")
        self.setGeometry(200, 200, 400, 200)

        # --- UI Layout ---
        layout = QVBoxLayout()

        # File load button
        self.load_button = QPushButton("Load Song")
        layout.addWidget(self.load_button)

        # Audio controls
        self.play_button = QPushButton("Play")
        self.stop_button = QPushButton("Stop")
        layout.addWidget(self.play_button)
        layout.addWidget(self.stop_button)

        # Chord labels
        self.current_label = QLabel("Current Chord: -")
        self.next_label = QLabel("Next Chord: -")
        layout.addWidget(self.current_label)
        layout.addWidget(self.next_label)

        self.setLayout(layout)

        # --- Media Player ---
        self.player = QMediaPlayer()

        # --- Timer to sync chords ---
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_chord_display)

        # --- Signals ---
        self.load_button.clicked.connect(self.load_song)
        self.play_button.clicked.connect(self.play_audio)
        self.stop_button.clicked.connect(self.stop_audio)

        # --- Data ---
        self.chords = []        # chord timeline
        self.beats = []         # beat times
        self.current_index = 0

    def load_song(self):
        """Open file dialog, load audio, run chord analysis."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Song", "", "Audio Files (*.mp3 *.wav)"
        )
        if file_path:
            # Load into QMediaPlayer
            url = QUrl.fromLocalFile(file_path)
            self.player.setMedia(QMediaContent(url))

            # Run chord analysis
            self.chords, self.beats = analyze_song(file_path)
            self.current_index = 0

            # Reset labels
            self.current_label.setText("Current Chord: -")
            self.next_label.setText("Next Chord: -")

    def play_audio(self):
        """Start playback and chord updates."""
        if self.player.mediaStatus() == QMediaPlayer.NoMedia:
            return
        self.player.play()
        self.timer.start(200)  # check chords every 200 ms

    def stop_audio(self):
        """Stop playback and timer."""
        self.player.stop()
        self.timer.stop()

    def update_chord_display(self):
        """Check current playback time and update chord labels."""
        if not self.chords:
            return

        current_time = self.player.position() / 1000.0  # ms → seconds

        # Move index forward if we passed the next chord time
        while (self.current_index + 1 < len(self.chords) and
               self.chords[self.current_index + 1]["time"] <= current_time):
            self.current_index += 1

        current_chord = self.chords[self.current_index]["chord"]

        # Next chord info
        next_chord = "-"
        beat_countdown = ""
        if self.current_index + 1 < len(self.chords):
            next_chord_time = self.chords[self.current_index + 1]["time"]
            next_chord = self.chords[self.current_index + 1]["chord"]

            # Count how many beats fall between now and the next chord
            beats_to_next = [
                b for b in self.beats if current_time < b <= next_chord_time
            ]
            beat_countdown = f" (in {len(beats_to_next)} beats)" if beats_to_next else ""

        # Update labels
        self.current_label.setText(f"Current Chord: {current_chord}")
        self.next_label.setText(f"Next Chord: {next_chord}{beat_countdown}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChordPlayer()
    window.show()
    sys.exit(app.exec_())
