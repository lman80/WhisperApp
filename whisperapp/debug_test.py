#!/usr/bin/env python3
"""
WhisperApp Debug Test Script
Run this to verify each component works independently.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def print_header(title):
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}\n")

def test_imports():
    """Test that all modules can be imported."""
    print_header("1. Testing Imports")
    
    try:
        from whisperapp import transcribe, cleanup, recorder, hotkey, database
        print("✅ All whisperapp modules import successfully")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_database():
    """Test database operations."""
    print_header("2. Testing Database")
    
    try:
        import tempfile
        from whisperapp.database import Database
        
        db_path = tempfile.mktemp(suffix='.db')
        db = Database(db_path)
        
        # Test save
        record_id = db.save_transcription("Test transcription", duration=5.0)
        print(f"✅ Saved transcription with ID: {record_id}")
        
        # Test retrieve
        transcriptions = db.get_transcriptions(limit=10)
        print(f"✅ Retrieved {len(transcriptions)} transcription(s)")
        
        # Test stats
        stats = db.get_statistics()
        print(f"✅ Statistics: {stats}")
        
        # Cleanup
        os.remove(db_path)
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_audio_devices():
    """Test audio device enumeration."""
    print_header("3. Testing Audio Devices")
    
    try:
        from whisperapp.recorder import list_audio_devices
        
        devices = list_audio_devices()
        print(f"Found {len(devices)} input device(s):")
        for d in devices:
            print(f"  - [{d['index']}] {d['name']} ({d['channels']} ch, {d['sample_rate']} Hz)")
        
        if not devices:
            print("⚠️  No input devices found!")
            return False
        return True
    except Exception as e:
        print(f"❌ Audio device test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_recording():
    """Test audio recording (2 second test)."""
    print_header("4. Testing Audio Recording (2 seconds)")
    
    try:
        from whisperapp.recorder import AudioRecorder
        import time
        
        print("🎤 Recording for 2 seconds... (speak now!)")
        recorder = AudioRecorder()
        recorder.start()
        time.sleep(2)
        wav_path = recorder.stop()
        
        print(f"✅ Recorded to: {wav_path}")
        print(f"✅ Duration: {recorder.last_duration:.2f}s")
        
        # Check file size
        size = os.path.getsize(wav_path)
        print(f"✅ File size: {size} bytes")
        
        if size < 1000:
            print("⚠️  Warning: File seems too small, audio may not have recorded")
        
        return wav_path
    except Exception as e:
        print(f"❌ Recording test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_transcription(wav_path=None):
    """Test transcription."""
    print_header("5. Testing Transcription")
    
    if not wav_path:
        print("⚠️  Skipping (no audio file)")
        return False
    
    try:
        from whisperapp.transcribe import transcribe_with_timing
        
        print(f"🔄 Transcribing {wav_path}...")
        print("   (First run downloads model ~600MB, please wait...)")
        
        result = transcribe_with_timing(wav_path)
        
        print(f"✅ Transcription: \"{result['text']}\"")
        print(f"✅ Time: {result['transcription_time']:.2f}s")
        print(f"✅ Words: {result['word_count']}")
        
        return result['text']
    except Exception as e:
        print(f"❌ Transcription test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_cleanup(text=None):
    """Test filler word cleanup."""
    print_header("6. Testing Filler Cleanup")
    
    test_text = text or "Um, I was like, you know, basically going to the store."
    
    try:
        from whisperapp.cleanup import clean_with_regex, clean_with_llm
        
        # Test regex (fast)
        regex_result = clean_with_regex(test_text)
        print(f"📝 Input:  \"{test_text}\"")
        print(f"✅ Regex:  \"{regex_result}\"")
        
        # Test LLM (slower, requires model download)
        print("\n🔄 Testing LLM cleanup (downloads ~2GB model on first run)...")
        try:
            llm_result = clean_with_llm(test_text)
            print(f"✅ LLM:    \"{llm_result}\"")
        except Exception as e:
            print(f"⚠️  LLM cleanup not available: {e}")
        
        return True
    except Exception as e:
        print(f"❌ Cleanup test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_hotkey():
    """Test hotkey detection (5 second test)."""
    print_header("7. Testing Hotkey Detection (5 seconds)")
    
    try:
        from whisperapp.hotkey import HotkeyManager
        from pynput.keyboard import Key
        import time
        
        events = []
        
        def on_start():
            events.append('START')
            print("  ▶️ Key PRESSED - would start recording")
        
        def on_stop():
            events.append('STOP')
            print("  ⏹️ Key RELEASED - would stop recording")
        
        print("⌨️  Press and release RIGHT COMMAND key within 5 seconds...")
        print("   (If this hangs, you need to grant Accessibility permissions)")
        
        manager = HotkeyManager(
            trigger_key=Key.cmd_r,
            on_start=on_start,
            on_stop=on_stop
        )
        manager.start_listening_async()
        
        time.sleep(5)
        manager.stop_listening()
        
        if events:
            print(f"✅ Detected {len(events)} event(s): {events}")
            return True
        else:
            print("⚠️  No hotkey events detected")
            print("   Make sure you granted Accessibility permissions:")
            print("   System Settings → Privacy & Security → Accessibility")
            return False
            
    except Exception as e:
        print(f"❌ Hotkey test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_text_injection():
    """Test text injection via clipboard."""
    print_header("8. Testing Text Injection")
    
    try:
        from whisperapp.hotkey import HotkeyManager
        import pyperclip
        
        test_text = "[WhisperApp Test] Hello World!"
        
        manager = HotkeyManager()
        
        print(f"📋 Will copy to clipboard: \"{test_text}\"")
        print("⚠️  Note: This will paste into the focused app!")
        print("   (skipping actual paste to avoid unwanted input)")
        
        # Just test clipboard
        old = pyperclip.paste()
        pyperclip.copy(test_text)
        new = pyperclip.paste()
        pyperclip.copy(old)  # Restore
        
        if new == test_text:
            print(f"✅ Clipboard works correctly")
            return True
        else:
            print(f"❌ Clipboard mismatch: expected '{test_text}', got '{new}'")
            return False
            
    except Exception as e:
        print(f"❌ Text injection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "="*60)
    print(" WhisperApp Debug Test Suite")
    print("="*60)
    
    results = {}
    
    # Run tests
    results['imports'] = test_imports()
    if not results['imports']:
        print("\n❌ Imports failed, cannot continue")
        return
    
    results['database'] = test_database()
    results['audio_devices'] = test_audio_devices()
    results['clipboard'] = test_text_injection()
    
    # Interactive tests
    print("\n" + "-"*60)
    response = input("Run audio recording test? (y/n): ").strip().lower()
    if response == 'y':
        wav_path = test_recording()
        if wav_path:
            results['recording'] = True
            
            response = input("\nRun transcription test? (y/n): ").strip().lower()
            if response == 'y':
                text = test_transcription(wav_path)
                results['transcription'] = bool(text)
    
    response = input("\nRun filler cleanup test? (y/n): ").strip().lower()
    if response == 'y':
        results['cleanup'] = test_cleanup()
    
    response = input("\nRun hotkey test? (y/n): ").strip().lower()
    if response == 'y':
        results['hotkey'] = test_hotkey()
    
    # Summary
    print_header("Test Summary")
    for test, passed in results.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {test}")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"\n  Passed: {passed}/{total}")

if __name__ == "__main__":
    main()
