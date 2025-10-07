import librosa
import numpy as np

MIN_DURATION = 0.5

# Chord templates: used for pattern matching
# Note: Some chords are the same (e.g. A# = Bb), I chose to display the more popular one (e.g. Bb)
CHORD_TEMPLATES = {
    # Major
    "C":  [1,0,0,0,1,0,0,1,0,0,0,0],
    "C#": [0,1,0,0,0,1,0,0,1,0,0,0],
    "D":  [0,0,1,0,0,0,1,0,0,1,0,0],
    "Eb": [0,0,0,1,0,0,0,1,0,0,1,0],
    "E":  [0,0,0,0,1,0,0,0,1,0,0,1],
    "F":  [1,0,0,0,0,1,0,0,0,1,0,0],
    "F#": [0,1,0,0,0,0,1,0,0,0,1,0],
    "G":  [0,0,1,0,0,0,0,1,0,0,0,1],
    "G#": [1,0,0,1,0,0,0,0,1,0,0,0],
    "A":  [0,1,0,0,1,0,0,0,0,1,0,0],
    "Bb": [0,0,1,0,0,1,0,0,0,0,1,0],
    "B":  [0,0,0,1,0,0,1,0,0,0,0,1],
    # Minor
    "Cm":  [1,0,0,1,0,0,0,1,0,0,0,0],
    "C#m": [0,1,0,0,1,0,0,0,1,0,0,0],
    "Dm":  [0,0,1,0,0,1,0,0,0,1,0,0],
    "Ebm": [0,0,0,1,0,0,1,0,0,0,1,0],
    "Em":  [0,0,0,0,1,0,0,1,0,0,0,1],
    "Fm":  [1,0,0,0,0,1,0,0,1,0,0,0],
    "F#m": [0,1,0,0,0,0,1,0,0,1,0,0],
    "Gm":  [0,0,1,0,0,0,0,1,0,1,0,0],
    "G#m": [0,0,0,1,0,0,0,0,1,0,1,0],
    "Am":  [0,0,0,0,1,0,0,0,0,1,0,1],
    "Bbm": [1,0,0,0,0,1,0,0,0,0,1,0],
    "Bm":  [0,1,0,0,0,0,1,0,0,0,0,1],
    # sus4
    "Csus4":  [1,0,0,0,0,1,0,1,0,0,0,0],   
    "C#sus4": [0,1,0,0,0,0,1,0,1,0,0,0],   
    "Dsus4":  [0,0,1,0,0,0,0,1,0,1,0,0],   
    "Ebsus4": [0,0,0,1,0,0,0,0,1,0,1,0],   
    "Esus4":  [0,0,0,0,1,0,0,1,0,0,1,0],   
    "Fsus4":  [1,0,0,0,0,1,0,0,0,1,0,0],   
    "F#sus4": [0,1,0,0,0,0,1,0,0,0,1,0],   
    "Gsus4":  [0,0,1,0,0,0,0,1,0,0,0,1],   
    "G#sus4": [1,0,0,1,0,0,0,0,1,0,0,0],   
    "Asus4":  [0,1,0,0,1,0,0,0,0,1,0,0],   
    "Bbsus4": [0,0,1,0,0,1,0,0,0,0,1,0],   
    "Bsus4":  [0,0,0,1,0,0,1,0,0,0,0,1],   
    # 7 
    "C7":  [1,0,0,0,1,0,0,1,0,0,1,0],
    "C#7": [0,1,0,0,0,1,0,0,1,0,0,1],
    "D7":  [0,0,1,0,0,0,1,0,0,1,0,1],
    "Eb7": [1,0,0,1,0,0,0,1,0,0,1,0],
    "E7":  [0,1,0,0,0,1,0,0,0,1,0,1],
    "F7":  [1,0,0,0,1,0,0,0,1,0,1,0],
    "F#7": [0,1,0,0,0,0,1,0,0,1,0,1],
    "G7":  [0,0,1,0,0,0,0,1,0,0,1,0],
    "G#7": [1,0,0,1,0,0,0,0,1,0,0,1],
    "A7":  [0,1,0,0,1,0,0,0,0,1,0,1],
    "Bb7": [1,0,0,0,0,1,0,0,1,0,1,0],
    "B7":  [0,0,1,0,0,0,1,0,0,0,1,0],
}

# Load song
def load_audio(file_path:str, sr: int = 22050):
    y, sr = librosa.load(file_path, sr=sr, mono=True)
    return y, sr


# Extract harmonic (3 methods: cqt, stft, cens)
def extract_chroma(y, sr, method:str = "cqt"):
    if method == "cqt":
        chroma_matrix = librosa.feature.chroma_cqt(y=y, sr=sr)
    elif method == "stft":
        S = np.abs(librosa.stft(y))
        chroma_matrix = librosa.feature.chroma_stft(S=S, sr=sr)
    elif method == "cens":
        chroma_matrix = librosa.feature.chroma_cens(y=y, sr=sr)
    
    # Return 12 x time_frames numpy array
    return chroma_matrix


# Match chroma_matrix above to chord templates
def recognize_chords(chroma_matrix, sr, beats, hop_length: int = 512):
    chord_timeline = []
    for i in range(len(beats) - 1):
        start, end = beats[i], beats[i + 1]
        # Convert timestamps to chroma frames indices
        start_frame = librosa.time_to_frames(start, sr=sr, hop_length=hop_length)
        end_frame = librosa.time_to_frames(end, sr=sr, hop_length=hop_length)

        # Mean chroma energy between beats
        avg_chroma = (np.mean(chroma_matrix[:, start_frame:end_frame], axis=1)
                      if end_frame > start_frame else chroma_matrix[:, start_frame])

        # Look through the CHORD_TEMPLATES to find best match
        best_chord, best_score = None, -1
        for chord, template in CHORD_TEMPLATES.items():
            score = np.dot(avg_chroma, template)
            if score > best_score:
                best_score, best_chord = score, chord

        # Store chord + timestamp
        chord_timeline.append({"time": start, "chord": best_chord})
    return chord_timeline


# Track beat and tempo
def detect_beats(y, sr):
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
    beat_times = librosa.frames_to_time(beats, sr=sr)

    # Calculate local tempo curve (in case song have some part that speed up or slow down)
    hop_length = 512
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length)
    local_tempo = librosa.beat.tempo(onset_envelope=onset_env, sr=sr,
                                     hop_length=hop_length, aggregate=None)
    
    # Convert local tempo frames to timestamp and build timeline 
    times = librosa.times_like(local_tempo, sr=sr, hop_length=hop_length)
    tempo_timeline = [{"time": float(t), "tempo": float(tp)} for t, tp in zip(times, local_tempo)]

    return tempo, beat_times, tempo_timeline


# Full song analysis pipeline
def analyze_song(file_path:str):
    y, sr = load_audio(file_path)
    chroma_matrix = extract_chroma(y, sr)
    tempo, beats, tempo_timeline = detect_beats(y, sr)
    chords = recognize_chords(chroma_matrix, sr, beats)
    return chords, beats, tempo, tempo_timeline
