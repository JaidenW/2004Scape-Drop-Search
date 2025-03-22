# 2004Scape (Lost City) Drop Table Search

This is just a really simple app to parse and search the existing drop tables in the source code, it utilizes "fuzzy" search so that you don't need to know the exact item name or you can use space instead of _, or even just type the name slightly wrong, this has a side effect of showing items not related to your search, but i find it preferable to having to know the exact item name in the code.

![First Start](https://github.com/user-attachments/assets/5e6650a1-7496-4c18-89a6-d9ca08b19ffe)
![Monster Search](https://i.imgur.com/2D6BhpN.png)
![Item Search](https://i.imgur.com/Dkq0h8u.png)

## Requirements
1. Python
2. fuzzywuzzy

## How to use
1. Create a folder
2. Clone the official source from [here](https://github.com/2004Scape/Server) into the folder you created.
3. This will create the "Server" directory inside that folder.
4. Place the app.py script and other files outside of "Server" directory (like [this](https://i.imgur.com/9UA5cQS.png)
5. Run the start.bat - this will install the requirements if needed and then launch the app. If you want to install the requirements manually, just run ``py ./app.py`` this does also launch faster since it's not checking for requirements first.

### Final Notes

This is by no means a polished app, it has no GUI and works entirely in command prompt, it's the bare minimum to acomplish the goal. I don't really intend to add any new features, but that doesn't mean if you submit a PR i'll ignore it, it just does what i need it to do. If you want to add something to it, feel free. as long as it could be benificial to someone, i'll happily add it.

This also does not have complete support for every drop, you'll note items named things like "defaultdrop" or "gemdrop", these are not handled by this script because you can generally inferr what those mean, (default drop i'm pretty sure is just bones)
