
import hashlib
import sys
import multiprocessing
from os.path import isfile
BLOCK = 4096
HASHES = {
    "00":   "4DDB5EC55BE045D1EE614AD823DE0CD4557A6871181ECA1A642111B809A0C20F",
    "01":   "73a946f4e9252145fc23635bf7d39795a52ae0a7c6a4ffc1cb3a4dee22b7df48",
    "02":   "70306e1547ec56cdbd189cfaa66dccfe3043ad236a9940b69826f65fef4a4e9c",
    "03":   "411244c497b18416e493cfe0c350917a2230acd4664c1deb9e716d7c55bd284c",
    "04":   "e423b05993f84f64e8c34eddcc1060ac7057e7d5358c2deebbc76456015f377b",
    "05":   "38cef3af0a3643b9ba12a570cfa5da2d987b720bbf7ccf27de8e76d56e92b46b",
    "06":   "38cef3af0a3643b9ba12a570cfa5da2d987b720bbf7ccf27de8e76d56e92b46b",
    "07":   "5188783156e06011e64e29af9d000bbe662da55e58f00ee49d12b46c0928df22",
    "08":   "62811c2a5f948e67ac33a32755cb63e289452ae4a67ae03417c583a020c68a7e",
    "09":   "02009b82fdaaeb06eab3aeb3eee74ef9abd98e0b5da0dd40bef6c9e7081beb5e",
    "10":   "f7160497ecf4d21b1e533ecb87d7c873c213b1ac759825493685ec4f0a4921cd",
    "11":   "c632be3f2b983706f9642ba3a3a912e4c43cdf14743efd3782c54cbdab889a47",
    "12":   "9b5cbc8e4bc9d9750ce00f30f2eb5a8e92244fc23042a26098e571435545bd66",
    "13":   "98ba40d864e09ceb4720c4e90df3a5417dff4835b2db16c5d4f5e9a6e0cc1e25",
    "14":   "5f22e5303383e14cac929889db57ccadfc2a0b3450548c3fbaca312c04c3f8cc",
    "15":   "fec03f7b70c0531e958b8cc5a8dccddc3ba6cb0762e7cf2090111f84d494ba9d",
    "16":   "02f6b8cdea08b3634e1cc42d94b737d731542611f06532d7cd20fe1388410fbc",
    "17":   "384e582ea6f11122a2a1b0fd646f4e91ca48d5fe88e28f5832b75effe25ea43a",
    "18":   "43365d71e549c69387a6c210284c1241c5b5630dd0cf5fcb015f5042a53b8159",
    "19":   "50407eb93c9425b670ad3bd21e29a89083f99fdc734c0c5c01fc90dfc74a3fe2",
    "20":   "8153980faa79d25b659f4b5bd010093134ec9d936f28a1d84660ac49714049fa",
    "21":   "4afaee359937f5dc14676c977305dae26c684a2af3ea7215ea18c70ba7e3b6c0",
    "22":   "2b0eaf8e70d2f4fe7799bee72ce8971186c91ce5605c3259db11a591ff0a539f",
    "23":   "7cdd7d446de3d4e9bfb5c83ce386ebbb908ebb252d299309c621b69762582206",
    "24":   "1382e93588e4d3f15231e5557b8b62c6c0d1bd204c24183b6b483111a8893145",
    "25":   "ed05927e193c56f83aceda50a64e795a106c507e02a4b3fe53303877985a93ff",
    "26":   "38896421ac06d30aaa53de217782d309f6559ba4edd3823da970c32dd9ee8a1a",
    "27":   "dae00dc4b24c16c9a405822802f0df9442120b376b7e1d3bd3aaaa269c89966e",
    "28":   "2c9e16334b8f2d5e01e18d18d382f9a389fb2169284aeca320b25ac114870723",
    "29":   "fa0e7d9e110306f981eceae6b06939387e15cf8a7d4d2c62732094f48df7190a",
    "30":   "34458322cf1ee0caa77e34cdc750abcb94ee40a94c5fa842534fe59016a3d7b0",
    "31":   "39efcc45a9dc6e34044b25160639e39d27517a6c62135de888e93b87cce8111c",
}
def verify_record(b):
    # get the hp part
    hp = b[1] & 0x7f
    price = (b[0] << 1) | ((b[1] >> 7) & 1)
    # hp is at most 120
    return hp <= 120 and price >= 2

def verify_hash(file_name, expected, actual):
    expected = expected.lower()
    actual = actual.lower()
    if expected != actual:
        return f"ERROR: {file_name} hash mismatch: {expected=}, {actual=}"
    return None

def verify_maindb(idx):
    idx = f"0{idx}" if idx < 10 else str(idx)
    file_name = f"data/main{idx}.db"

    if not isfile(file_name):
        return f"ERROR: {file_name} is missing"

    sha = hashlib.sha256()
    # https://www.quickprogrammingtips.com/python/how-to-calculate-sha256-hash-of-a-file-in-python.html
    block_idx = 0
    with open(file_name, "rb") as f:
        for byte_block in iter(lambda: f.read(BLOCK), b""):
            for i in range(0, len(byte_block), 2):
                if idx == "00" and block_idx == 0 and i == 0:
                    if byte_block[0] != 0 or byte_block[1] != 0:
                        return f"ERROR: for {file_name}: record at 0 should be 0x0, 0x0"
                elif not verify_record(byte_block[i:i+2]):
                    return f"ERROR: for {file_name}: record at {hex(block_idx*BLOCK+i)} is {hex(byte_block[i])},{hex(byte_block[i+1])}, which is incorrect"
            sha.update(byte_block)
            block_idx+=1
    
    hash = sha.hexdigest()
    hash_result = verify_hash(file_name, HASHES[idx], hash)
    if hash_result:
        return hash_result

    print(f"{file_name}: {hash.lower()}")
    return None
    

    

if __name__ == "__main__":
    print("Checking main db")
    errors = []
    with multiprocessing.Pool() as pool:
        for result in pool.imap_unordered(verify_maindb, range(32)):
            if result:
                errors.append(result)


    print()
    if not errors:
        print("All is good")
    else:
        for error in sorted(errors):
            print(error)
        print("There were errors detected")
