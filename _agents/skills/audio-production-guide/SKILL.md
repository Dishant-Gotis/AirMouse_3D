---
skill_name: Audio Production Guide
description: Produce professional audio with recording techniques, mixing, mastering, and podcast production
category: Creative & Media
version: 1.0.0
---

# Audio Production Guide

## Overview
Professional audio requires technical knowledge and creative taste. Master recording, mixing, and mastering for quality output.

## Recording Setup

### Home Studio Essentials

```
Equipment Checklist:
- Microphone (Neumann U87, Audio-Technica AT2020)
- Preamp (Focusrite Scarlett 2i2)
- Audio interface (minimum 2 in/out)
- Studio monitors (KRK Rokit 5)
- Headphones (Sony MDR-7506)
- Pop filter
- Microphone stand/boom arm
- XLR cables
- Monitor stands
```

### Recording Technique

```python
class RecordingSession:
    def __init__(self, sample_rate=48000, bit_depth=24):
        self.sample_rate = sample_rate
        self.bit_depth = bit_depth

    def get_recommended_levels(self):
        """Recording levels"""
        return {
            'dialogue': -12,  # dB
            'music': -6,
            'sound_effects': -6,
            'headroom': 3  # Leave 3dB headroom
        }

    def setup_recording(self):
        """Optimal recording settings"""
        return {
            'sample_rate': 48000,  # Standard for video
            'bit_depth': 24,       # More detail than 16-bit
            'buffer_size': 128,    # Low latency
            'clipping': 'off'      # Avoid clipping
        }
```

## Mixing Fundamentals

### Mix Bus Signal Flow

```
Input → Preamp → EQ → Compressor → Fader → Pan →
Sends (Reverb/Delay) → Mix Bus → Subgroups → Master

Subgroups:
- Drums
- Bass
- Guitars
- Vocals
- Effects
```

### Mixing Techniques

```python
class MixingSession:
    def __init__(self):
        self.tracks = {}

    def balance_levels(self):
        """Set initial levels"""
        # Start with kick at -6dB
        # Build mix around kick
        pass

    def eq_workflow(self):
        """EQ mixing strategy"""
        return {
            'hi-pass_filter': 'Remove sub-100Hz rumble',
            'presence_peak': 'Add clarity 4-8kHz',
            'de_esser': 'Reduce sibilance 5-7kHz',
            'subtractive_eq': 'Remove problem frequencies first',
            'additive_eq': 'Then add character'
        }

    def compression_settings(self):
        """Compression for different instruments"""
        return {
            'vocals': {'ratio': 4, 'threshold': -20, 'release': 0.5},
            'bass': {'ratio': 4, 'threshold': -15, 'release': 0.3},
            'drums': {'ratio': 8, 'threshold': -12, 'release': 0.1},
            'mix_bus': {'ratio': 1.5, 'threshold': -12, 'release': 1.0}
        }

    def apply_reverb(self):
        """Reverb on send channel"""
        return {
            'type': 'plate',
            'decay': 2.5,
            'pre_delay': 25,
            'mix': 0.25  # 25% wet
        }
```

## Mastering Process

```python
class MasteringChain:
    def __init__(self, sample_rate=48000):
        self.sample_rate = sample_rate
        self.plugins = []

    def get_mastering_chain(self):
        """Professional mastering chain"""
        return [
            {'type': 'limiter', 'threshold': -0.3},  # Catch peaks
            {'type': 'linear_phase_eq'},              # Transparent EQ
            {'type': 'multiband_compressor'},         # Frequency-specific
            {'type': 'limiting', 'threshold': -1.0}, # Final limiting
            {'type': 'metering'}                      # LUFS measurement
        ]

    def measure_loudness(self):
        """Modern loudness standards"""
        return {
            'streaming': -14,  # LUFS
            'broadcast': -23,  # LUFS
            'cinema': -27,     # LUFS
            'classical': -6    # LUFS
        }

    def export_masters(self):
        """Create distribution masters"""
        return {
            'streaming': {'format': 'MP3', 'bitrate': 320},
            'broadcast': {'format': 'WAV', 'bitrate': 16},
            'cd': {'format': 'WAV', 'sample_rate': 44100},
            'video': {'format': 'AAC', 'bitrate': 128}
        }
```

## Podcast Production

```python
class PodcastWorkflow:
    def __init__(self):
        self.episode_data = {}

    def recording_checklist(self):
        """Pre-recording setup"""
        return [
            '✓ Test microphone levels',
            '✓ Record reference tone at -12dB',
            '✓ Set backup recorder',
            '✓ Monitor audio in headphones',
            '✓ Record dry, add EQ in post'
        ]

    def post_production_flow(self):
        """Podcast post-production steps"""
        return [
            'Strip silence',
            'Normalize dialogue to -3dB',
            'Gate background noise',
            'Compress dialogue 2-4:1 ratio',
            'EQ for clarity (reduce low end)',
            'Add intro/outro music',
            'Mix levels to -16 LUFS',
            'Export for distribution'
        ]

    def distribution_platforms(self):
        """Upload to podcast platforms"""
        platforms = [
            'Spotify',
            'Apple Podcasts',
            'Google Podcasts',
            'Anchor',
            'Podbean'
        ]
        return platforms
```

## Production Checklist

- [ ] Calibrate monitoring environment
- [ ] Record levels at -12dB average
- [ ] Use high-quality converters
- [ ] Create detailed edit notes
- [ ] Mix at moderate volume
- [ ] Reference on multiple systems
- [ ] Check frequency balance
- [ ] Measure final loudness
- [ ] Create multiple masters
- [ ] Archive original recordings
