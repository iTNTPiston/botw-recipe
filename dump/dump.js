
const {
    Num_Ingredients_Max, Num_Parts, Num_Ingredients_Total, Num_Recipe_Per_Part, Num_Recipe_Last_Part, Main_Record_Size
} = require("./constants.js")
const {CookingData} = require("./bundle.js");
const pot = new CookingData();
const fs = require("fs");

const { spawn } = require('child_process');
const { convert_to_record, assert } = require("./adapter.js");

// This script produces data folder which contains the database in 32 parts

const FORCE = true;

const DATA_DIR = "../data";

class Adapter {
    cook(items){
        if (items.length === 0){
            return 0;
        }
         
        return convert_to_record(pot.cook_hp(items))
    }
}

function array2d(first_order, second_order){
    const array = [];
    for (let i=0;i<first_order;i++){
        array[i] = [];
        for (let j=0;j<second_order;j++){
            array[i].push(0);
        }
    }
    return array;
}

// given id_data which contains a list of items, it will iterate from start to end as if indices in the multichoose set of the items
class RecipeIterator{
    constructor(id_data, start, end){
        this.current = start;
        this.end = end;
        this.id_data = id_data;
        this.num_items = id_data.length;

        const data = array2d(Num_Ingredients_Max+1, this.num_items+1)
        const bino = array2d(this.num_items+Num_Ingredients_Max, Num_Ingredients_Max+1)
        // binomial(n, k), k<=NUM_INGR is bino[n][k]

        // Compute binomial with dynamic programming
        for (let n = 0; n<this.num_items+Num_Ingredients_Max; n++) {
            bino[n][0] = 1;
        }
            
        for (let k=0; k<Num_Ingredients_Max+1; k++) {
            bino[k][k] = 1;
        }
        
        for (let n=1;n<this.num_items+Num_Ingredients_Max;n++) {
            for (let k=1;k<Num_Ingredients_Max+1;k++) {
                bino[n][k] = bino[n-1][k-1] + bino[n-1][k]
            }
        }

        // data[i][m] is size of choosing i ingredients from m, so bino[i+m-1][i]
        for (let m=0;m <this.num_items+1;m++) {
            data[0][m] = 1;
        }

        for (let i=1;i<Num_Ingredients_Max+1;i++){
            for (let m=0;m<this.num_items+1;m++) {
                data[i][m] = bino[i+m-1][i]
            }
        }
        
        this.data = data
        this.total = data[Num_Ingredients_Max][this.num_items]
    }
        
    next(){
        if (this.current >= this.end || this.current >= this.total){
            return undefined;
        }
            
        let input = this.current;
        this.current += 1;
        
        let rest_items = this.num_items;
        const items = [];
        let good = false;

        for (let item=0;item<Num_Ingredients_Max;item++) {
            let index = 0;
            for (let m=this.num_items-rest_items+1; m<this.num_items+1; m++) {
                if (index + this.data[Num_Ingredients_Max-1-item][this.num_items-m+1] > input){
                    items.push(m-1);
                    good = true;
                    break;
                }
                    
                index += this.data[Num_Ingredients_Max-1-item][this.num_items-m+1];
            }
                
            
            if (!good){
                break;
            }
            
            rest_items=this.num_items-items[item];
            input -= index;
        }

        if (good){
            return items.filter(i=>i!==0).map(i=>this.id_data[i]);
        }
        return undefined;
    }
        
}
     
function run_dump(part){
    
    assert(0 <= part && part < Num_Parts);
    // Load the items
    const id_data_dict = require("../ids.json");
    const id_data = [];
    for (let i=0;i<Num_Ingredients_Total;i++){
        id_data.push("");
    }
    for (const k in id_data_dict){
        if (id_data_dict[k] === "<Invalid>"){
            id_data[k] = "Paraglider";
        }else{
            id_data[k] = id_data_dict[k];
        }
        
    }
    assert(id_data.length === Num_Ingredients_Total)

    const UPDATE_EVERY = 200; // ms
    const updateStart = UPDATE_EVERY*part;
    const updateInterval = UPDATE_EVERY*Num_Parts;

    const partStr = part < 10 ? `0${part}` : `${part}`;

    const adapter = new Adapter();

    // Initialize Dumper
    const recipes = new RecipeIterator(id_data, part*Num_Recipe_Per_Part,(part+1)*Num_Recipe_Per_Part)

    const total = part === Num_Parts-1 ? Num_Recipe_Last_Part : Num_Recipe_Per_Part;
    const desc = `Part ${partStr}`;
    

    const buffer = new Uint8Array(total*Main_Record_Size);
    let count = 0;
    let recipe = recipes.next();
    let lastUpdated = Date.now()+updateStart-updateInterval;
    let lastCount = 0;

    while (recipe !== undefined){
        const main_data = adapter.cook(recipe);
        const [b1, b2 ,b3] = to_3_bytes_be(main_data);
        buffer[count*Main_Record_Size] = b1;
        buffer[count*Main_Record_Size+1] = b2;
        buffer[count*Main_Record_Size+2] = b3;
        recipe = recipes.next();
        count++;

        if (Date.now() - lastUpdated > updateInterval){
            // update
            const ips = (count - lastCount)/(updateInterval/1000.0);
            lastUpdated = Date.now();
            lastCount = count;
            const percentage = Math.floor((count/total)*100) + "%";
            console.log(`${desc}: ${percentage} | ${count}/${total} (${ips}it/s)           `);
        }
        

    }

    fs.writeFileSync(DATA_DIR+"/"+partStr+".db", buffer);
    console.log(`${desc}: 100%                                                              `);
}
    

function run_multi(){
    if (fs.existsSync(DATA_DIR)){
        if(!FORCE) {
            console.log("The data directory exists");
            return;
        }
    }else{
        fs.mkdirSync(DATA_DIR, { recursive: true });
    }

    const children = [];
    for (let i=0;i<Num_Parts;i++) {
        const child = spawn("node", ["dump.js", `${i}`])
        
        let updatePrefix = "";
        for (let j=0;j<i;j++){
            updatePrefix+="\n";
        }
        let updatePostfix = "\033[F\033[F";
        for (let j=0;j<i;j++){
            updatePostfix+="\033[F";
        }
        child.stdout.setEncoding('utf8');

        child.stdout.on('data', function(data) {
            console.log(`${updatePrefix}${data}${updatePostfix}`);
        });

        children.push(child);
    }

}
if (process.argv[1].endsWith("dump.js")){
    if (process.argv.length === 2){
        run_multi();
    }else{
        run_dump(parseInt(process.argv[2]));
    }
}


