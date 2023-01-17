mod crit_mgr;
pub use crit_mgr::CritMgr;

mod query;
pub use query::Query;

pub mod database;
pub mod processing;

pub const RECORD_SIZE: usize = 2;
pub const NUM_RECORD: u64 = 4392741639; // binomial(219+5-1,5)
pub const CHUNK_SIZE: usize = 137273177; // ceil(NUM_RECORD / 32)

/// Type of a record in main db
pub struct RecipeData {
    /// Price/Modifier Flag
    pub price: u16,
    /// Hp recover
    pub hp: u8
}

impl RecipeData {
    pub fn from_bytes(buf: &[u8]) -> Self {
        let data: u16 =  ((buf[0] as u16) << 8) | buf[1] as u16;
        let price = (data >> 7) & 0x1ff;
        let hp = buf[1] & 0x7f;
        RecipeData { price, hp }
    }
}
