from time import sleep
from tqdm import trange, tqdm
from multiprocessing import Pool, RLock, freeze_support

L = list(range(9))

def progresser(n):
    interval = 0.001 / (n + 2)
    total = 5000
    text = "#{}, est. {:<04.2}s".format(n, interval * total)
    for _ in trange(total, desc=text, position=n):
        sleep(interval)

if __name__ == '__main__':
    freeze_support()  # for Windows support
    tqdm.set_lock(RLock())  # for managing output contention
    p = Pool(initializer=tqdm.set_lock, initargs=(tqdm.get_lock(),))
    p.map(progresser, L)

def gen():
    state = 0
    while state < 10:
        yield state, state*state
        state = state + 1

for a,b in gen():
    print(f"{a=}, {b=}")