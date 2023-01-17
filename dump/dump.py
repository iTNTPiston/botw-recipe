import json
import bitarray
import sys
import signal
import os
from multiprocessing import Pool, RLock, Manager, freeze_support
from find_recipes_simple import process_recipe
from tqdm import tqdm, trange
from constants import Num_Ingredients_Max, Num_Parts, Num_Ingredients_Total, Num_Recipe_Per_Part, Num_Recipe_Last_Part, Main_Record_Size

# This script produces data folder which contains 3 databases:
# main db: This is the database containing the non-crit hp value and price for every recipe
# crit db: This is the database containing if the crit hp of a recipe is different from non-crit hp
# four db: This is the database containing if the crit hp of a recipe is 4 more than the base hp

DATA_DIR = "../data"

def count_one_bit(i):
    if i < 0:
        raise ValueError(f"negative {i=}")
    count = 0
    while i > 0:
        if (i & 1):
            count += 1
        i = i >> 1
    return count

# Adapters should all have get_data(liss_of_items) -> base_hp, price, crit_flag, hearty_flag, monster_flag interface
class AbstractAdapter:
    def cook(self, items):
        base_hp, price, crit_flag, hearty_flag, monster_flag = self.get_data(items)
        assert 0 <= base_hp <= 120
        lower_2_bytes = ((price << 7) + base_hp) & 0xFFFF
        crit_flag = 1 << 22 if crit_flag else 0
        hearty_flag = 1 << 21 if hearty_flag else 0
        monster_flag = 1 << 20 if monster_flag else 0

        lower_23_bits = lower_2_bytes | crit_flag | hearty_flag | monster_flag
        # if lower 23 bits has odd number of 1s, set parity bit to 1
        parity_bit = 1 << 23 if (count_one_bit(lower_23_bits) & 1) else 0
        return parity_bit | lower_23_bits

    def get_data(self, items):
        pass

class BrkirchRecipeAdapter(AbstractAdapter):
    def __init__(self):
        super().__init__()
        with open("recipeData.json", "r", encoding="utf-8") as recipe_file:
            self.recipe_data = json.load(recipe_file)

    def get_data(self, items):
        if not items:
            return 0, 0, False, False, False
        item_str = ",".join(items)
        return process_recipe(self.recipe_data, item_str)

def get_adapter(id):
    if id == "brkirch":
        return BrkirchRecipeAdapter()
    raise ValueError(f"Invalid adapter {id=}")

def array2d(first_order, second_order):
    array = [None] * first_order
    for i in range(first_order):
        array[i] = [0] * second_order
    return array

# given id_data which contains a list of items, it will iterate from start to end as if indices in the multichoose set of the items
class RecipeIterator:
    def __init__(self, id_data, start, end):
        self.current = start
        self.end = end
        self.id_data = id_data
        self.num_items = len(id_data)
        data = array2d(Num_Ingredients_Max+1, self.num_items+1)
        bino = array2d(self.num_items+Num_Ingredients_Max, Num_Ingredients_Max+1)
        # binomial(n, k), k<=NUM_INGR is bino[n][k]

        # Compute binomial with dynamic programming
        for n in range(self.num_items+Num_Ingredients_Max):
            bino[n][0] = 1

        for k in range(Num_Ingredients_Max+1):
            bino[k][k] = 1

        for n in range(1,self.num_items+Num_Ingredients_Max):
            for k in range(1, Num_Ingredients_Max+1):
                bino[n][k] = bino[n-1][k-1] + bino[n-1][k]

        # data[i][m] is size of choosing i ingredients from m, so bino[i+m-1][i]
        for m in range(self.num_items+1):
            data[0][m] = 1

        for i in range(1, Num_Ingredients_Max+1):
            for m in range(self.num_items+1):
                data[i][m] = bino[i+m-1][i]
        
        self.data = data
        self.total = data[Num_Ingredients_Max][self.num_items]
    
    def get_total(self):
        return self.total
        
    def __iter__(self):
        return self
    def __next__(self):
        if self.current >= self.end or self.current >= self.total:
            raise StopIteration
        input = self.current    
        self.current += 1
        
        rest_items = self.num_items
        items = []
        good = False

        for item in range(Num_Ingredients_Max):
            index = 0
            for m in range(self.num_items-rest_items+1, self.num_items+1):
                if index + self.data[Num_Ingredients_Max-1-item][self.num_items-m+1] > input:
                    items.append(m-1)
                    good = True
                    break
                
                index += self.data[Num_Ingredients_Max-1-item][self.num_items-m+1]
            
            if not good:
                break
            
            rest_items=self.num_items-items[item]
            input -= index
        
        if good:
            return [self.id_data[i] for i in items if i != 0]

        else:
            raise StopIteration
        
def run_dump(task):
    adapter_id, part = task
    assert 0 <= part < Num_Parts
    # Load the items
    with open("../ids.json", "r", encoding="utf-8") as ids_file:
        id_data_dict = json.load(ids_file)
    id_data = []
    for k in id_data_dict:
        id_data.append(id_data_dict[k])
    assert len(id_data) == Num_Ingredients_Total

    # Create Adapter

    adapter = get_adapter(adapter_id)

    # Initialize Dumper

    recipes = RecipeIterator(id_data, part*Num_Recipe_Per_Part,(part+1)*Num_Recipe_Per_Part)

    # Set up tqdm for progress reporting

    total = Num_Recipe_Last_Part if part == Num_Parts-1 else Num_Recipe_Per_Part
    desc = f"Part {part:02}"

    try:
        with open(os.path.join(DATA_DIR, f"{part:02}.db"), "wb") as main_db:
            for recipe in tqdm(recipes, total=total, desc=desc, position=part):
                # get recipe from adapter
                main_data = adapter.cook(recipe)
                # write main_db. python io is buffered by default
                main_db.write(bytearray(main_data.to_bytes(Main_Record_Size, "big")))
    except KeyboardInterrupt:
        pass

def run_multi(adapter_id):
    # Check if output exists
    if os.path.exists(DATA_DIR):
        if "-f" not in sys.argv:
            print(f"The data directory ({DATA_DIR}) exists. Rename or it to start dumping")
            sys.exit(1)
        else:
            answer = input(f"The data directory ({DATA_DIR}) exists. Continue [y/n]?")
            if answer != "y":
                sys.exit(1)
    
    os.makedirs(DATA_DIR, exist_ok=True)

    # Define jobs
    def jobs():
        for part in range(Num_Parts):
            yield adapter_id, part

    # Init Pool
    tqdm.set_lock(RLock())  # for managing output contention
    
    try:
        with Pool(initializer=tqdm.set_lock, initargs=(tqdm.get_lock(),)) as p:
            for _ in p.imap_unordered(run_dump, jobs()):
                pass
    except KeyboardInterrupt:
        if os.name == 'nt':
            os.system('cls')
        # for mac and linux(here, os.name is 'posix')
        else:
            os.system('clear')
        print("Interrupted!")
        sys.exit(1)

    print("All Done! Run python3 check.py to verify the dumped data is good")

if __name__ == "__main__":
    freeze_support()
    adapter = "brkirch"
    if len(sys.argv) > 1:
        adapter = sys.argv[1]
    run_multi(adapter)
