# -*- coding: utf-8 -*-
from books.farmers.extraction.extractors.baseExtractor import BaseExtractor
from books.farmers.extractionkeys import KEYS
from interface.valuewrapper import ValueWrapper
from books.farmers.extraction.extractionExceptions import OwnerYearException, OwnerNameException
from books.farmers.extraction.extractors.birthdayExtractor import BirthdayExtractor
import shared.textUtils as textUtils
import shared.regexUtils as regexUtils
from shared.genderExtract import Gender, GenderException
import re

class OwnerExtractor(BaseExtractor):

    SEARCH_SPACE = 200
    def extract(self, text, entry):
        self.OWNER_YEAR_PATTERN = r"om(?:\.|,)\s?vuodesta\s(?P<year>\d\d\d\d)"
        self.OWNER_NAME_PATTERN = r"(?P<name>[A-ZÄ-Öa-zä-ö -]+(?:o\.s\.)?[A-ZÄ-Öa-zä-ö -]+)(?:\.|,)\ssynt" #r"(?P<name>[A-ZÄ-Öa-zä-ö -]+)(?:\.|,)\ssynt"
        self.OWNER_OPTIONS = (re.UNICODE | re.IGNORECASE)
        self.entry = entry
        self.owner_year = ValueWrapper("")
        self.first_names = ValueWrapper("")
        self.surname = ValueWrapper("")
        self.owner_gender = ValueWrapper("")
        self.birthday = {KEYS["birthDay"]:  ValueWrapper(""), KEYS["birthMonth"]:  ValueWrapper(""),
                KEYS["birthYear"]:  ValueWrapper(""), KEYS["birthLocation"]:  ValueWrapper("")}
        self._find_owner(text)
        return self._constructReturnDict()


    def _find_owner(self, text):
        text = textUtils.takeSubStrBasedOnRange(text, self.matchStartPosition, self.SEARCH_SPACE)
        self._find_owner_year(text)
        self._find_owner_name(text)
        self._find_owner_birthday(text)

    def _find_owner_birthday(self, text):
        birthdayExt = BirthdayExtractor(self.entry, self.errorLogger, self.xmlDocument)
        birthdayExt.setDependencyMatchPositionToZero()
        self.birthday = birthdayExt.extract(text, self.entry)


    def _find_owner_name(self, text):
        try:
            ownerName= regexUtils.safeSearch(self.OWNER_NAME_PATTERN, text, self.OWNER_OPTIONS)
            self.matchFinalPosition = ownerName.end()
            self._split_names(ownerName.group("name"))

        except regexUtils.RegexNoneMatchException as e:
            self.errorLogger.logError(OwnerNameException.eType, self.currentChild)
            self.first_names.error = OwnerNameException.eType
            self.surname.error = OwnerNameException.eType

    def _find_owner_gender(self, name):
        try:
            self.owner_gender.value = Gender.find_gender(name)
        except GenderException as e:
                self.errorLogger.logError(e.eType, self.currentChild)
                self.owner_gender.value = ""
                self.owner_gender.error = e.eType


    def _split_names(self, name):
        name = re.sub(r"(?:<|>|&|')", r"", name)
        names = re.split(" ", name)

        self.surname.value = names[len(names)-1].strip(" ")
        if len(names) > 1:
            for i in range(0, len(names)-1):
                if names[i].strip(" ") != "o.s.":
                    self.first_names.value += names[i].strip(" ") + " "
            self.first_names.value = self.first_names.value.strip(" ")
            self._find_owner_gender(names[1])


    def _find_owner_year(self, text):
        try:
            ownerYear= regexUtils.safeSearch(self.OWNER_YEAR_PATTERN, text, self.OWNER_OPTIONS)
            self.matchFinalPosition = ownerYear.end()
            self.owner_year.value = int(ownerYear.group("year"))
        except regexUtils.RegexNoneMatchException as e:
            self.errorLogger.logError(OwnerYearException.eType, self.currentChild)
            self.owner_year.error = OwnerYearException.eType

    def _constructReturnDict(self):
        return {KEYS["owner"] : ValueWrapper({ KEYS["ownerFrom"] : self.owner_year,
                KEYS["firstnames"] : self.first_names,
                KEYS["surname"] : self.surname,
                KEYS["gender"] : self.owner_gender,
                KEYS["ownerBirthData"] : ValueWrapper(self.birthday)
        })}
