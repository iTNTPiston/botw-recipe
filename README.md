# botw-recipe

**NOTE: Currently the database is inaccurate for hearty and dubious food, therefore the database download is not provided. You can still dump it yourself but you will get an inaccurate db.**


A WMC recipe searcher that is FAST

How fast is it? It takes 10 seconds to search through 4.4 trillion recipes using this program, whereas it took the same computer around half an hour to search through 5 million recipes using the `find_recipes.py` script made by brkirch.

This is possible by pre-computing all possible material combination and put them in a database in a way that is fast to query, and by using a language much faster than python.

## Setup
This section guides you to setup the project

### Tools
Install Rust: https://www.rust-lang.org/tools/install

### Prepare Data
First we need to prepare the database. 

You can either dump the data yourself with the tools provided (Python needed), or download from [here (link will be provided in the future, see NOTE at the top)]() (around 900MB compressed and 9GB decompressed). You will see some `*.db` files in the downloaded zip. Extract the zip and put the `data/` folder with the `*.db` files in it at the root of the repo like below
```
botw-recipe
├───data
│   ├───crit.db
│   ├───main00.db
│   ├───main01.db
│   └───...
├───dump
├───presets
├───src
│   ├───command
│   └───data
...
```

### Dumping Data (Optional)


### Checking Data
Run the check script to verify that your data is good after you either dumped or downloaded it
```
cd dump
python check.py
```
You should see `All is good` in the end.
**NOTE: You will see some error because the database is currently inaccurate**

### Run the Program
Run the following command from the root directory (not `dump`)
```
cargo run --release
```
This will launch the application. 

### Example Workflow
This section will guide you through an example workflow.

**Suppose we want to find a recipe with +120 attack up, zoom, multishot and no quickshot**
1. Run the program, you should see a prompt
    ```
    botw-recipe
    Recipe Database for WMC
    Type ? for help
    [+:][-:][h:0-120][c:off][e:0]>
    ```
    This is what each section means:
    - `[+:]`: what modifiers are included, currently none (will include any modifier)
    - `[-:]`: what modifiers are excluded, currently none
    - `[h:0-120]`: hp value range, currently 0-120, inclusive, which will include all recipes
    - `[c:off]`: rng hp crit indicator. `off` means we will not consider rng hp crit
    - `[e:0]`: material exclusion indicator. Currently no materials are excluded
2. First we want to set the modifier filters. We want:
    - **A**ttack, **Z**oom, **M**ultishot
    - No **Q**uickshot because it makes the bow very slow
    
    Type `modifier+ AZM` and hit enter 
    ```
    [+:][-:][h:0-120][c:off][e:0]> modifier+ AZM
    Search will only include recipes that have all of:
    - Attack Up
    - Multishot
    - Zoom


    [+:AMZ][-:][h:0-120][c:off][e:0]>
    ```

    Then type `modifier- Q` and hit enter
    ```
    [+:AMZ][-:][h:0-120][c:off][e:0]> modifier- Q
    Search will only include recipes that have all of:
    - Attack Up
    - Multishot
    - Zoom
    Search will NOT include recipes that have any of:
    - Quick Shot


    [+:AMZ][-:Q][h:0-120][c:off][e:0]>
    ```
3. Finally we will set the range on hp. You can use `minhp` and `maxhp` to do that
    ```
    [+:AMZ][-:Q][h:0-120][c:off][e:0]> minhp 120
    Search will only include hp >= 120

    [+:AMZ][-:Q][h:120-120][c:off][e:0]>
    ```
4. At any time, you can type `status` to review the current search configuration
    ```
    [+:AMZ][-:Q][h:120-120][c:off][e:0]> status
    Search will only include hp >= 120
    Search will only include hp <= 120
    Search will NOT include rng heart crit
    Search will only include recipes that have all of:
    - Attack Up
    - Multishot
    - Zoom
    Search will NOT include recipes that have any of:
    - Quick Shot

    Search will include recipes with any material

    Use "run <output>" to search based on the configuration and save the results to a file.
    Use "reduce <input> <output>" to filter the result based on excluded materials only.

    [+:AMZ][-:Q][h:120-120][c:off][e:0]>
    ```
5. Now we will run the search and save the result to a file called `all_potential_recipes.bin`. You can select whatever name you want
    ```
    [+:AMZ][-:Q][h:120-120][c:off][e:0]> run all_potential_recipes
    Use Ctrl+C to abort the process
    --> Processing with 32 threads...
    --> Progress: 4392741639/4392741639 (100%). Found 94819 Recipes     
    --> Process finished in 2.0019457s.
    Saving results to all_potential_recipes.bin

    [+:AMZ][-:Q][h:120-120][c:off][e:0]>
    ```
    Depending on your hardward, the time it takes to run the search might vary
6. Now we want to see what materials are in the recipes. However, dumping all 94K recipes and looking through them manually is way too much for a human. With this program, you can combine all recipes and only look at what materials are used, using the `sample ` command

    *Note that only the `run` command uses the modifier/hp configuration we set earlier. The rest of the steps filter through the previous outputs, so it doesn't need to use the modifier/hp configuration.*
    ```
    [+:][-:][h:0-120][c:off][e:0]> sample all_potential_recipes
    Use Ctrl+C to abort the process
    --> Processing with 32 threads...
    --> Progress: 94819/94819 (100%).   
    --> Process finished in 1.0029545s.
    1 = Acorn in 414/94819 recipes (0.43%)
    8 = Apple in 780/94819 recipes (0.82%)
    9 = Armoranth in 717/94819 recipes (0.75%)
    10 = Armored Carp in 1980/94819 recipes (2.08%)
    11 = Armored Porgy in 1980/94819 recipes (2.08%)
    12 = Baked Apple in 568/94819 recipes (0.59%)

    (... only showing part of it here. You will see all materials in the console ...)
    
    209 = Voltfruit in 655/94819 recipes (0.69%)
    210 = Warm Darner in 6/94819 recipes (0%)
    211 = Warm Safflina in 571/94819 recipes (0.6%)
    213 = Wildberry in 779/94819 recipes (0.82%)
    214 = Winterwing Butterfly in 6/94819 recipes (0%)
    218 = Zapshroom in 655/94819 recipes (0.69%)

    [+:][-:][h:0-120][c:off][e:0]>
    ```
7. You can look at the list and exclude the materials you don't want. In this case, we will use a preset file in the `presets` folder called `exclude_for_hundo.txt` to exclude the materials that you don't get in hundo early game
    ```
    [+:][-:][h:0-120][c:off][e:0]> load presets/exclude_for_hundo.txt
    The following materials are now excluded:
    - 2 = Amber
    - 9 = Armoranth
    - 10 = Armored Carp
    - 11 = Armored Porgy
    
    (... only showing part of it here. You will see all materials in the console ...)

    - 211 = Warm Safflina
    - 213 = Wildberry
    - 214 = Winterwing Butterfly
    - 217 = Yellow Lizalfos Tail

    [+:][-:][h:0-120][c:off][e:124]>
    ```
    Note that the prompt now shows `[e:124]` with 124 materials excluded. You can see what they are by typing `status`
8. Now we will use the `reduce` command to process the result with the updated material filter, and save the results to `material_excluded1.bin`
    ```
    [+:][-:][h:0-120][c:off][e:124]> reduce all_potential_recipes material_excluded1 
    Use Ctrl+C to abort the process
    --> Processing with 32 threads...
    --> Progress: 94819/94819 (100%). Found 5751 Recipes   
    --> Process finished in 1.0021299s.
    Saving results to material_excluded1.bin

    [+:][-:][h:0-120][c:off][e:124]>
    ```
    We have reduced the number of recipes from 94K to 5K with those filters
9. Now let's keep reducing the number of recipes. If you have a material in mind, you can use the `inspect` command to find its id
    ```
    [+:][-:][h:0-120][c:off][e:124]> inspect shroom
    32 = Chillshroom     
    44 = Endura Shroom   
    85 = Hylian Shroom   
    95 = Ironshroom      
    132 = Razorshroom    
    162 = Rushroom       
    176 = Silent Shroom  
    182 = Stamella Shroom
    188 = Sunshroom
    197 = Toasty Chillshroom
    198 = Toasty Endura Shroom
    199 = Toasty Hylian Shroom
    200 = Toasty Ironshroom
    201 = Toasty Razorshroom
    202 = Toasty Rushroom
    203 = Toasty Silent Shroom
    204 = Toasty Stamella Shroom
    205 = Toasty Sunshroom
    206 = Toasty Zapshroom
    218 = Zapshroom

    [+:][-:][h:0-120][c:off][e:124]>
    ```
    Let's exclude all shrooms for the purpose of this demo
    ```
    [+:][-:][h:0-120][c:off][e:124]> exclude+ 32 44 85 95 132 162 176 182 188 197 198 199 200 201 202 203 204 205 206 218
    ```
    (Note: if the terminal doesn't let you paste the command, try right click to paste or Ctrl+Shift+V)
10. `reduce` again
    ```
    [+:][-:][h:0-120][c:off][e:143]> reduce material_excluded1 material_excluded2
    Use Ctrl+C to abort the process
    --> Processing with 32 threads...
    --> Progress: 5751/5751 (100%). Found 2969 Recipes   
    --> Process finished in 1.0018299s.
    Saving results to material_excluded2.bin

    [+:][-:][h:0-120][c:off][e:143]> 
    ```
11. There are still 2969 recipes so you can filter again. For the purpose of this demo, we will now dump all the recipes to a yaml (human-readable) file called `output.yaml`
    ```
    [+:][-:][h:0-120][c:off][e:143]> dump material_excluded2 output
    Dumping results from material_excluded2 to output
    Done

    [+:][-:][h:0-120][c:off][e:143]>
    ```
12. Open `output.yaml` with a text editor and you will see the recipes in text form. Here's an example
    ```yaml
    - Recipe:
      - Shard of Farosh's Horn
      - Swift Carrot
      - Toasted Big Hearty Truffle
      - Toasted Big Hearty Truffle
      - Toasted Big Hearty Truffle
      Hp: 120
      HpCrit: 120
      Modifiers:
      - Attack Up
      - Durability Up
      - Critical Hit
      - Long Throw
      - Multishot
      - Zoom
      - Surf Up
    ```
