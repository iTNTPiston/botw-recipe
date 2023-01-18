import hashlib
import json
from multiprocessing import Pool
from constants import Num_Parts

DATA_DIR = "../data"
BLOCK = 4096

def get_hash_maindb(idx):
    file_name = f"{DATA_DIR}/{idx:02}.db"

    sha = hashlib.sha256()
    # https://www.quickprogrammingtips.com/python/how-to-calculate-sha256-hash-of-a-file-in-python.html
    with open(file_name, "rb") as f:
        for byte_block in iter(lambda: f.read(BLOCK), b""):
            sha.update(byte_block)
    
    hash = sha.hexdigest()
    return hash.lower()

def run_hash_dump():
    hashes = {}
    with Pool() as p:
        for i, x in enumerate(p.map(get_hash_maindb, range(Num_Parts))):
            hashes[f"{i:02}"] = x
    with open("hash.json", "w+", encoding="utf-8") as json_file:
        json.dump(hashes, json_file, indent=2)

    print("Hashes saved to hash.json")

if __name__ == "__main__":
    run_hash_dump()
   