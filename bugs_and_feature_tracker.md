# Bugs and Feature Enhancements
This is a page of some of the enhancements and ideas that I'd like to work on, sorted into priorities based on what I think will make the most impact on the Audiobook Maker.

## Enhancements

## In Progress
- Be able to edit the sentences in the table and or delete them - https://github.com/JarodMica/audiobook_maker/issues/80

### Need to Add
- Missing generations, check and verify that all sentences have audio generated for them - https://github.com/JarodMica/audiobook_maker/issues/72

### Should Add
- Allow for exporting AB even if all sentences have not been generated - https://github.com/JarodMica/audiobook_maker/issues/82
- Save GUI state in a settings file
- Book Name reduncancy to Table header instead of textbox section (Maybe add?  An indicate that no AB has been loaded is kinda nice)


### Would Be Nice
- Chapter Separation
- Pauses between sentences implemented in the text file - https://github.com/JarodMica/audiobook_maker/issues/84
- Better sentence segmentation, allowing user to split sentences on quotation marks - https://github.com/JarodMica/audiobook_maker/issues/93
- Find and replace option - https://github.com/JarodMica/audiobook_maker/issues/94
- Configure default Narrator color in settings

## Bugs

### High Priority
- Text Parser - https://github.com/JarodMica/audiobook_maker/issues/68

### Medium Priority
- Hangs while listening - https://github.com/JarodMica/audiobook_maker/issues/81

### Low Priority
- If user does not make any generation setting modifications, generation_settings.json will not be created for the audiobook, causing "Load Existing Audiobook" to fail if they want to reload in the AB from maybe a previous section

## Completed
[x] Turn regenerate Mode --> Regenerate column checkbox ~ v3.4

[x] Speaker column to sentence in addition (or instead) of colors ~ v3.4

[x] Move TTS and S2S dropdown menus to the right hand side ~ v3.4