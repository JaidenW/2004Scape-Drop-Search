# 2004Scape (Lost City) Drop Table Search

This is just a really simple app to parse and search the existing drop tables in the source code, it utilizes "fuzzy" search so that you don't need to know the exact item name or you can use space instead of _, or even just type the name slightly wrong.

I also want to mention that the "members" column might be different to what you expect of it. It's not if the item it's self is a members item. Within the drop tables there are certian drops for monsters which require you to be in a members world. This is for things like dark wizards which are F2P monsters, but they have specific items which will only drop on members worlds, for example; Blood Runes. 

![First Start](https://i.imgur.com/iLWhuIL.png)
![Monster Search](https://i.imgur.com/ZXPpGLr.png)
![Item Search](https://i.imgur.com/NoHermx.png)

## Requirements
1. Python
2. fuzzywuzzy
3. python-Levenshtein

## How to use
1. Create a folder
2. Clone the official source from [here](https://github.com/2004Scape/Server) into the folder you created.
3. This will create the "Server" directory inside that folder.
4. Place the app.py script and other files outside of "Server" directory (like [this](https://i.imgur.com/9UA5cQS.png)
5. Run the start.bat - this will install the requirements if needed and then launch the app. If you want to install the requirements manually, just run ``py ./app.py`` this does also launch faster since it's not checking for requirements first.

### Updates

#### 1.0.1 
- Added support for region based drops, tons of monsters were not included.

#### 1.0.2
- Added support for shared drop tables, including; random herbs, gem drops, rare drops, megarare drops.
- Reduced the fuzziness but also tuned to be more useful; cha druid now returns chaos_druid instead of druid and when no good match is found, the highest match is still showed in addition to showing prospective matches.

#### 1.0.3
- Cleaned up the initialization output, now only displays simple counts.
- Now generates a json list of files without drops, so we don't try to parse them again (delete the file to manually re-parse)

If you have any issues, or just want to say thanks, my IGN is Jaiden W
