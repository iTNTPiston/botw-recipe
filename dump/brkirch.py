### Modified by iTNTPiston
# find_recipes.py Version 1.2
# 
# Copyright 2022 brkirch
# 
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
# 
# 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# 
# Changelog:
# Version 1.2 (8/9/22)
# - An updated recipeData.json is required for this version
# - Added key items
# Version 1.1 (8/1/22)
# - An updated recipeData.json is required for this version
# - Updated to detect when crit cook will always apply
# - Added perentage indicator when iterating through combinations for manually specified recipes
# Version 1.0.2 (8/1/22)
# - Fix Dragon Claws not being included with Dragon Parts
# Version 1.0.1 (8/1/22)
# - Minor addition to manual recipe/ingredient entry parsing
# Version 1.0.0 (8/1/22)
# - More changes and enhancements to manual recipe entry parsing
# - Add flags for specifying which materials can or can't be used as ingredients
# Version 1.0.0a (7/30/22)
# - Fix broken algorithm for iterating through combinations for manually specified recipes
# - Further increase flexibility of manual recipe entry; now includes fuzzy matching for material names and the ability to specify entire material food/material categories
# Version 0.9.1 (7/28/22)
# - Minor improvements to manual recipe entry parsing
# Version 0.9 (7/28/22)
# - Significantly increased the flexibility of the manual recipe entry syntax. Using delimiters / | ; : and also " or " between ingredients specifies that any one of the ingredients can be used, and all possible recipes that can be created from the combinations will be tested.
# Version 0.8 (7/27/22)
# - Added a flag for manual recipe entry (any conditions specified will still be accounted for)
# - Fixed more recipe matching bugs
# Version 0.7 (7/27/22)
# - Fixed a recipe matching bug that affects a few recipes

import numpy as np
import json

from adapter import BaseAdapter, bootstrap

######### LEGACY START

# DO NOT TOUCH THIS
def legacy_get_price(NMMR, sellTotal, buyTotal, ingredientCount):
    if ingredientCount > 5:
        ingredientCount = 5
    sellTotal = int(np.float32(sellTotal) * NMMR[ingredientCount - 1])
    if sellTotal % 10 != 0:
        sellTotal += 10
        sellTotal -= (sellTotal % 10)
    if buyTotal < sellTotal:
        sellTotal = buyTotal
    if sellTotal < 3:
        sellTotal = 2
    return sellTotal

# DO NOT TOUCH THIS
def legacy_match_single_recipe(cookData, recipe, recipeTags):
    for checkRecipe in cookData['SingleRecipes']:
        hasMatched = True
        recipeIndexes = set(range(len(recipe)))
        if 'Actors' in checkRecipe and checkRecipe['Actors'] != []:
            hasMatched = False
            for ingredient in checkRecipe['Actors']:
                for recipeIndex in recipeIndexes:
                    if recipe[recipeIndex] == ingredient:
                        ingredientName = recipe[recipeIndex]
                        recipeIndexes = [recipeIndex for recipeIndex in recipeIndexes if not recipe[recipeIndex] == ingredientName]
                        hasMatched = True
                        break
                if hasMatched: break
            if not hasMatched: continue
        if 'Tags' in checkRecipe and checkRecipe['Tags'] != []:
            hasMatched = False
            for tag in checkRecipe['Tags']:
                if tag == []:
                    continue
                else:
                    tag = tag[0]
                for recipeIndex in recipeIndexes:
                    if tag in recipeTags[recipeIndex]:
                        ingredientName = recipe[recipeIndex]
                        recipeIndexes = [recipeIndex for recipeIndex in recipeIndexes if not recipe[recipeIndex] == ingredientName]
                        hasMatched = True
                        break
                if hasMatched: break
            if not hasMatched: continue
        return checkRecipe
    return {"Recipe": "Dubious Food"}

# DO NOT TOUCH THIS
def legacy_match_recipe(cookData, recipe, recipeTags):
    for checkRecipe in cookData['Recipes']:
        hasMatched = True
        recipeIndexes = set(range(len(recipe)))
        if 'Actors' in checkRecipe:
            for ingredientGroup in checkRecipe['Actors']:
                if ingredientGroup == []: continue
                hasMatched = False
                for ingredient in ingredientGroup:
                    for recipeIndex in recipeIndexes:
                        if recipe[recipeIndex] == ingredient:
                            ingredientName = recipe[recipeIndex]
                            recipeIndexes = [recipeIndex for recipeIndex in recipeIndexes if not recipe[recipeIndex] == ingredientName]
                            hasMatched = True
                            break
                    if hasMatched: break
                if not hasMatched: break
            if not hasMatched: continue
        if 'Tags' in checkRecipe:
            for tagsGroup in checkRecipe['Tags']:
                if tagsGroup == []: continue
                hasMatched = False
                for tag in tagsGroup:
                    if tag == []:
                        continue
                    else:
                        tag = tag[0]
                    for recipeIndex in recipeIndexes:
                        if tag in recipeTags[recipeIndex]:
                            ingredientName = recipe[recipeIndex]
                            recipeIndexes = [recipeIndex for recipeIndex in recipeIndexes if not recipe[recipeIndex] == ingredientName]
                            hasMatched = True
                            break
                    if hasMatched: break
                if not hasMatched: break
            if not hasMatched: continue
        return checkRecipe
    return {"Recipe": "Dubious Food"}

######### LEGACY END

HEARTY_VALUES = {
    "Big Hearty Radish":      20,
    "Big Hearty Truffle":     16,
    "Hearty Bass":             8,
    "Hearty Blueshell Snail": 12,
    "Hearty Durian":          16,
    "Hearty Lizard":          16,
    "Hearty Radish":          12,
    "Hearty Salmon":          16,
    "Hearty Truffle":          4
}


def parse_ingredient(ingredient):
    return ingredient.lower()

def parse_recipe(recipe, material_name_map):
    recipeSlots = [parse_ingredient(ingredient.strip()) for ingredient in recipe.split(',')]
    if len(recipeSlots) > 5: raise Exception("Recipes can have at most 5 ingredients")
    
    return [ material_name_map[name] for name in recipeSlots ]

def get_price(NMMR, ingredientIndexes, materialData, count):
    buyTotal, sellTotal = 0, 0
    for ingredientIndex in ingredientIndexes:
        material = materialData[ingredientIndex]
        if "CookLowPrice" in material['Tags']:
            buyTotal += 1
            sellTotal += 1
        else:
            buyTotal += material['BuyingPrice']
            sellTotal += material['SellingPrice']
    return legacy_get_price(NMMR, sellTotal, buyTotal, count) 

def compute_recipe(NMMR, cookData, materialData, ingredientIndexes: list):
    effectType, numUnique, recipe, recipeTags = False, 0, [], []
    # value if normal food, no crit
    base_hp = 0
    # value if dubious food
    dubious_hp = 0
    # value if hearty food
    hearty_hp = 0
    # chance of crit. -1 = guaranteed not crit, 0-99 = rng, 100+ = guaranteed crit
    crit_chance = 0
    # chance of monster extract rng.
    # -1 = not used
    #  0 = has monster extract, rng between lo, mid, hi (regular food)
    #  1 = has monster extract, rng between lo, hi      (fairy tonic)
    monster_extract_mode = -1
    
    # Compute effect, base_hp, and dubious_hp
    for i, materialNameIndex in enumerate(ingredientIndexes):
        material = materialData[materialNameIndex]

        recipe.append(material['Name'])
        if material["Name"] == "Monster Extract":
            monster_extract_mode = 0

        if material['EffectType'] != "None":
            if effectType == False and material['EffectType'] != "None":
                effectType = material['EffectType']
            elif effectType != "None" and effectType != False and material['EffectType'] != effectType:
                effectType = "None"

        dubious_hp += material['HitPointRecover']
        base_hp += material['HitPointRecover'] * 2
        if material['EffectType'] == "LifeMaxUp":
            hearty_hp += HEARTY_VALUES[material["Name"]]
        if ingredientIndexes.index(materialNameIndex) == i:
            base_hp += int(material['BoostHitPointRecover'])
            crit_chance += material['BoostSuccessRate']
            numUnique += 1
        recipeTags.append(material['Tags'])

    base_hp = min(base_hp, 120)
    dubious_hp = max(4, min(dubious_hp, 120))

    #print(base_hp)

    # Match recipe
    if numUnique == 1:
        matched_recipe = legacy_match_single_recipe(cookData, recipe, recipeTags)
    else:
        matched_recipe = legacy_match_recipe(cookData, recipe, recipeTags)

    #print(crit_chance)

    if not effectType:
        effectType = "None"
    
    if matched_recipe['Recipe'] == "Dubious Food" or (matched_recipe["Recipe"] == "Elixir" and effectType == "None"):
        # dubious food handler
        base_hp = dubious_hp            # Use dubious food formula for hp
        price = 2                       # Fix price as 2
        crit_chance = -1                # cannot crit
        monster_extract_mode = -1       # cannot use monster extract rng
        effectType = "None"

    elif matched_recipe["Recipe"] == "Rock-Hard Food":
        # rock hard food handler
        base_hp = 1                     # Fix hp as 1
        price = 2                       # Fix price as 2
        crit_chance = -1                # cannot crit
        monster_extract_mode = -1       # cannot use monster extract rng
        effectType = "None"

    elif matched_recipe['Recipe'] == "Fairy Tonic":
        # fairy tonic handler
                                        # base_hp is unchanged
        price = 2                       # Fix price as 2
                                        # can crit
        if monster_extract_mode == 0:
            monster_extract_mode = 1    # monster extract rng lo or hi
        effectType = "None"

    else:
        # Compute normal recipe price
        price = get_price(NMMR, ingredientIndexes, materialData, len(recipe))
        if effectType == "LifeMaxUp":
            # hearty handler
            base_hp = hearty_hp         # Set base hp as hearty hp
                                        # price unchanged
                                        # can crit
                                        # monster extract mode unchanged
            # all other recipes
                                        # base_hp unchanged
                                        # price unchanged
                                        # can crit
                                        # monster extract mode unchanged

    has_no_effect = effectType == "None"
    is_hearty_food = effectType == "LifeMaxUp"
    crit_hp_coost = 4 if is_hearty_food else 12

    # Recipe Heart Boost
    if 'HB' in matched_recipe: 
        base_hp = min(base_hp+int(matched_recipe['HB']), 120) 
    
    # Compute crit_hp, which is critial success hp under regular conditions
    crit_hp = base_hp
    if crit_chance == -1:
        # guaranteed not crit
        pass

    elif crit_chance < 100:
        # rng crit
        crit_hp = min(base_hp+crit_hp_coost, 120)
    elif crit_chance >= 100:
        # guaranteed crit
        if has_no_effect or is_hearty_food:
            # guaranteed heart crit
            base_hp = min(base_hp+crit_hp_coost, 120)
            crit_hp = base_hp
        else:
            # rng crit
            crit_hp = min(base_hp+crit_hp_coost, 120)

    # Compute low_hp and handle monster extract
    low_hp = base_hp
    if monster_extract_mode == 0:
        # regular monster extract mode, lowest is 1, crit unchanged
        low_hp = 1
    elif monster_extract_mode == 1:
        # either lo or hi
        # set lo to 1
        low_hp = 1
        # set base to crit
        base_hp = crit_hp

    return base_hp, price, crit_hp != base_hp, is_hearty_food, low_hp != base_hp

# returns base_hp, price, crit_flag, hearty_flag, monster_flag
def process_recipe(recipe_data, material_name_map, recipe_str):

    recipeData = recipe_data
    materialData = recipeData[0]
    cookData = recipeData[1]

    NMMR = cookData['System']['NMMR']
    for NMMRIndex in range(len(NMMR)):
        NMMR[NMMRIndex] = np.float32(NMMR[NMMRIndex])

    materialsList = parse_recipe(recipe_str, material_name_map)

    return compute_recipe(NMMR, cookData, materialData, materialsList)

class BrkirchRecipeAdapter(BaseAdapter):
    def __enter__(self):
        super().__enter__()
        with open("recipeData.json", "r", encoding="utf-8") as recipe_file:
            self.recipe_data = json.load(recipe_file)
        # make name map
        material_data = self.recipe_data[0]
        material_name_map = {}
        for i, material in enumerate(material_data):
            material_name_map[material['Name'].lower()] = i
        self.material_name_map = material_name_map
        return self

    def get_data(self, items):
        item_str = ",".join(items)
        return process_recipe(self.recipe_data, self.material_name_map, item_str)

if __name__ == "__main__":
    bootstrap(BrkirchRecipeAdapter)