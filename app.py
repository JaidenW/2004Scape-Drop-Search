import os
import re
import json
from typing import Dict, List
from fuzzywuzzy import fuzz, process

class DropParser:
    def __init__(self):
        self.base_paths = [
            r"Server\data\src\scripts\drop tables\scripts",
            r"Server\data\src\scripts\areas"
        ]
        self.shared_droptables_path = r"Server\data\src\scripts\drop tables\scripts\shared_droptables.rs2"
        self.drop_table_mappings = {
            'rare_drop_table': 'randomherb',
            'ultrarare_drop_table': 'ultrarare_getitem',
            'gem_drop_table': 'randomjewel'
        }
        self.reverse_drop_table_mappings = {v: k for k, v in self.drop_table_mappings.items()}
        self.monsters: Dict[str, List[dict]] = {}
        self.items_to_monsters: Dict[str, List[str]] = {}
        self.drop_tables: Dict[str, List[dict]] = {}
        self.empty_files = self.load_empty_files()
        self.parse_files()

    def load_empty_files(self):
        try:
            with open("empty_files.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def parse_files(self):
        new_empty_files = {}
        
        if os.path.exists(self.shared_droptables_path):
            self.parse_shared_droptables(self.shared_droptables_path)
        
        for base_path in self.base_paths:
            if not os.path.exists(base_path):
                continue

            files_found = False
            for root, _, files in os.walk(base_path):
                for filename in files:
                    full_path = os.path.join(root, filename)
                    if 'shared_droptables.rs2' in filename.lower():
                        continue
                    files_found = True
                    
                    current_mtime = os.path.getmtime(full_path)
                    if full_path in self.empty_files and self.empty_files[full_path] == current_mtime:
                        new_empty_files[full_path] = current_mtime
                        continue
                    
                    drops = self.parse_drop_file(full_path)
                    if drops:
                        monster_name = filename.split('.')[0]
                        if monster_name in self.monsters:
                            self.monsters[monster_name].extend(drops)
                        else:
                            self.monsters[monster_name] = drops
                        for drop in drops:
                            item = drop['item']
                            if item not in self.items_to_monsters:
                                self.items_to_monsters[item] = []
                            if monster_name not in self.items_to_monsters[item]:
                                self.items_to_monsters[item].append(monster_name)
                    else:
                        new_empty_files[full_path] = current_mtime
            
            if not files_found:
                pass
        
        with open("empty_files.json", "w") as f:
            json.dump(new_empty_files, f)
        
        print(f"Loaded {len(self.monsters)} monsters")
        print(f"Loaded {len(self.items_to_monsters)} items")
        print(f"Loaded {len(self.drop_tables)} shared drop tables")

    def parse_quantity(self, quantity_str: str) -> str:
        quantity_str = quantity_str.strip()
        calc_match = re.match(r'calc\(random\((\d+)\)\s*\+\s*(\d+)\)', quantity_str)
        if calc_match:
            random_max = int(calc_match.group(1))
            offset = int(calc_match.group(2))
            return f"{offset}-{random_max + offset}"
        try:
            int(quantity_str)
            return quantity_str
        except ValueError:
            return '1'

    def parse_drop_file(self, file_path: str, is_drop_table: bool = False) -> List[dict]:
        drops = []
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
                if not is_drop_table and 'npc_param(death_drop)' in content:
                    drops.append({'item': 'default_drop', 'chance': '1/1', 'quantity': '1', 'members': False, 'rarity': 'Common'})

                blocks = re.split(r'(?:else\s*)?if\s*\(\$random\s*<\s*(\d+)\)', content)
                if len(blocks) > 1:
                    blocks = blocks[1:]
                    previous_chance = 0
                    
                    for i in range(0, len(blocks), 2):
                        upper_bound = int(blocks[i])
                        block_content = blocks[i + 1]
                        is_members = 'map_members = true' in block_content
                        
                        drop_matches = re.findall(
                            r'obj_add\(npc_coord,\s*([^,]+)(?:,\s*([^,]+))?(?:,\s*\^lootdrop_duration\))?', 
                            block_content
                        )
                        for match in drop_matches:
                            item = match[0].strip()
                            quantity = match[1].strip() if len(match) > 1 and match[1] else '1'
                            successes = upper_bound - previous_chance
                            if successes <= 0:
                                continue
                            chance = f"{successes}/128"
                            if item.startswith('~'):
                                drops.append({
                                    'item': item,
                                    'chance': chance,
                                    'quantity': '1',
                                    'members': is_members,
                                    'rarity': 'Common'
                                })
                            else:
                                parsed_quantity = self.parse_quantity(quantity)
                                drops.append({
                                    'item': item,
                                    'chance': chance,
                                    'quantity': parsed_quantity,
                                    'members': is_members,
                                    'rarity': 'Common'
                                })
                            previous_chance = upper_bound

        except Exception:
            pass
            
        return drops

    def reduce_to_one(self, chance: str) -> str:
        if '/' not in chance:
            return chance
        num, denom = map(int, chance.split('/'))
        if num == 0:
            return "0/1"
        reduced_denom = round(denom / num)
        return f"1/{reduced_denom}"

    def parse_shared_droptables(self, file_path: str):
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
                procedures = re.split(r'\[proc,[^\]]+\]\(\)\(namedobj, int\)', content)[1:]
                proc_names = re.findall(r'\[proc,([^\]]+)\]\(\)\(namedobj, int\)', content)
                
                for proc_name, proc_content in zip(proc_names, procedures):
                    drops = []
                    proc_content = proc_content.strip()
                    
                    early_return = re.search(r'if\s*\(map_members\s*=\s*false\)\s*\{\s*return\s*\(([^,]+),\s*([^)]+)\);', proc_content)
                    if early_return:
                        item, quantity = early_return.groups()
                        drops.append({
                            'item': item.strip(),
                            'chance': '1/1',
                            'quantity': self.parse_quantity(quantity),
                            'members': False,
                            'rarity': 'Common'
                        })
                    
                    random_def = re.findall(r'\$random\s*=\s*random\((\d+)\);', proc_content)
                    random_max = 128
                    if random_def:
                        random_max = int(random_def[-1])
                    
                    blocks = re.split(r'(?:else\s*)?if\s*\(\$random\s*<\s*(\d+)\)', proc_content)[1:]
                    previous_chance = 0
                    
                    is_rare_drop_table = proc_name == 'randomherb'
                    
                    for i in range(0, len(blocks), 2):
                        upper_bound = int(blocks[i])
                        block_content = blocks[i + 1]
                        is_members = 'map_members = true' in block_content or (is_rare_drop_table and drops)
                        
                        return_matches = re.findall(r'return\s*\(([^,]+),\s*([^)]+)\);', block_content)
                        proc_matches = re.findall(r'return\s*\(~([^\)]+)\);', block_content)
                        
                        for item, quantity in return_matches:
                            item = item.strip()
                            successes = upper_bound - previous_chance
                            chance = f"{successes}/{random_max}"
                            parsed_quantity = self.parse_quantity(quantity)
                            drops.append({
                                'item': item,
                                'chance': chance,
                                'quantity': parsed_quantity,
                                'members': is_members,
                                'rarity': 'Common'
                            })
                            previous_chance = upper_bound
                        
                        for proc_ref in proc_matches:
                            successes = upper_bound - previous_chance
                            chance = f"{successes}/{random_max}"
                            drops.append({
                                'item': f"~{proc_ref}",
                                'chance': chance,
                                'quantity': '1',
                                'members': is_members,
                                'rarity': 'Common'
                            })
                            previous_chance = upper_bound
                    
                    switch_match = re.search(r'switch_int\s*\(random\((\d+)\)\)\s*\{([^}]+)\}', proc_content)
                    if switch_match:
                        switch_max = int(switch_match.group(1)) + 1
                        switch_content = switch_match.group(2)
                        case_matches = re.findall(r'case\s*\d+\s*:\s*return\s*\(([^,]+),\s*([^)]+)\);', switch_content)
                        default_match = re.search(r'case\s*default\s*:\s*return\s*\(([^,]+),\s*([^)]+)\);', switch_content)
                        chance = f"1/{switch_max}"
                        for item, quantity in case_matches:
                            drops.append({
                                'item': item.strip(),
                                'chance': chance,
                                'quantity': self.parse_quantity(quantity),
                                'members': False,
                                'rarity': 'Common'
                            })
                        if default_match:
                            item, quantity = default_match.groups()
                            drops.append({
                                'item': item.strip(),
                                'chance': chance,
                                'quantity': self.parse_quantity(quantity),
                                'members': False,
                                'rarity': 'Common'
                            })
                    
                    if drops:
                        self.drop_tables[proc_name] = drops
                
                for table_name, proc_name in self.drop_table_mappings.items():
                    if proc_name in self.drop_tables:
                        self.drop_tables[table_name] = self.drop_tables[proc_name]
                
        except Exception:
            pass

    def fuzzy_search(self, query: str, choices: List[str], limit: int = 5) -> List[tuple]:
        matches = process.extract(query, choices, limit=limit, scorer=fuzz.ratio)
        if matches and matches[0][1] == 100:
            return [m for m in matches if m[1] >= 95]
        return matches

    def display_drop_table(self, table_name: str, base_chance: str = "1/1", is_members: bool = False, visited: set = None) -> None:
        if visited is None:
            visited = set()
        if table_name in visited:
            print(f"    (Recursive reference to {table_name} skipped)")
            return
        visited.add(table_name)
        
        if table_name not in self.drop_tables or not self.drop_tables[table_name]:
            print(f"    (No data found for {table_name})")
            return
        
        base_num, base_denom = map(int, base_chance.split('/'))
        print(f"\n    {table_name} contents (Base Chance: {base_chance}):")
        print("    " + "-" * 60)
        print(f"    {'Item':<25} {'Chance':>12} {'Quantity':>10} {'Members':>8}")
        print("    " + "-" * 60)
        for drop in self.drop_tables[table_name]:
            adjusted_chance = drop['chance'] if drop['chance'] == '1/1' else self.reduce_to_one(f"{int(drop['chance'].split('/')[0]) * base_num}/{int(drop['chance'].split('/')[1]) * base_denom}")
            members_str = "Yes" if drop['members'] else "No"
            print(f"    {drop['item']:<25} {adjusted_chance:>12} {drop['quantity']:>10} {members_str:>8}")
            if drop['item'].startswith('~'):
                nested_table = drop['item'].lstrip('~')
                if nested_table in self.drop_tables:
                    self.display_drop_table(nested_table, adjusted_chance, drop['members'], visited)

    def show_special_tables(self):
        for table_name in self.drop_table_mappings.keys():
            self.display_drop_table(table_name)

    def search_monster(self, monster_name: str) -> None:
        monster_name = monster_name.lower()
        all_monsters = list(self.monsters.keys())
        
        matches = self.fuzzy_search(monster_name, all_monsters)
        
        if matches and matches[0][1] >= 80:
            for match, score in matches:
                if score >= 80:
                    monster = match
                    print(f"\nDrops for {monster} (Match: {score}%):")
                    print("-" * 60)
                    print(f"{'Item':<25} {'Chance':>12} {'Quantity':>10} {'Members':>8}")
                    print("-" * 60)
                    special_table_references = {}
                    for drop in self.monsters[monster]:
                        members_str = "Yes" if drop['members'] else "No"
                        adjusted_chance = self.reduce_to_one(drop['chance'])
                        print(f"{drop['item']:<25} {adjusted_chance:>12} {drop['quantity']:>10} {members_str:>8}")
                        if drop['item'].startswith('~'):
                            nested_table = drop['item'].lstrip('~')
                            drop_table_key = self.reverse_drop_table_mappings.get(nested_table, nested_table)
                            if drop_table_key in self.drop_tables:
                                special_table_references[nested_table] = (adjusted_chance, drop['members'])
                    
                    for table_name, (chance, is_members) in special_table_references.items():
                        self.display_drop_table(table_name, chance, is_members)
                    
                    print("=" * 60)
        elif matches:
            best_match, best_score = matches[0]
            monster = best_match
            print(f"\nBest match for '{monster_name}':")
            print(f"Drops for {monster} (Match: {best_score}%):")
            print("-" * 60)
            print(f"{'Item':<25} {'Chance':>12} {'Quantity':>10} {'Members':>8}")
            print("-" * 60)
            special_table_references = {}
            for drop in self.monsters[monster]:
                members_str = "Yes" if drop['members'] else "No"
                adjusted_chance = self.reduce_to_one(drop['chance'])
                print(f"{drop['item']:<25} {adjusted_chance:>12} {drop['quantity']:>10} {members_str:>8}")
                if drop['item'].startswith('~'):
                    nested_table = drop['item'].lstrip('~')
                    drop_table_key = self.reverse_drop_table_mappings.get(nested_table, nested_table)
                    if drop_table_key in self.drop_tables:
                        special_table_references[nested_table] = (adjusted_chance, drop['members'])
            
            for table_name, (chance, is_members) in special_table_references.items():
                self.display_drop_table(table_name, chance, is_members)
            
            print("=" * 60)
            print(f"Note: No matches above 80%. Showing best match found.")
            print("Did you mean one of these?")
            for match, score in matches[1:]:
                print(f"  {match} ({score}% match)")
        else:
            print(f"No matches found for '{monster_name}'")

    def search_item(self, item_name: str) -> None:
        item_name = item_name.lower()
        all_items = list(self.items_to_monsters.keys())
        
        matches = self.fuzzy_search(item_name, all_items)
        
        if matches and matches[0][1] >= 80:
            for match, score in matches:
                if score >= 80:
                    item = match
                    print(f"\nMonsters that drop {item} (Match: {score}%):")
                    print("-" * 60)
                    print(f"{'Monster':<25} {'Chance':>12} {'Quantity':>10} {'Members':>8}")
                    print("-" * 60)
                    for monster in self.items_to_monsters[item]:
                        for drop in self.monsters[monster]:
                            if drop['item'] == item:
                                members_str = "Yes" if drop['members'] else "No"
                                adjusted_chance = self.reduce_to_one(drop['chance'])
                                print(f"{monster:<25} {adjusted_chance:>12} {drop['quantity']:>10} {members_str:>8}")
                    print("=" * 60)
        elif matches:
            best_match, best_score = matches[0]
            item = best_match
            print(f"\nBest match for '{item_name}':")
            print(f"Monsters that drop {item} (Match: {best_score}%):")
            print("-" * 60)
            print(f"{'Monster':<25} {'Chance':>12} {'Quantity':>10} {'Members':>8}")
            print("-" * 60)
            for monster in self.items_to_monsters[item]:
                for drop in self.monsters[monster]:
                    if drop['item'] == item:
                        members_str = "Yes" if drop['members'] else "No"
                        adjusted_chance = self.reduce_to_one(drop['chance'])
                        print(f"{monster:<25} {adjusted_chance:>12} {drop['quantity']:>10} {members_str:>8}")
            print("=" * 60)
            print(f"Note: No matches above 80%. Showing best match found.")
            print("Did you mean one of these?")
            for match, score in matches[1:]:
                print(f"  {match} ({score}% match)")
        else:
            print(f"No matches found for '{item_name}'")

def main():
    parser = DropParser()
    
    while True:
        print("\n1. Search by monster")
        print("2. Search by item")
        print("3. Show special drop tables")
        print("4. Exit")
        choice = input("Choose an option (1-4): ")
        
        if choice == '1':
            monster = input("Enter monster name: ")
            parser.search_monster(monster)
        elif choice == '2':
            item = input("Enter item name: ")
            parser.search_item(item)
        elif choice == '3':
            parser.show_special_tables()
        elif choice == '4':
            print("Goodbye!")
            break
        else:
            print("Invalid option, please try again")

if __name__ == "__main__":
    main()