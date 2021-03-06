from . animation import BaseAnimation
from .. layout import Strip


class BaseStripAnim(BaseAnimation):

    def __init__(self, layout, start=0, end=-1):
        super().__init__(layout)

        if not isinstance(layout, Strip):
            raise RuntimeError('Must use bibliopixel.layout.Strip with ' +
                               'Strip Animations!')

        self._start = max(start, 0)
        self._end = end
        if self._end < 0 or self._end >= self.layout.numLEDs:
            self._end = self.layout.numLEDs - 1

        self._size = self._end - self._start + 1
