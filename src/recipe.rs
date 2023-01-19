use std::fs;
use bit_set::BitSet;

pub const NUM_ITEMS: usize = 213;
pub const NUM_INGR: usize = 5;
const EMPTY_STRING: String = String::new();

pub fn is_valid_item(id: usize) -> bool {
    id < NUM_ITEMS
}

pub struct RecipeConverter {
    /// item id map
    ids: [String; NUM_ITEMS],
    /// data[i][m] = m multichoose i
    data: [[u64; NUM_ITEMS+1]; NUM_INGR+1],
}

impl RecipeConverter {
    pub fn new() -> Self {
        // Compute constants
        // bionmial(n, k), k<=NUM_INGR is bino[n][k]
        let mut bino = [[0u64; NUM_INGR+1]; NUM_ITEMS+NUM_INGR];
        let mut data = [[0u64; NUM_ITEMS+1]; NUM_INGR+1];
        for n in 0..NUM_ITEMS+NUM_INGR {
            bino[n][0] = 1;
        }
        for k in 0..NUM_INGR+1 {
            bino[k][k] = 1;
        }
        for n in 1..NUM_ITEMS+NUM_INGR {
            for k in 1..NUM_INGR+1 {
                bino[n][k] = bino[n-1][k-1] + bino[n-1][k];
            }
        }

        // data[i][m] is size of choosing i ingredients from m (m multichoose i)
        // so bino[i+m-1][i]
        for m in 0..NUM_ITEMS+1 {
            data[0][m] = 1;
        }
        for i in 1..NUM_INGR+1 {
            for m in 0..NUM_ITEMS+1 {
                data[i][m] = bino[i+m-1][i];
            }
        }

        let mut ids = [EMPTY_STRING; NUM_ITEMS];

        // Load Item JSON
        let items_data = fs::read_to_string("ids.json").expect("Unable to read ids.json. Make sure it's in the root of the working directory");
        let json: serde_json::Value = serde_json::from_str(&items_data).expect("Error parsing ids.json");
        let mut i: usize = 0;
        while let Some(item_name) = json.get(i.to_string()) {
            ids[i] = String::from(item_name.as_str().expect("Error reading item: item name is not a string"));
            i+=1;
        }

        RecipeConverter {
            ids,
            data,
        }
    }

    /// Get material name
    pub fn get_material_name(&self, material: usize) -> String {
        self.ids[material].to_string()
    }

    /// Convert recipe id to a list of ingredients
    /// Result vector size is at most 5
    pub fn to_materials(&self, recipe_id: u64) -> Vec<String> {
        let items = self.to_material_ids(recipe_id);
        let mut output = vec![];
        for item in items {
            if item == 0 {
                // filter out "<none>"
                continue;
            }
            let item_name = self.ids.get(item).unwrap_or_else(|| panic!("Invalid item id when processing recipe id {}", recipe_id));
            output.push(String::from(item_name));
        }
        output
    }

    /// Convert recipe id to a bit set representing which ingredients are used
    pub fn to_material_set(&self, recipe_id: u64) -> BitSet {
        let mut output = BitSet::new();
        let items = self.to_material_ids(recipe_id);
        for item in items {
            if item == 0 {
                // filter out "<none>"
                continue;
            }
            output.insert(item);
        }
        output
    }

    /// recipe_id is the index into the set of all recipes, in the order of multichoose generation order
    /// This algorithm gets the ingredients in polynomial time compared to number of materials
    pub fn to_material_ids(&self, recipe_id: u64) -> [usize; NUM_INGR] {
        let mut items = [0; NUM_INGR];
        let mut input = recipe_id;
        let mut rest_items = NUM_ITEMS;
        
        let mut good = false;
        for item in 0..NUM_INGR {
            let mut index = 0u64;
            for m in NUM_ITEMS-rest_items+1..NUM_ITEMS+1 {
                if index + self.data[NUM_INGR-1-item][NUM_ITEMS-m+1] > input {
                    items[item] = m-1;
                    good = true;
                    break;
                }
                index += self.data[NUM_INGR-1-item][NUM_ITEMS-m+1];
            }
            if !good {
                break;
            }
            rest_items=NUM_ITEMS-items[item];
            input -= index;
        }
        if !good {
            panic!("Uhhh bad recipe id: {}", recipe_id);
        }

        items
    }

    /// Inverse of to_material_ids
    pub fn to_recipe_id(&self, input_items: &[usize]) -> Result<u64, String> {
        if input_items.len() > NUM_INGR {
            return Err(String::from("Too many ingredients"));
        }
        // copy the inputs and append until 5
        let mut items = [0 as usize; NUM_INGR];
        for i in 0..NUM_INGR {
            if let Some(item_id) = input_items.get(i) {
                items[i] = *item_id;
            }else{
                break;
            }
        }
        items.sort_unstable();
        let mut output = 0u64;
        // reconstruct rest_items to be at the beginning of last iteration
        let mut rest_items = NUM_ITEMS-items[NUM_INGR-2];

        // reverse the iterations
        for item in 0..NUM_INGR {
            // compute index
            let reverse_item = NUM_INGR-1-item;
            let m = items[reverse_item]+1;
            let mut index: u64 = 0;
            for reverse_m in NUM_ITEMS-rest_items+1..m {
                index += self.data[item][NUM_ITEMS-reverse_m+1];
            }
            // add to output (reverse input -= index)
            output += index;
            // recover rest_items to beginning of last iteration
            if reverse_item > 1 {
                rest_items = NUM_ITEMS-items[reverse_item-2];
            }else{
                rest_items = NUM_ITEMS;
            }
               
        }

        Ok(output)
        
    }

    pub fn get_matching_materials(&self, words: &[&str]) -> BitSet {
        let mut output = BitSet::new();
        let words: Vec<String> = words.iter().map(|s| s.to_ascii_lowercase()).collect();
        for i in 0..NUM_ITEMS {
            let name = &self.ids[i].to_ascii_lowercase();
            for word in &words {
                if name.contains(word) {
                    output.insert(i);
                    break;
                }
            }
        }

        output
    }

}
