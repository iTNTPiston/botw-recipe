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

# See README.md for the layout
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
    with open("constants.js", "w+", encoding="utf-8") as constants_file:
        constants_file.write(f"exports.{Num_Normal_Ingredients=};\n")
        constants_file.write(f"exports.{Num_Cooked_Ingredients=};\n")
        constants_file.write(f"exports.{Num_Ingredients_Total=};\n")
        constants_file.write(f"exports.{Num_Ingredients_Max=};\n")
        constants_file.write(f"exports.{Num_Recipe_Total=};\n")
        constants_file.write(f"exports.{Main_Record_Size=};\n")
        constants_file.write(f"exports.{Num_Parts=};\n")
        constants_file.write(f"exports.{Num_Recipe_Per_Part=};\n")
        constants_file.write(f"exports.{Num_Recipe_Last_Part=};\n")