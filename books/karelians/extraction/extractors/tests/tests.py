from nose.tools import *
import lxml
import lxml.etree as etree
from books.karelians.extraction.extractors.nameextractor import NameExtractor
from books.karelians.extraction.extractors.professionextractor import ProfessionExtractor
from shared.exceptionlogger import ExceptionLogger
from books.karelians.extractionkeys import KEYS
from interface.valuewrapper import ValueWrapper

class TestNameExtractor:

    @classmethod
    def setup_class(self):
        self.mockXml1 = etree.Element("PERSON")
        self.mockXml1.text = "abc"
        self.mockXml1.attrib["name"] = "KALLIO, KYÖSTI VILJAMI"

        self.mockXml2 = etree.Element("PERSON")
        self.mockXml2.text = "abc"
        self.mockXml2.attrib["name"] = "jaska"

        self.eLogger = ExceptionLogger()

    def test_extract(self):
        ValueWrapper.xmlEntry = self.mockXml1
        ex = NameExtractor(self.mockXml1, self.eLogger, self.mockXml1)
        result = ex.extract(self.mockXml1.text, {"xml":self.mockXml1})
        assert_equals(result[KEYS["surname"]].value, "KALLIO")
        assert_equals(result[KEYS["firstnames"]].value, "KYÖSTI VILJAMI")

    def test_extract_noname(self):
        ValueWrapper.xmlEntry = self.mockXml2
        ex = NameExtractor(self.mockXml2, self.eLogger, self.mockXml2)
        result = ex.extract(self.mockXml2.text, {"xml":self.mockXml2})
        assert_equals(result[KEYS["surname"]].value, "jaska")
        assert_equals(result[KEYS["firstnames"]].value, "")


class TestProfessionExtractor():

    @classmethod
    def setup_class(self):
        self.mockXml1 = etree.Element("PERSON")
        self.mockXml1.text = """eläkeläinen, vaivaiskoivun kasvattaja, synt. 4. 11. -95 Viipurissa. Puol. t -63.
        Lapset: Voldemar-15. Maire -19. Syntyneet Viipurissa. Asuinp. Karjalassa:
        Viipuri, Monrepo. Muut asuinp Ahlainen. Alakylä. Olga Fokin asuu tyttärensä
        luona ja harrastaa ulkoilua."""
        self.mockXml1.attrib["name"] = "KALLIO, KYÖSTI VILJAMI"

        self.mockXml2 = etree.Element("PERSON")
        self.mockXml2.text =  """synt. 2. 10. -25 Uukuniemellä. Puol. Aune o.s. Salonen,
        emäntä, synt.'11. 11. -32 Alajärvellä. Lapset: Jouko -50, Aira
        -52, Leena -54, Veijo -55, Ansa -56. Arto -58, Helena -63, Rauni ja"""
        self.mockXml2.attrib["name"] = "KALLIO, KYÖSTI VILJAMI"
        self.eLogger = ExceptionLogger()

    def test_no_profession(self):
        ValueWrapper.xmlEntry = self.mockXml2
        ex = ProfessionExtractor(self.mockXml2, self.eLogger, self.mockXml2)
        ex.setDependencyMatchPositionToZero()
        result = ex.extract(self.mockXml2.text, {"xml":self.mockXml2})
        assert_equals(result[KEYS["profession"]].value, "")


