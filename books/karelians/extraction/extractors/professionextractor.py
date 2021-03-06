from books.karelians.extraction.extractors.baseExtractor import BaseExtractor
from books.karelians.extractionkeys import KEYS
from interface.valuewrapper import ValueWrapper
from books.karelians.extraction.extractionExceptions import ProfessionException
import shared.textUtils as textUtils
import shared.regexUtils as regexUtils
import re

class ProfessionExtractor(BaseExtractor):

    SEARCH_SPACE = 60

    def extract(self, text, entry):
        self.PROFESSION_PATTERN = r"(?<profession>[a-zä-ö,\. ]*) synt"
        self.PROFESSION_OPTIONS = (re.UNICODE | re.IGNORECASE)
        self.professions = ""
        self.profession_error = False
        self._find_profession(text)
        return self._constructReturnDict()


    def _find_profession(self, text):
        text = textUtils.takeSubStrBasedOnRange(text, self.matchStartPosition, self.SEARCH_SPACE)
        try:
            #limit the search range if there is spouse keyword:
            try:
                foundSpouseWord =  regexUtils.safeSearch(r"Puol", text, self.PROFESSION_OPTIONS)
                text = textUtils.takeSubStrBasedOnRange(text, 0, foundSpouseWord.start())
            except regexUtils.RegexNoneMatchException as e:
                pass

            foundProfession= regexUtils.safeSearch(self.PROFESSION_PATTERN, text, self.PROFESSION_OPTIONS)
            self.matchFinalPosition = foundProfession.end()
            self.professions = foundProfession.group("profession")
        except regexUtils.RegexNoneMatchException as e:
            pass

    def _clean_professions(self):
        self.professions = self.professions.strip(",")
        self.professions = self.professions.strip()
        self.professions = self.professions.lstrip()

        uppercase = re.match(r"[A-ZÄ-Ö]", self.professions)
        if uppercase is not None:
            comma = self.professions.find(",")
            if comma != -1:
                self.professions = self.professions[comma:]

        self.professions = self.professions.strip(",")
        self.professions = self.professions.strip(".")
        self.professions = self.professions.strip()
        self.professions = self.professions.lstrip()
        self.professions = re.sub(r"[a-zä-ö]{1,3}(?:,|\.)\s", "", self.professions, self.PROFESSION_OPTIONS)

        if len(self.professions) < 3:
            self.professions = ""

        if self.professions == "":
            self.errorLogger.logError(ProfessionException.eType, self.currentChild)
            self.profession_error = ProfessionException.eType

    def _constructReturnDict(self):
        self._clean_professions()
        p = ValueWrapper(self.professions)
        p.error = self.profession_error
        return {KEYS["profession"] : p}