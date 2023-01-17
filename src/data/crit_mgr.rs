use std::cmp;
use bit_set::BitSet;
use positioned_io::{RandomAccessFile, ReadAt};

const CRIT_CHUNK_SIZE: usize = 4096;

/// Crit Database (crit.db) Manager
pub struct CritMgr {
    /// Critical Cooking Data. 
    /// If bit X is set, it means the recipe with id X has different heart value if crit
    data: BitSet,
    /// If bit X is set, it means the chunk X is loaded into data
    loaded: BitSet
}

impl CritMgr {
    pub fn new() -> Self {
        CritMgr { data: BitSet::new(), loaded: BitSet::new() }
    }

    /// Get critical cooking data from recipe id and base hp of the recipe
    pub fn get_recipe_crit_hp(&mut self, recipe_id: u64, base_hp: u8) -> u8 {
        // If heart already max, no matter if crit or not, it will be max (in fact the crit db will have 0)
        if base_hp == 120 {
            return 120;
        }
        if self.get_recipe_flag(recipe_id) {
            cmp::min(base_hp+12, 120)
        }else{
            base_hp
        }
    }
    fn get_recipe_flag(&mut self, recipe_id: u64) -> bool {
        let recipe_id = recipe_id.try_into().unwrap_or_else(|_| panic!("Recipe id overflow: {}", recipe_id));
        // Which byte the recipe id is in
        let recipe_byte_id = recipe_id / 8;
        // Which chunk the byte is in
        let chunk_id = recipe_byte_id / CRIT_CHUNK_SIZE;

        // Ensure the chunk is loaded
        if !self.loaded.contains(chunk_id) {
            self.load_chunk(chunk_id);
        }

        self.data.contains(recipe_id)

    }
    fn load_chunk(&mut self, chunk_id: usize) {
        let start = chunk_id*CRIT_CHUNK_SIZE;
        let file = RandomAccessFile::open("data/crit.db").unwrap_or_else(|_| panic!("Cannot open crit db"));
        let mut buf = [0; CRIT_CHUNK_SIZE];
        let bytes_read = file.read_at(start as u64, &mut buf).unwrap_or_else(|_| panic!("Error reading crit db"));
        self.loaded.insert(chunk_id);

        for i in 0..bytes_read {
            let data_start = (start+i)*8; 
            let the_byte = buf[i];
            for s in 0..8 {
                if the_byte & (1 << s) != 0 {
                    self.data.insert(data_start+s);
                } 
            }          
        }
    }
}
