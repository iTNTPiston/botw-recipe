from math import factorial, ceil

Num_Normal_Ingredients = 149
Num_Cooked_Ingredients = 62

# plus 2 is 1 for "None" and 1 for "Invalid"
Num_Ingredients_Total = Num_Normal_Ingredients + Num_Cooked_Ingredients + 2
Num_Ingredients_Max = 5

def binomial(n, k):
    return int(factorial(n) / (factorial(k) * factorial(n-k)))
# Num_Ingredients_Total multichoose Num_Ingredients_Max
Num_Recipe_Total = binomial(Num_Ingredients_Total+Num_Ingredients_Max-1, Num_Ingredients_Max)

# db layout (each letter is one bit)
# ixhm ____ pppp pppp phhh hhh
# i - parity bit. Total number of 1s in the 3-byte (including parity bit) should be even
# x - crit bit. If set, the recipe has rng heart value
# h - hearty bit. If set, the recipe adds 4 instead of 12 when calculating crit heart
# m - monster extract bit. If set, the recipe might give hp=1
# _ - reserved for future use
# p - (9 bits), lower 9 bits of the price
# h - (7 bits), unsigned (base) heart value

Main_Record_Size = 3

# Split main db into 32 parts
Num_Parts = 32

Num_Recipe_Per_Part = ceil(Num_Recipe_Total / Num_Parts)

Num_Recipe_Last_Part = Num_Recipe_Total - Num_Recipe_Per_Part * (Num_Parts-1)


if __name__ == "__main__":
    print(f"{Num_Normal_Ingredients=}")
    print(f"{Num_Cooked_Ingredients=}")
    print(f"{Num_Ingredients_Total=}")
    print(f"{Num_Ingredients_Max=}")
    print(f"{Num_Recipe_Total=}")
    print(f"{Main_Record_Size=}")
    print(f"{Num_Parts=}")
    print(f"{Num_Recipe_Per_Part=}")
    print(f"{Num_Recipe_Last_Part=}")