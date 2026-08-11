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


if __name__ == "__main__":
    unittest.main()

