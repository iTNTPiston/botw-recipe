const { CookingData } = require("./bundle.js");
const { convert_to_record, to_3_bytes_be } = require("./adapter.js");

const pot = new CookingData();
const itemString = process.argv[2];
const items = itemString.split(",").map(x=>x.trim());
const data = pot.cook_hp(items);

console.log(data);
const record = convert_to_record(data);
console.log(record.toString(16));
console.log(to_3_bytes_be(record).map(x=>x.toString(16)));

