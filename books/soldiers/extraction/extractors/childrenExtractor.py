# -*- coding: utf-8 -*-
import re
from operator import itemgetter

from books.soldiers.extraction.extractors.baseExtractor import BaseExtractor
from books.soldiers.extraction.extractionExceptions import *
from shared import regexUtils, textUtils
from books.soldiers.extractionkeys import KEYS
from interface.valuewrapper import ValueWrapper


class ChildrenExtractor(BaseExtractor):

    def extract(self, text):
        super(ChildrenExtractor, self).extract(text)
        self.PATTERN_DEFAULT = r'(?:Lapset|Tytär|Poika|Lapsel|Tylär)(?P<children>[A-ZÄ-Öa-zä-ö,0-9,\.\n -]*?)((?:(?:- ?\n?(?=(?:Ts)|(?:Ts)|(?:Js)|(?:JR)|(?:Osa)|(?:Osall)))|pso ))'
        self.PATTERN_WORDFORMAT = r'(?P<count>yksi|kaksi|kolme|neljä|viisi|kuusi|seitsemän|kahdeksan|yhdeksän|kymmenen) (?:lasta|lapsi|tytär|poika)'
        self.WORDS_TO_NUMBERS_MAPPING = {"yksi": 1, "kaksi": 2, "kolme": 3, "neljä": 4, "viisi": 5, "kuusi": 6, "seitsemän": 7, "kahdeksan": 8, "yhdeksän": 9, "kymmenen": 10}
        self.OPTIONS = (re.UNICODE | re.IGNORECASE)
        self.REQUIRES_MATCH_POSITION = True
        self.childCount = 0
        self.sortedChildren = {"current": "", "manPrevious": "", "spousePrevious": ""}
        self.allChildren = ""        #TODO: Needed for other children extraction. Dirty solution for now.


        preparedText = self._prepareTextForExtraction(text)
        self._findChildren(preparedText)
        return self._constructReturnDict()

    def _prepareTextForExtraction(self, text):
        t = textUtils.takeSubStrBasedOnPos(text, self.matchStartPosition)
        t = re.sub(r'[:;\!\?\+~¨\^\'\"]', '', t)
        return t

    def _findChildren(self, text):
        try:
            foundChildren= regexUtils.safeSearch(self.PATTERN_DEFAULT, text, self.OPTIONS)
            self.childCount = self._getChildCount(foundChildren)
            self.allChildren = foundChildren.group("children")
            self.sortedChildren = self._sortChildrenBasedOnMarriage(foundChildren)
            self.matchFinalPosition = foundChildren.end()
        except regexUtils.RegexNoneMatchException as e:
            self._findChildrenWithNumberWords(text)

    def _findChildrenWithNumberWords(self, text):
        """Sometimes the books list the amount of children in format like "yksi tytär" or "viisi lasta"."""
        try:
            foundChildren= regexUtils.safeSearch(self.PATTERN_WORDFORMAT, text, self.OPTIONS)
            self.childCount = self._mapWordsToChildCount(foundChildren)
            self.matchFinalPosition = foundChildren.end()
        except regexUtils.RegexNoneMatchException as e:
            self.errorLogger.logError(ChildrenException.eType, self.currentChild)

    def _mapWordsToChildCount(self, foundChildren):
        if foundChildren.group("count").lower() in self.WORDS_TO_NUMBERS_MAPPING:
            return self.WORDS_TO_NUMBERS_MAPPING[foundChildren.group("count").lower()]
        else:
            return 0

    def _getChildCount(self, foundChildren):
        children = self._buildListOfChildren(foundChildren)
        return len(children)

    def _buildListOfChildren(self, foundChildren):
        children = foundChildren.group("children")
        #TODO: VERY NAIVE IMPLEMENTATION MAKE BETTER
        childList1 = children.split(",")
        childList2 = []
        for c in childList1:
            c = ' '.join(c.split())
            if len(c) > 2:
                childList2.append(c)
        return childList2

    def _sortChildrenBasedOnMarriage(self, foundChildren):

            sorter = ChildSorter()
            childrenMatchAsString = foundChildren.group("children")
            return sorter.sortChildrenBasedOnMarriage(childrenMatchAsString)


    def _constructReturnDict(self):
        return  { "cursorLocation" : self.matchFinalPosition,
                 KEYS["childCount"]:  ValueWrapper(self.childCount), KEYS["separated"] :  ValueWrapper({KEYS["nyk"]:  ValueWrapper(self.sortedChildren["current"]),
                                                               KEYS["miehEd"] :  ValueWrapper(self.sortedChildren["manPrevious"]),
                                                               KEYS["psoEd"] :  ValueWrapper(self.sortedChildren["spousePrevious"])})}


class ChildSorter():
    """
    We want to separate the children to three categories:
        current: from current marriage,
        manPrevious: from man's previous marriage,
        spousePrevious:  from spouse's previous marriage
    Separation is based on text-patterns from source material and is based on few keywords found from text. We use
    regex to detect the words and then split the text (and children) to categories.
    """
    SPOUSE_PREVIOUS_PATTERN = r'(?P<psoed>pson ed aviol|pson aik aviol|vaimon I aviol|vaimon ed aviol|rvan ed aviol|pson? I aviol|pson I avioi|miehen I)'
    CURRENT_PATTERN = r'(?P<nykaviol>nyk aviol|nykyis aviol)'
    MAN_PREVIOUS_PATTERN = r'(?P<miehed>(?<!n )I aviol|(?<!n )ed aviol|miehen I aviol|miehen aik aviol|(?<!pson )aik aviol|miehen ed aviol|(?<!n )II aviol|(?<!n )II? avlol)'
    OPTIONS = re.UNICODE
    FINAL_CHILD = -1
    childText = ""
    childrenFromCurrentMarriage = ""
    childrenFromMansPreviousMarriage = ""
    childrenFromSpousesPreviousMarriage = ""

    spousePrevMatch = None
    currentMatch = None
    manPrevMatch = None
    textSections = []


    def sortChildrenBasedOnMarriage(self, children):
        self.childText = children
        self._findKeywords(children)
        sections = self._calculateSectionsInText()
        self._sortChildrenFromSections(sections)
        return self._constructReturnDict()

    def _findKeywords(self, text):
        self.spousePrevMatch = regexUtils.search(self.SPOUSE_PREVIOUS_PATTERN, text, self.OPTIONS)
        self.currentMatch = regexUtils.search(self.CURRENT_PATTERN, text, self.OPTIONS)
        self.manPrevMatch = regexUtils.search(self.MAN_PREVIOUS_PATTERN, text, self.OPTIONS)

    def _calculateSectionsInText(self):
        sections = self._createModelOfSections()
        #order sections based on their beginning point in original text
        ordered = sorted(sections, key=itemgetter("begin"))
        return self._calculateSectionEndingPoints(ordered)

    def _createModelOfSections(self):
        #figure out the positions where each section begins and ends and create a datastructure of it
        substrPositions = []
        if self.spousePrevMatch != None:
            substrPositions.append({"type" : "spousePrevious", "begin" : self.spousePrevMatch.start("psoed"), "end" : self.spousePrevMatch.end("psoed")})
        if self.manPrevMatch != None:
            substrPositions.append({"type" : "manPrevious", "begin" : self.manPrevMatch.start("miehed"), "end" : self.manPrevMatch.end("miehed")})
        if self.currentMatch != None:
            substrPositions.append({"type" : "current", "begin" : self.currentMatch.start("nykaviol"), "end" : self.currentMatch.end("nykaviol")})
        return substrPositions

    def _calculateSectionEndingPoints(self, sections):
        for i in range(0, len(sections)):
            if i+1 < len(sections):
                #define the end position of the substring containing the children data. It
                #is the begnning of the next part or the end of the string.
                sections[i]["childEnd"] = sections[i+1]["begin"]
            else:
                sections[i]["childEnd"] = len(self.childText)   #last child in string, so section ends to final character.
        return sections

    def _sortChildrenFromSections(self, sections):
        sepChildrenHelper = {"current": "", "manPrevious" : "", "spousePrevious" : ""}

        #if there was text before the first keyword, interpret them as current children:
        if len(sections) > 0 and sections[0]["begin"] > 0:
            sepChildrenHelper["current"] = self._extractSection(0, sections[0]["begin"])

        if len(sections) == 0:
            #all children are from currentMarriage. This is because when all children are from current, the text
            #doesn't mention any of the keywords.
            sepChildrenHelper["current"] = self.childText

        for item in sections:
            sepChildrenHelper[item["type"]] = self._extractSection(item["end"], item["childEnd"])

        self.childrenFromCurrentMarriage = sepChildrenHelper["current"]
        self.childrenFromMansPreviousMarriage = sepChildrenHelper["manPrevious"]
        self.childrenFromSpousesPreviousMarriage= sepChildrenHelper["spousePrevious"]

    def _extractSection(self, start, end):
        return self.childText[start:end]

    def _constructReturnDict(self):
        return {"current": self.childrenFromCurrentMarriage, "spousePrevious": self.childrenFromSpousesPreviousMarriage,
                "manPrevious": self.childrenFromMansPreviousMarriage}