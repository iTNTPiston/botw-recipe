const { CookingData } = require("./bundle.js");
const { convert_to_record, to_3_bytes_be } = require("./adapter.js");

const pot = new CookingData();
const run = (itemString) => {
    console.log(`Running ${itemString}`)
    const items = itemString.split(",").map(x=>x.trim());
    const data = pot.cook_hp(items);

    console.log(data);
    const record = convert_to_record(data);
    console.log(record.toString(16));
}

for (let i=2;i<process.argv.length;i++){
    const itemString = process.argv[i];
    run(itemString);
}

//console.log(to_3_bytes_be(record).map(x=>x.toString(16)));

