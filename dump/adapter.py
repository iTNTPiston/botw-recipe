import sys

def count_one_bit(i):
    if i < 0:
        raise ValueError(f"negative {i=}")
    count = 0
    while i > 0:
        if (i & 1):
            count += 1
        i = i >> 1
    return count

class BaseAdapter:
    def cook(self, items):
        if not items:
            return 0
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
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_value, tracback):
        pass

def bootstrap(adapter_class):
    items = [x.strip() for x in sys.argv[1].split(",")]
    with adapter_class() as adapter:
        print(adapter.get_data(items))
        print(hex(adapter.cook(items)))
