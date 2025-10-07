import numpy as np
import librosa
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor, QBrush
from PyQt5.QtCore import Qt, QTimer


class SpectrumWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Spectrum visualization init
        self.num_bars = 32
        self.bar_values = [0] * self.num_bars
        self.bar_color = QColor("#c7b4ff")
        self.setStyleSheet("background-color: #2b2b2b; border-radius: 8px;")

        # Timer that trigger color update every 50ms
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_bars)
        self.timer.setInterval(50)

        # Audio data 
        self.energy_frames = None
        self.sr = 22050
        self.frame_hop = 512
        self.current_frame = 0
        self.color_phase = 0.0  

    # Process audio to extract list of amplitude values (how loud it is), so later I can use to
    # set how high each visual bar is
    def load_audio(self, file_path):
        # Load song
        y, sr = librosa.load(file_path, sr=self.sr, mono=True)
        S = np.abs(librosa.stft(y, hop_length=self.frame_hop, n_fft=2048))

        # Take average energy across all frequencies
        self.energy_frames = np.mean(S, axis=0)  
        self.energy_frames = self.energy_frames / np.max(self.energy_frames)
        self.current_frame = 0


    # Animation timer start
    def start(self):
        self.timer.start(50)

    # Animation timer stop
    def stop(self):
        self.timer.stop()
        self.bar_values = [0] * self.num_bars
        self.update()


    # Adjust how high the bar based on the frame's energy (loudness) in the song 
    def set_position(self, position_sec):
        if self.energy_frames is None:
            return

        frame_idx = int((position_sec * self.sr) / self.frame_hop)
        if 0 <= frame_idx < len(self.energy_frames):
            energy = self.energy_frames[frame_idx]
            # Randomize bar heights for better visual
            # I'm not able to make it reflect actual spectral content yet
            self.bar_values = [
                max(10, int(energy * 100 * np.random.uniform(0.6, 1.4)))
                for _ in range(self.num_bars)
            ]
        self.update()

    # Animate color transition
    def update_bars(self):
        # Slowly change hue for dynamic rainbow
        self.color_phase = (self.color_phase + 0.02) % 1.0
        r, g, b = self.hsv_to_rgb(self.color_phase, 0.6, 1.0)
        self.bar_color = QColor(int(r * 255), int(g * 255), int(b * 255))
        self.update()

    # Convert HSV to RGB
    def hsv_to_rgb(self, h, s, v):
        """Convert HSV color to RGB tuple."""
        import colorsys
        return colorsys.hsv_to_rgb(h, s, v)

    
    # Draw bars
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(self.bar_color, Qt.SolidPattern))

        # Determine bar width and spacing 
        width = self.width()
        height = self.height()
        bar_width = width / (self.num_bars * 1.5)
        spacing = bar_width / 2

        # Draw each bar 
        for i, val in enumerate(self.bar_values):
            x = int(i * (bar_width + spacing))
            bar_height = int((val / 100) * height)
            y = int(height - bar_height)
            painter.drawRect(x, y, int(bar_width), bar_height)

        painter.end()
