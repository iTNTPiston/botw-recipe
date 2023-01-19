
import json
import math
import sys
from tqdm import tqdm
from multiprocessing import Pool, RLock
from constants import Num_Parts, Main_Record_Size, Num_Recipe_Per_Part

DATA_DIR = "../data"
BLOCK = 3000
LIMIT = 100

def construct_record(block, i):
    record = 0
    for j in range(Main_Record_Size):
        record = record << 8
        record += block[i+j]
    return record

def analyze_record(record):
    parity_bit = record & 0x800000 >> 23
    crit_flag = (record >> 22) & 1
    hearty_flag = (record >> 21) & 1
    monster_flag = (record >> 20) & 1
    price = (record >> 7) & 0x1FF
    base_hp = (record) & 0x7F
    
    return (parity_bit, base_hp, price, bool(crit_flag), bool(hearty_flag), bool(monster_flag))

def get_diffs_maindb(task):
    alt_dir, idx = task
    file_name_1 = f"{DATA_DIR}/{idx:02}.db"
    file_name_2 = f"{alt_dir}/{idx:02}.db"

    diffs = []

    # https://www.quickprogrammingtips.com/python/how-to-calculate-sha256-hash-of-a-file-in-python.html
    with open(file_name_1, "rb") as f1:
        with open(file_name_2, "rb") as f2:
            for block_idx, (block1, block2) in tqdm(
                enumerate(zip(iter(lambda: f1.read(BLOCK), b""), iter(lambda: f2.read(BLOCK), b""))),
                total=int(math.ceil(Num_Recipe_Per_Part*Main_Record_Size/BLOCK)),
                position=idx,
                desc=str(idx)
                ):
                for i in range(int(BLOCK/Main_Record_Size)):
                    r1 = construct_record(block1, i*Main_Record_Size)
                    r2 = construct_record(block2, i*Main_Record_Size)
                    if r1 != r2:
                        recipe = int(Num_Recipe_Per_Part*idx+block_idx*BLOCK/Main_Record_Size+i)
                        diffs.append((recipe, analyze_record(r1), analyze_record(r2)))
                        if(len(diffs) > 100):
                            return diffs, True
    
    return diffs, False

def run_hash_dump(alt_dir):
    diffs = {}
    jobs = [ (alt_dir, i) for i in range(Num_Parts) ]
    count = 0
    capped = False
    tqdm.set_lock(RLock())  # for managing output contention
    with Pool(initializer=tqdm.set_lock, initargs=(tqdm.get_lock(),)) as p:
        for i, x in enumerate(p.map(get_diffs_maindb, jobs)):
            child_diffs, child_capped = x
            if child_capped:
                capped = True
            diffs[f"{i:02}"] = child_diffs
            count += len(child_diffs)
    with open("diffs.json", "w+", encoding="utf-8") as json_file:
        json.dump(diffs, json_file, indent=2)

    print(f"{count} diffs saved to diffs.json")
    if capped:
        print("Not all data are processed because the limit has been reached")

if __name__ == "__main__":
    run_hash_dump(sys.argv[1])
   