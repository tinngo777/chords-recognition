import librosa
import numpy as np


MIN_DURATION = 0.5

CHORD_TEMPLATES = {
    # Major chords
    "C":  [1,0,0,0,1,0,0,1,0,0,0,0],
    "C#": [0,1,0,0,0,1,0,0,1,0,0,0],
    "D":  [0,0,1,0,0,0,1,0,0,1,0,0],
    "D#": [0,0,0,1,0,0,0,1,0,0,1,0],
    "E":  [0,0,0,0,1,0,0,0,1,0,0,1],
    "F":  [1,0,0,0,0,1,0,0,0,1,0,0],
    "F#": [0,1,0,0,0,0,1,0,0,0,1,0],
    "G":  [0,0,1,0,0,0,0,1,0,0,0,1],
    "G#": [1,0,0,1,0,0,0,0,1,0,0,0],
    "A":  [0,1,0,0,1,0,0,0,0,1,0,0],
    "A#": [0,0,1,0,0,1,0,0,0,0,1,0],
    "B":  [0,0,0,1,0,0,1,0,0,0,0,1],
    # Minor chords
    "Cm":  [1,0,0,1,0,0,0,1,0,0,0,0],
    "C#m": [0,1,0,0,1,0,0,0,1,0,0,0],
    "Dm":  [0,0,1,0,0,1,0,0,0,1,0,0],
    "D#m": [0,0,0,1,0,0,1,0,0,0,1,0],
    "Em":  [0,0,0,0,1,0,0,1,0,0,0,1],
    "Fm":  [1,0,0,0,0,1,0,0,1,0,0,0],
    "F#m": [0,1,0,0,0,0,1,0,0,1,0,0],
    "Gm":  [0,0,1,0,0,0,0,1,0,1,0,0],
    "G#m": [0,0,0,1,0,0,0,0,1,0,1,0],
    "Am":  [0,0,0,0,1,0,0,0,0,1,0,1],
    "A#m": [1,0,0,0,0,1,0,0,0,0,1,0],
    "Bm":  [0,1,0,0,0,0,1,0,0,0,0,1],
}






def load_audio(file_path:str, sr: int = 22050):
    # Load audio file, return waveform y and sample rate sr
    y, sr = librosa.load(file_path, sr = sr, mono = True)
    return y, sr


def extract_chroma(y, sr, method:str = "cqt"):
    # Extract chroma features from audio
    # methods include cqt, stft, cens
    # return chroma matrix 12xframes
    if method == "cqt":
        chroma_matrix = librosa.feature.chroma_cqt(y = y, sr = sr)
    elif method == "stft":
        S = np.abs(librosa.stft(y))
        chroma_matrix = librosa.feature.chroma_stft(S = S, sr = sr)
    elif method == "cens":
        chroma_matrix = librosa.feature.chroma_cens(y = y, sr = sr)
    
    return chroma_matrix


def recognize_chords(chroma_matrix, sr, beats, hop_length: int = 512):
    """
    Recognize chords once per beat.
    """
    chord_timeline = []

    # Loop through each beat interval
    for i in range(len(beats) - 1):
        start = beats[i]
        end = beats[i + 1]

        # Convert beats (frames) to chroma frame indices
        start_frame = librosa.time_to_frames(start, sr=sr, hop_length=hop_length)
        end_frame = librosa.time_to_frames(end, sr=sr, hop_length=hop_length)

        # Average chroma over the beat interval
        if end_frame > start_frame:
            avg_chroma = np.mean(chroma_matrix[:, start_frame:end_frame], axis=1)
        else:
            avg_chroma = chroma_matrix[:, start_frame]

        # Find best chord
        best_chord = None
        best_score = -1
        for chord, template in CHORD_TEMPLATES.items():
            score = np.dot(avg_chroma, template)
            if score > best_score:
                best_score = score
                best_chord = chord

        chord_timeline.append({"time": start, "chord": best_chord})

    return chord_timeline


def detect_beats(y, sr):
    # Run beat tracking on audio, return tempo and beat times in array
    tempo, beats = librosa.beat.beat_track(y = y, sr = sr)
    beat_times = librosa.frames_to_time(beats, sr = sr)
    return tempo, beat_times


def analyze_song(file_path:str):
    #Load audio
    y, sr = load_audio(file_path)

    # Extract chroma
    chroma_matrix = extract_chroma(y, sr)

 
    # Beat tracking
    tempo, beats = detect_beats(y, sr)

    chords = recognize_chords(chroma_matrix, sr, beats)

    # Returns chord timeline (list of dicts)
    return chords, beats