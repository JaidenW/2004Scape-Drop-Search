import os
import re
from typing import Dict, List
from fuzzywuzzy import fuzz, process

class DropParser:
    def __init__(self):
        self.base_paths = [
            r"Server\data\src\scripts\drop tables\scripts",
            r"Server\data\src\scripts\areas"
        ]
        self.monsters: Dict[str, List[dict]] = {}
        self.items_to_monsters: Dict[str, List[str]] = {}
        self.parse_files()

    def parse_files(self):
        """Parse all files in the specified folders and their subfolders"""
        for base_path in self.base_paths:
            print(f"Looking in folder: {os.path.abspath(base_path)}")
            if not os.path.exists(base_path):
                print(f"Error: Folder '{base_path}' does not exist")
                continue

            files_found = False
            for root, _, files in os.walk(base_path):
                for filename in files:
                    full_path = os.path.join(root, filename)
                    files_found = True
                    monster_name = filename.split('.')[0]
                    print(f"Processing file: {full_path}")
                    drops = self.parse_drop_file(full_path)
                    if drops:
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
            
            if not files_found:
                print(f"No files found in {base_path}")
        
        print(f"Loaded monsters: {list(self.monsters.keys())}")
        print(f"Loaded items: {list(self.items_to_monsters.keys())}")

    def parse_quantity(self, quantity_str: str) -> str:
        """Parse quantity string, handling both fixed numbers and calc(random(n) + m)"""
        quantity_str = quantity_str.strip()
        calc_match = re.match(r'calc\(random\((\d+)\)\s*\+\s*(\d+)\)', quantity_str)
        if calc_match:
            random_max = int(calc_match.group(1))
            offset = int(calc_match.group(2))
            return f"{offset}-{random_max + offset}"  # e.g., "1-3" for calc(random(2) + 1)
        try:
            int(quantity_str)  # Check if it's a simple number
            return quantity_str
        except ValueError:
            return quantity_str  # Return as-is if it's neither

    def parse_drop_file(self, file_path: str) -> List[dict]:
        """Parse a single drop file and return list of drops with probabilities"""
        drops = []
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
                if 'npc_param(death_drop)' in content:
                    drops.append({'item': 'default_drop', 'chance': '100%', 'quantity': '1', 'members': False})

                blocks = re.split(r'if\s*\(\$random\s*<\s*(\d+)\)', content)[1:]
                previous_chance = 0
                
                for i in range(0, len(blocks), 2):
                    upper_bound = int(blocks[i])
                    block_content = blocks[i + 1]
                    is_members = 'map_members = true' in block_content
                    
                    drop_matches = re.findall(
                        r'obj_add\(npc_coord,\s*([^,]+),\s*([^,]+),\s*\^lootdrop_duration\)', 
                        block_content
                    )
                    
                    for item, quantity in drop_matches:
                        chance = (upper_bound - previous_chance) / 128 * 100
                        parsed_quantity = self.parse_quantity(quantity)
                        drops.append({
                            'item': item.strip(),
                            'chance': f'{chance:.2f}%',
                            'quantity': parsed_quantity,
                            'members': is_members
                        })
                        previous_chance = upper_bound

                if drops:
                    print(f"Parsed {len(drops)} drops from {file_path}")
                else:
                    print(f"No drops found in {file_path}")
                    
        except Exception as e:
            print(f"Error parsing {file_path}: {str(e)}")
            
        return drops

    def fuzzy_search(self, query: str, choices: List[str], limit: int = 5) -> List[tuple]:
        """Perform fuzzy matching and return top matches"""
        return process.extract(query, choices, limit=limit, scorer=fuzz.partial_ratio)

    def search_monster(self, monster_name: str) -> None:
        monster_name = monster_name.lower()
        all_monsters = list(self.monsters.keys())
        
        matches = self.fuzzy_search(monster_name, all_monsters)
        
        if matches and matches[0][1] >= 80:
            for match, score in matches:
                if score >= 60:
                    monster = match
                    print(f"\nDrops for {monster} (Match: {score}%):")
                    print("-" * 60)
                    print(f"{'Item':<20} {'Chance':>8} {'Quantity':>10} {'Members':>8}")
                    print("-" * 60)
                    for drop in self.monsters[monster]:
                        members_str = "Yes" if drop['members'] else "No"
                        print(f"{drop['item']:<20} {drop['chance']:>8} {drop['quantity']:>10} {members_str:>8}")
        else:
            print(f"No close matches for '{monster_name}'")
            if matches:
                print("Did you mean one of these?")
                for match, score in matches:
                    print(f"  {match} ({score}% match)")

    def search_item(self, item_name: str) -> None:
        item_name = item_name.lower()
        all_items = list(self.items_to_monsters.keys())
        
        matches = self.fuzzy_search(item_name, all_items)
        
        if matches and matches[0][1] >= 80:
            for match, score in matches:
                if score >= 60:
                    item = match
                    print(f"\nMonsters that drop {item} (Match: {score}%):")
                    print("-" * 60)
                    print(f"{'Monster':<20} {'Chance':>8} {'Quantity':>10} {'Members':>8}")
                    print("-" * 60)
                    for monster in self.items_to_monsters[item]:
                        for drop in self.monsters[monster]:
                            if drop['item'] == item:
                                members_str = "Yes" if drop['members'] else "No"
                                print(f"{monster:<20} {drop['chance']:>8} {drop['quantity']:>10} {members_str:>8}")
        else:
            print(f"No close matches for '{item_name}'")
            if matches:
                print("Did you mean one of these?")
                for match, score in matches:
                    print(f"  {match} ({score}% match)")

def main():
    parser = DropParser()
    
    while True:
        print("\n1. Search by monster")
        print("2. Search by item")
        print("3. Exit")
        choice = input("Choose an option (1-3): ")
        
        if choice == '1':
            monster = input("Enter monster name: ")
            parser.search_monster(monster)
        elif choice == '2':
            item = input("Enter item name: ")
            parser.search_item(item)
        elif choice == '3':
            print("Goodbye!")
            break
        else:
            print("Invalid option, please try again")

if __name__ == "__main__":
    main()