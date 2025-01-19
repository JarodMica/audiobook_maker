# Bugs and Feature Enhancements
This is a page of some of the enhancements and ideas that I'd like to work on, sorted into priorities based on what I think will make the most impact on the Audiobook Maker.

## Enhancements

## In Progress
- N/a

### High Priority
- Add "Load Voices, and "Load Models" to the Menu Bar
- Allow for loading epubs
- Allow for loading PDFs

### Medium Priority
- Allow for exporting AB even if all sentences have not been generated - https://github.com/JarodMica/audiobook_maker/issues/82
- Save GUI state in a settings file
- Book Name reduncancy to Table header instead of textbox section (Maybe add?  An indicate that no AB has been loaded is kinda nice)
- Persistent settings/save user state - https://github.com/JarodMica/audiobook_maker/issues/118
- Rearranging sentences with drag and drop or something similar


### Low Priority
- Chapter Separation
- Pauses between sentences implemented in the text file - https://github.com/JarodMica/audiobook_maker/issues/84
- Better sentence segmentation, allowing user to split sentences on quotation marks - https://github.com/JarodMica/audiobook_maker/issues/93
- Find and replace option - https://github.com/JarodMica/audiobook_maker/issues/94
- Configure default Narrator color in settings
- Optimize regenerate in bulk for multi-speaker due to model loading
- After Regenerate chosen sentence, select the sentence after for playback - https://github.com/JarodMica/audiobook_maker/issues/118
- Multi-line playback - https://github.com/JarodMica/audiobook_maker/issues/118
- Change some sliders to spinboxes - https://github.com/JarodMica/audiobook_maker/issues/118
- Clarify Audiobook export, might even be better to only allow for the export of the loaded audiobook and allow user to select the folder they want to output to.  This is much more intuitive - https://github.com/JarodMica/audiobook_maker/issues/113
- Export to M4B or audiobook formats

## Bugs

### High Priority
- Text Parser - https://github.com/JarodMica/audiobook_maker/issues/68
- Assure threadsafety for Regenerate Chosen Sentence - https://github.com/JarodMica/audiobook_maker/issues/118

### Medium Priority
- Hangs while listening - https://github.com/JarodMica/audiobook_maker/issues/81
- Missing generations, check and verify that all sentences have audio generated for them - https://github.com/JarodMica/audiobook_maker/issues/72

### Low Priority
- Speaker name left aligns on speaker assignment


## Completed
[x] - Be able to edit the sentences in the table and or delete them - https://github.com/JarodMica/audiobook_maker/issues/80

[x] Turn regenerate Mode --> Regenerate column checkbox ~ v3.4

[x] Speaker column to sentence in addition (or instead) of colors ~ v3.4

[x] Move TTS and S2S dropdown menus to the right hand side ~ v3.4