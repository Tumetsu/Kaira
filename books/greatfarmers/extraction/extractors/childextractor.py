from books.greatfarmers.extraction.extractors.baseExtractor import BaseExtractor
from books.greatfarmers.extractionkeys import KEYS
from interface.valuewrapper import ValueWrapper
from books.greatfarmers.extraction.extractionExceptions import NoChildrenException, MultipleMarriagesException
from shared import regexUtils
from shared import textUtils
import re
import regex
from shared.geo.geocoding import GeoCoder, LocationNotFound
from shared.genderExtract import Gender, GenderException


class ChildExtractor(BaseExtractor):
    geocoder = GeoCoder()
    #[A-Zä-Ö\s-]+\sja\s[A-Zä-Ö\s-]+-\d\d\D

    def extract(self, text, entry):

        self.CHILD_PATTERN = r"(?:Lapset|tytär|poika|tyttäret|pojat)(;|:)(?P<children>.*?)(?:\.|Tilal{s<=1}|Edelli{s<=1}|hänen{s<=1}|joka{s<=1}|emännän{s<=1}|isännän{s<=1})"
        self.CHILD_OPTIONS = (re.UNICODE | re.IGNORECASE)

        self.MANY_MARRIAGE_PATTERN = r"(toisesta|ensimmäisestä|aikaisemmasta|edellisestä|nykyisestä|avioliitosta)"
        self.many_marriages = False
        self.SPLIT_PATTERN1 = r"(?P<child>[A-ZÄ-Öa-zä-ö\d\s-]{3,})"
        self.NAME_PATTERN = r"^(?P<name>[a-zä-ö\s-]+)"
        self.YEAR_PATTERN = r"(?P<year>(\d\d))"
        self.LOCATION_PATTERN = r"\d\d\s(?P<location>[a-zä-ö\s-]+$)"
        self.SPLIT_OPTIONS1 = (re.UNICODE | re.IGNORECASE)
        self.children_str = ""
        self.child_list = []
        self.child_error = False
        self.girls = 0
        self._check_many_marriages(text)
        self._find_children(text)

        return self._constructReturnDict()

    def _find_children(self, text):
        text = re.sub(r"sekä", ",",text)

        try:
            foundChildren= regexUtils.safeSearch(self.CHILD_PATTERN, text, self.CHILD_OPTIONS)
            self.matchFinalPosition = foundChildren.end()
            self.children_str = foundChildren.group("children")
            self._clean_children()
            self._split_children()

        except regexUtils.RegexNoneMatchException as e:
            self.errorLogger.logError(NoChildrenException.eType, self.currentChild)
            self.child_error = NoChildrenException.eType

    def _check_many_marriages(self, text):
        marriage = regexUtils.search(self.MANY_MARRIAGE_PATTERN, text, self.CHILD_OPTIONS)
        if marriage is not None:
            self.many_marriages = True
            self.errorLogger.logError(MultipleMarriagesException.eType, self.currentChild)


    def _clean_children(self):
        self.children_str = self.children_str.strip(",")
        self.children_str = self.children_str.strip(".")
        self.children_str = self.children_str.strip()

    def _split_children(self):
        foundChildren = regexUtils.regexIter(self.SPLIT_PATTERN1, self.children_str, self.SPLIT_OPTIONS1)
        count = 0
        for m in foundChildren:
            count += 1

            #check if there is "ja" word as separator such as "Seppo -41 ja Jaakko -32.
            ja_word = regexUtils.search(r"\sja\s",m.group("child"))
            if ja_word is not None:
                firstChild = self._process_child(m.group("child")[0:ja_word.start()])
                secondChild = self._process_child(m.group("child")[ja_word.end():])
                self._twins_year_handler(firstChild, secondChild)
            else:
                self._process_child(m.group("child"))

    def _twins_year_handler(self, first, second):
        #if there is twins, the book doesn't explicitly define birthyear for first one.
        #therefore copy second child's value to first one
        if first is not None and second is not None:
            if first.value["birthYear"].value == "" and second.value["birthYear"].value != "":
                first.value["birthYear"].value = second.value["birthYear"].value


    def _process_child(self, child):

        try:
            name = regexUtils.safeSearch(self.NAME_PATTERN, child, self.CHILD_OPTIONS).group("name")
            name = name.strip()
            name = name.strip("-")
            name = name.strip(" ")
            try:
                gender = ValueWrapper(Gender.find_gender(name))
            except GenderException as e:
                self.errorLogger.logError(e.eType, self.currentChild)
                gender = ValueWrapper("")
                gender.error = e.eType


            if gender.value == "Female":
                self.girls += 1

            try:
                yearMatch = regexUtils.safeSearch(self.YEAR_PATTERN, child, self.CHILD_OPTIONS)
                year = yearMatch.group("year")
                if float(year) <70:
                    year = "19" + year
                else:
                    year = "18" + year
            except regexUtils.RegexNoneMatchException:
                year = ""
            result = ValueWrapper({"name" : ValueWrapper(name),
                                                 "gender" : gender, "birthYear" : ValueWrapper(year)})
            self.child_list.append(result)
            return result
        except regexUtils.RegexNoneMatchException:
            pass





    def _constructReturnDict(self):
        c = ValueWrapper(self.child_list)
        c.error = self.child_error
        return {KEYS["manymarriages"] : ValueWrapper(self.many_marriages), KEYS["children"] : c, KEYS["childCount"] : ValueWrapper(len(self.child_list)),
                 KEYS["girlCount"] : ValueWrapper(self.girls),  KEYS["boyCount"] : ValueWrapper(len(self.child_list) - self.girls)}
