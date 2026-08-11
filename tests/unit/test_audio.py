from __future__ import annotations

import unittest

from dictate.audio import Recorder


class Stream:
    def __init__(self, **kwargs: object) -> None:
        self.kwargs = kwargs
        self.started = False
        self.stopped = False
        self.closed = False

    def start(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.stopped = True

    def close(self) -> None:
        self.closed = True


class AudioTests(unittest.TestCase):
    def test_default_microphone_capture_stays_in_memory(self) -> None:
        streams: list[Stream] = []

        def factory(**kwargs: object) -> Stream:
            stream = Stream(**kwargs)
            streams.append(stream)
            return stream

        recorder = Recorder(stream_factory=factory)
        recorder.start()
        stream = streams[0]
        self.assertTrue(stream.started)
        self.assertEqual(16_000, stream.kwargs["samplerate"])
        self.assertEqual(1, stream.kwargs["channels"])
        self.assertEqual("int16", stream.kwargs["dtype"])
        stream.kwargs["callback"](b"pcm", 3, None, None)
        self.assertEqual(b"pcm", recorder.stop())
        self.assertTrue(stream.stopped)
        self.assertTrue(stream.closed)

    def test_discard_closes_live_stream_and_clears_audio(self) -> None:
        streams: list[Stream] = []

        def factory(**kwargs: object) -> Stream:
            stream = Stream(**kwargs)
            streams.append(stream)
            return stream

        recorder = Recorder(stream_factory=factory)
        recorder.start()
        stream = streams[0]
        stream.kwargs["callback"](b"partial", 7, None, None)
        recorder.discard()
        self.assertTrue(stream.stopped)
        self.assertTrue(stream.closed)
        with self.assertRaises(RuntimeError):
            recorder.stop()

    def test_device_status_discards_partial_audio_and_fails_on_stop(self) -> None:
        streams: list[Stream] = []

        def factory(**kwargs: object) -> Stream:
            stream = Stream(**kwargs)
            streams.append(stream)
            return stream

        recorder = Recorder(stream_factory=factory)
        recorder.start()
        stream = streams[0]
        stream.kwargs["callback"](b"partial", 7, None, None)
        stream.kwargs["callback"](b"", 0, None, "device-disconnected")
        with self.assertRaisesRegex(RuntimeError, "device status"):
            recorder.stop()
        self.assertTrue(stream.closed)

    def test_selected_device_is_opened_at_session_start_and_open_failure_leaves_no_recording(self) -> None:
        attempts: list[object] = []

        def unavailable(**kwargs: object) -> Stream:
            attempts.append(kwargs["device"])
            raise RuntimeError("selected device unavailable")

        recorder = Recorder("42", stream_factory=unavailable)
        with self.assertRaisesRegex(RuntimeError, "selected device unavailable"):
            recorder.start()
        self.assertEqual(["42"], attempts)
        with self.assertRaisesRegex(RuntimeError, "not active"):
            recorder.stop()


if __name__ == "__main__":
    unittest.main()

