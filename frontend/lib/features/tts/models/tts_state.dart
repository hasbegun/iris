/// TTS playback state
enum TtsPlaybackState {
  stopped,
  playing,
  paused,
}

/// TTS state
class TtsState {
  final TtsPlaybackState playbackState;
  final String? currentText;
  final String? error;
  final double speechRate;
  final double volume;
  final double pitch;
  final int currentWordStart;
  final int currentWordEnd;

  const TtsState({
    this.playbackState = TtsPlaybackState.stopped,
    this.currentText,
    this.error,
    this.speechRate = 0.5,
    this.volume = 1.0,
    this.pitch = 1.0,
    this.currentWordStart = 0,
    this.currentWordEnd = 0,
  });

  TtsState copyWith({
    TtsPlaybackState? playbackState,
    String? currentText,
    String? error,
    double? speechRate,
    double? volume,
    double? pitch,
    int? currentWordStart,
    int? currentWordEnd,
    bool clearCurrentText = false,
    bool clearError = false,
  }) {
    return TtsState(
      playbackState: playbackState ?? this.playbackState,
      currentText: clearCurrentText ? null : (currentText ?? this.currentText),
      error: clearError ? null : (error ?? this.error),
      speechRate: speechRate ?? this.speechRate,
      volume: volume ?? this.volume,
      pitch: pitch ?? this.pitch,
      currentWordStart: currentWordStart ?? this.currentWordStart,
      currentWordEnd: currentWordEnd ?? this.currentWordEnd,
    );
  }

  bool get isPlaying => playbackState == TtsPlaybackState.playing;
  bool get isPaused => playbackState == TtsPlaybackState.paused;
  bool get isStopped => playbackState == TtsPlaybackState.stopped;
}
