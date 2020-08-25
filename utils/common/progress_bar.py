class progress_bar():

    def __init__(self, total):
        super().__init__()
        self._arrow = 50
        self.total = total

    def show(self, current_set):
        a = int((current_set / self.total) * self._arrow)
        b = self._arrow - a
        text = "\r|{}{}| {:>3s}% ({:>} of {:>})".format(
            '#' * a,
            ' ' * b,
            str(int((current_set / self.total) * 100)),
            str(current_set),
            str(self.total)
        )

        print(text, end='')
        if a == self._arrow:
            print('')


if __name__ == '__main__':
    import time
    length = 50
    process_bar = progress_bar(length)

    for i in range(1, length+1):
        process_bar.show(i)
        time.sleep(0.05)
