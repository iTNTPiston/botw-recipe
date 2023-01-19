use std::cmp;
use std::fs;
use std::io::{self, Write};
use std::sync::{Arc, atomic::{AtomicBool, Ordering}};

use bit_set::BitSet;

mod command;
mod data;
mod recipe;
mod sys;
mod view;



fn main() {
    println!("botw-recipe");
    println!("Recipe Database for WMC");
    println!("Type ? for help");
    repl();
    sys::remove_temp_dir();
}

fn repl() {
    let mut crit_mgr = data::CritMgr::new();
    
    let converter = recipe::RecipeConverter::new();

    println!("{:?}", converter.to_materials(746));
    println!("{:?}", converter.to_materials(478491435));

    let running = Arc::new(AtomicBool::new(false));
    let can_interrupt = set_interrupt(running.clone()).is_ok();

    let mut query = data::Query {
        minhp: 0,
        maxhp: 120,
        crit: false,
        include_modifiers: 0,
        exclude_modifiers: 0,
        exclude_materials: BitSet::new()
    };

    loop {
        let mut line = String::new();
        print!("{}> ", view::query(&query));
        io::stdout().flush().unwrap();
        let b = io::stdin().read_line(&mut line).unwrap();
        if b == 0 {
            continue;
        }
        let command = line.trim().to_ascii_lowercase();
        if command == "exit" {
            break;
        }

        if let Err(msg) = execute(&command, &converter, &mut crit_mgr, &mut query, can_interrupt, running.clone()) {
            println!("error: {}", msg);
        }
        
        println!("");
    }
   
}

/// Set Ctrl C interrupt handler for stopping
fn set_interrupt(running: Arc<AtomicBool>) -> Result<(), ctrlc::Error>{
    ctrlc::set_handler(move || {
        if running.load(Ordering::SeqCst) {
            println!("interrupt");
            running.store(false, Ordering::SeqCst)
        }else{
            println!("interrupt");
            println!("Use \"exit\" to exit the program");
            println!("");
            print!("(interrupted) > ");
            io::stdout().flush().unwrap();
        }
    })
}

fn execute(command: &str, converter: &recipe::RecipeConverter, crit_mgr: &mut data::CritMgr, query: &mut data::Query, can_interrupt: bool, running: Arc<AtomicBool>) -> Result<(), String> {
    let cmd_parts: Vec<&str> = command.split_whitespace().collect();
    if cmd_parts.is_empty() {
        return Ok(());
    }

    match cmd_parts[0] {
        "?" => {
            help();
            Ok(())
        },
        "cook" => command::cook(&cmd_parts[1..], &converter, crit_mgr),
        "inspect" => {
            command::inspect(&cmd_parts[1..], &converter);
            Ok(())
        },
        "minhp" => {
            command::get_u32_arg(&cmd_parts, "minhp").map(|hp|{
                let hp = cmp::min(120, cmp::max(0, hp)) as u8;
                query.minhp = hp;
                println!("{}", view::query_minhp_detail(query));
            })
        },
        "maxhp" => {
            command::get_u32_arg(&cmd_parts, "maxhp").map(|hp|{
                let hp = cmp::min(120, cmp::max(0, hp)) as u8;
                query.maxhp = hp;
                println!("{}", view::query_minhp_detail(query));
            })
        },
        "crit" => {
            query.crit = !query.crit;
            println!("{}", view::query_crit_detail(&query));
            Ok(())
        },
        "modifier+" => {
            command::get_arg(&cmd_parts, "modifier_list").map(|modifier_list|{
                query.include_modifiers = view::modifier_flag(&modifier_list);
                println!("{}", view::query_modifier_detail(query));
            })
        },
        "modifier-" => {
            command::get_arg(&cmd_parts, "modifier_list").map(|modifier_list|{
                query.exclude_modifiers = view::modifier_flag(&modifier_list);
                println!("{}", view::query_modifier_detail(query));
            })
        },
        "exclude+" => command::exclude_add(&cmd_parts[1..], converter, &mut query.exclude_materials),
        "exclude-" => command::exclude_remove(&cmd_parts[1..], converter, &mut query.exclude_materials),

        "status" => {
            println!("{}", view::query_detail(query, converter));
            println!("");
            match query.validate() {
                Ok(_) => {
                    println!("Use \"run <output>\" to search based on the configuration and save the results to a file.");
                    println!("Use \"reduce <input> <output>\" to filter the result based on excluded materials only.");
                    Ok(())
                },
                Err(msgs) => {
                    Err(msgs.join("\n"))
                }
            }
            
        },
        "load" => {
            command::get_arg(&cmd_parts, "preset_file").and_then(|preset_path| {
                let commands = load_preset(&preset_path);
                for command in commands {
                    execute(&command, converter, crit_mgr, query, can_interrupt, running.clone())?;
                }
                Ok(())
            })
        }

        "run" => {
            command::get_arg(&cmd_parts, "output_file").and_then(|output| {
                if can_interrupt {
                    println!("Use Ctrl+C to abort the process");
                }
                
                data::processing::run_query(&query, &output, running.clone())
            })
        },
        "sample" => {
            command::get_arg(&cmd_parts, "input_file").and_then(|input| {
                if can_interrupt {
                    println!("Use Ctrl+C to abort the process");
                }
                
                data::processing::run_sample(&input, converter, running.clone())
            })
        }
        "reduce" => {
            command::get_arg_pair(&cmd_parts, "input_file", "output_file").and_then(|(input, output)| {
                if can_interrupt {
                    println!("Use Ctrl+C to abort the process");
                }
                
                data::processing::run_reduce(&query, &input, &output, running.clone())
            })
        },
        "dump" => {
            command::get_arg_pair(&cmd_parts, "input_file", "output_file").and_then(|(input, output)| {
                println!("Dumping results from {} to {}", input, output);
                    
                data::processing::run_dump(&input, &output, converter, crit_mgr)?;
                println!("Done");
                Ok(())
            })
        }
        other => Err(format!("Unknown command \"{}\"", other))
    }
}

fn help() {
    println!("Available Commands:");
    println!("cook MATERIAL ...      Get a single recipe given materials. Materials are given as ids");
    println!("inspect WORD ...       Look up material id with words");
    println!("minhp VALUE            Configure to search only recipes with hp >= VALUE");
    println!("maxhp VALUE            Configure to search only recipes with hp <= VALUE");
    println!("crit                   Toggle search only include/exclude rng heart crit (will not exclude guaranteed heart crit)");
    println!("modifier+ FLAGS        Configure to search only recipes that have all of the modifiers. Use the first letter for modifiers, e.g. \"AZM\" = Attack Up, Zoom and Multishot");
    println!("modifier- FLAGS        Configure to exclude recipes that have any of the modifiers.");
    println!("exclude+ MATERIAL ...  Add materials to the exclude list. Search will exclude recipes that have any of the material in the list.");
    println!("exclude- MATERIAL ...  Remove materials from the exclude list.");
    println!("status                 View the current search configuration");
    println!("load PRESET            Load a preset file. A preset file contains text commands, one per line");
    println!("run OUTPUT             Run the search and save results to OUTPUT (results are binary)");
    println!("sample INPUT           Read search output and print materials used");
    println!("reduce INPUT OUTPUT    Use previous search output and filter based (only) on excluded materials");
    println!("dump INPUT OUTPUT      Dump previous search output to a YAML file");
    println!("exit                   Exit the program");
}

fn load_preset(path: &str) -> Vec<String> {
    let file = match fs::read_to_string(path) {
        Ok(f) => f,
        Err(_) => {
            println!("Cannot open {}", path);
            return vec![];
        }
    };

    file.split('\n').into_iter().map(|x| x.to_string()).collect()
}
