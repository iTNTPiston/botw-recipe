use std::fs::File;
use std::io::BufReader;
use positioned_io::RandomAccessFile;

use super::RecipeData;
use super::{CHUNK_SIZE, RECORD_SIZE};

use crate::sys;

struct Chunk {
    path: String,
    file: RandomAccessFile
}

impl Chunk {
    fn get_record_at(&self, offset: u64) -> Result<RecipeData, String> {
        let mut buf = [0; 2];
        let read_size = sys::read_random_access_file(&self.path, &self.file, offset, &mut buf)?;
        if read_size != RECORD_SIZE {
            return Err(format!("error reading db: unexpected record size {}", read_size));
        }
    
        Ok(RecipeData::from_bytes(&buf))
    }
}

/// Get recipe data (hp and price) by id
pub fn get_recipe_by_id(recipe_id: u64) -> Result<RecipeData, String> {
    let chunk_id = sys::to_usize(recipe_id / CHUNK_SIZE as u64);
    let record_offset = (recipe_id % CHUNK_SIZE as u64) * RECORD_SIZE as u64;
    get_chunk(chunk_id)?.get_record_at(record_offset)
}

fn get_chunk(chunk_id: usize) -> Result<Chunk, String> {
    let path = get_chunk_filename(chunk_id);
    let file = sys::open_random_access_file(&path)?;
    Ok(Chunk { path, file })
}

/// Open a chunk for sequential reading
pub fn get_chunk_seq(chunk_id: usize) -> Result<BufReader<File>, String> {
    let path = get_chunk_filename(chunk_id);
    sys::open_file_rbuf(&path)
}

fn get_chunk_filename(chunk_id: usize) -> String {
    if chunk_id < 10 {
        format!("data/main0{}.db", chunk_id)
    } else {
        format!("data/main{}.db", chunk_id)
    }
}
