# -*- coding: utf-8 -*-

from books.soldiers import readData
from books.soldiers.extraction.dataExtraction import DataExtraction
from books.soldiers.extraction.extractionExceptions import *
from shared.exceptionlogger import ExceptionLogger
from interface.valuewrapper import ValueWrapper
from interface.processdatainterface import ProcessDataInterface
from books.soldiers.extractionkeys import KEYS

XMLPATH = "../xmldata/"
CSVPATH = "../csv/"

class ProcessData(ProcessDataInterface):

    def __init__(self, callback):
        self.dataFilename = ""
        self.csvBuilder = None
        self.extractor = None
        self.chunkerCheck = None
        self.errors = 0
        self.count = 0
        self.xmlDataDocument = None
        self.readDataEntries = []
        self.processUpdateCallbackFunction = None
        self.processUpdateCallbackFunction = callback

    #TODO: Nimeä uudestaan kuvaamaan että se palauttaa valmiin tuloksen?
    def startExtractionProcess(self, xmlDocument, filePath):
        self.xmlDataDocument = xmlDocument
        self.dataFilename = filePath
        self._initProcess()
        self._processAllEntries()
        self._finishProcess()
        return {"errors": self.errorLogger.getErrors(), "entries": self.readDataEntries, "xmlDocument": self.xmlDataDocument,
                "file": filePath}


    def extractOne(self, xmlEntry):
        """Can be used to extract only one entry after the main file"""
        ValueWrapper.reset_id_counter()
        entry = self._createEntry(xmlEntry)
        ValueWrapper.xmlEntry = xmlEntry
        try:
            personEntryDict = self.extractor.extraction(entry["xml"].text, entry, self.errorLogger)
            entry["extractionResults"] = personEntryDict
        except ExtractionException as e:
            pass

        return entry

    def _initProcess(self):
        self.errors = 0
        self.count = 0
        #self.csvBuilder = ResultCsvBuilder()
        #self.csvBuilder.openCsv(filePath)

        self.errorLogger = ExceptionLogger()

        #self.xmlDataDocument = readData.getXMLroot(filePath)

        self.extractor = DataExtraction(self.xmlDataDocument)
        self.xmlDataDocumentLen = len(self.xmlDataDocument)
        print ("XML file elements: " + str(len(self.xmlDataDocument)))

    def _processAllEntries(self):
        i = 0
        ValueWrapper.reset_id_counter()
        for child in self.xmlDataDocument:
            entry = self._createEntry(child)
            ValueWrapper.xmlEntry = child
            try:
                self._processEntry(entry)
            except ExtractionException as e:
                self.readDataEntries.append(entry)    #TODO: Probably better idea to pass dict with keys with empty fields?
                self._handleExtractionErrorLogging(exception=e, entry=entry)

            i +=1
            ValueWrapper.reset_id_counter() #Resets the id-generator for each datafield of entry
            self.processUpdateCallbackFunction(i, self.xmlDataDocumentLen)



    def _processEntry(self, entry):
        personEntryDict = self.extractor.extraction(entry["xml"].text, entry, self.errorLogger)
        entry["extractionResults"] = personEntryDict
        self.readDataEntries.append(entry)
        #self.csvBuilder.writeRow(personEntryDict)
        self.count +=1
        return entry

    def _createEntry(self, xmlEntry):
        return {"xml": xmlEntry, "extractionResults" : self._createResultTemplate()}

    def _createResultTemplate(self):
        return {KEYS["surname"] : "", KEYS["firstnames"] : "", KEYS["birthDay"]: "",
               KEYS["birthMonth"] : "", KEYS["birthYear"] : "", KEYS["birthLocation"] : "",
               KEYS["profession"] : "", KEYS["address"] : "", KEYS["deathDay"] : "",
               KEYS["deathMonth"]: "", KEYS["deathYear"]: "", KEYS["kaatunut"]: "",
               KEYS["deathLocation"]: "", KEYS["talvisota"]: "", KEYS["talvisotaregiments"]: "",
               KEYS["jatkosota"]: "", KEYS["jatkosotaregiments"]: "",KEYS["rank"]: "",
               KEYS["kotiutusDay"]: "", KEYS["kotiutusMonth"]: "", KEYS["kotiutusYear"]: "",
               KEYS["kotiutusPlace"]: "", KEYS["medals"]: "",KEYS["hobbies"]: "",
               KEYS["hasSpouse"]: "", KEYS["children"]: "", KEYS["childCount"]: ""}

    def _handleExtractionErrorLogging(self, exception, entry):
        self.errorLogger.logError(exception.eType, entry)
        self.errors +=1
        self.count +=1

    def _finishProcess(self):
        self._printStatistics()
        #self.csvBuilder.closeCsv()


    def _printStatistics(self):
        print ("Errors encountered: " + str(self.errors) + "/" + str(self.count))
        self.errorLogger.printErrorBreakdown()


