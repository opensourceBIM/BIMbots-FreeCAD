## How to translate BIMBots

This folder contains one 'master' translation file called bimbots.ts which contains all strings
found in the code. It is generated with:

`pylupdate5 *.py *.ui -ts translations/bimbots.ts`

To translate BIMBots to your language, (FreeCAD plugin only, the Python 
module functions stay in english), download the bimbots.ts file, and translate it
using the [Qt Linguist](https://doc.qt.io/qt-5/linguist-translators.html) tool.

There are also online translation services which accept .ts files, you can use that too.

Once done, save your translation as another file, by adding your language (and
optionally region if applicable) to the filename, ex:

bimbots-fr.ts (for French) or
bimbots-fr_CA.ts (for Canadian French)

Language and region codes are easy to [find on the net](https://www.fincher.org/Utilities/CountryLanguageList.shtml).

Once done, you need to compile your .ts file as a .qm file with:

`lrelease bimbots-fr.ts -qm bimbots-fr.qm`

Once you have both a .ts and a.qm file for your language, create a 
[pull request](https://help.github.com/en/articles/about-pull-requests) here 
and we'll include it!


