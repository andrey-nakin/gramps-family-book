# $Id$

"""Reports/Text Reports/Family Book"""

#------------------------------------------------------------------------
#
# Standard Python modules
#
#------------------------------------------------------------------------
import string
from collections import defaultdict

#------------------------------------------------------------------------
#
# Gramps modules
#
#------------------------------------------------------------------------
from gramps.gen.display.name import displayer
from gramps.gen.display.place import displayer as place_displayer
from gramps.gen.lib import Date, Event, EventType, FamilyRelType, Name, NameType, Person, Family, Place
from gramps.gen.lib import StyledText, StyledTextTag, StyledTextTagType
from gramps.gen.plug import docgen
from gramps.gen.plug.menu import BooleanOption, EnumeratedListOption, PersonOption
from gramps.gen.plug.report import Report
from gramps.gen.plug.report import utils
from gramps.gen.plug.report import MenuReportOptions
import gramps.gen.datehandler
from gramps.gen.relationship import get_relationship_calculator
from gramps.gen.const import GRAMPS_LOCALE as glocale
try:
    _trans = glocale.get_addon_translator(__file__)
except ValueError:
    _trans = glocale.translation
_ = _trans.gettext

#------------------------------------------------------------------------
#
# Constants
#
#------------------------------------------------------------------------
empty_birth = Event()
empty_birth.set_type(EventType.BIRTH)

empty_marriage = Event()
empty_marriage.set_type(EventType.MARRIAGE)


#------------------------------------------------------------------------
#
# FamilyBook report
#
#------------------------------------------------------------------------
class FamilyBook(Report):
    def __init__(self, database, options, user):
        """
        Initialize the report.

        @param database: the Gramps database instance
        @param options: instance of the Options class for this report
        @param user: a gramps.gen.user.User() instance
        """

        Report.__init__(self, database, options, user)
        self.user = user
        menu = options.menu
        self.person_id    = menu.get_option_by_name('pid').get_value()

    def write_report(self):
        """
        Build the actual report.
        """

        mark1 = docgen.IndexMark(_('Family Book'), docgen.INDEX_TYPE_TOC, 1)
        self.doc.start_paragraph('FSR-Key')
        self.doc.write_text('', mark1) # for use in a TOC in a book report
        self.doc.end_paragraph()

        self.doc.start_paragraph('FSR-Normal')
        self.doc.write_text('\\documentclass[10pt, a5paper]{report}\n')
        self.doc.write_text('\\usepackage[utf8]{inputenc}\n')
        self.doc.write_text('\\usepackage[russian]{babel}\n')
        self.doc.write_text('\\usepackage{graphicx}\n')
        self.doc.write_text('\\usepackage{wrapfig}\n')
        self.doc.write_text('\\usepackage{multicol}\n')
        self.doc.write_text('\\usepackage{tgadventor}\n')
        self.doc.write_text('\\begin{document}\n')
        self.doc.write_text('\\tableofcontents\n')
        self.doc.write_text('\\part{Персоналии}\n')
        self.doc.end_paragraph()

        self._build_obj_dict()

#        person = self.database.get_person_from_gramps_id(self.person_id)
#        (rank, ahnentafel, person_key) = self.__calc_person_key(person)
#        self.__process_person(person)

        person_list = list(self.obj_dict[Person].keys())
        person_list.sort(key = lambda x: self.obj_dict[Person][x][0])
        for person_handle in person_list:
            person = self.database.get_person_from_handle(person_handle)
            self.__process_person(person)

        self.doc.start_paragraph('FSR-Normal')
        self.doc.write_text('\\end{document}\n')
        self.doc.end_paragraph()

    def _build_obj_dict(self):
        _obj_class_list = (Person, Place)

        # setup a dictionary of the required structure
        self.obj_dict = defaultdict(lambda: defaultdict(set))
        self.bkref_dict = defaultdict(lambda: defaultdict(set))


        # initialise the dictionary to empty in case no objects of any
        # particular class are included in the web report
        for obj_class in _obj_class_list:
            self.obj_dict[obj_class] = defaultdict(set)

        ind_list = self.database.iter_person_handles()
#        ind_list = self.filter.apply(self.database, ind_list, user=self.user)

        for handle in ind_list:
            self._add_person(handle)

        # Debug output
#        log.debug("final object dictionary \n" +
#                  "".join(("%s: %s\n" % item) for item in self.obj_dict.items()))

#        log.debug("final backref dictionary \n" +
#                  "".join(("%s: %s\n" % item) for item in self.bkref_dict.items()))

    def _add_person(self, person_handle, bkref_class = None, bkref_handle = None):
        '''
        Add person_handle to the L{self.obj_dict}, and recursively all referenced objects
        '''
        # Update the dictionaries of objects back references
        if (bkref_class is not None):
            self.bkref_dict[Person][person_handle].add((bkref_class, bkref_handle, None))
        # Check if the person is already added
        if (person_handle in self.obj_dict[Person]): return
        # Add person in the dictionaries of objects
        person = self.database.get_person_from_handle(person_handle)
        if (not person): return
        if (not self.__is_person_valid(person)): return
        person_name = self.__person_name(person)
        self.obj_dict[Person][person_handle] = [person_name, person.gramps_id, len(self.obj_dict[Person])]
        # Person events
#        evt_ref_list = person.get_event_ref_list()
#        if evt_ref_list:
#            for evt_ref in evt_ref_list:
#                self._add_event(evt_ref.ref, Person, person_handle, evt_ref)
        # Person citations
#        for citation_handle in person.get_citation_list():
#            self._add_citation(citation_handle, Person, person_handle)
        # Person name citations
#        for name in [person.get_primary_name()] + \
#                        person.get_alternate_names():
#            for citation_handle in name.get_citation_list():
#                self._add_citation(citation_handle, Person, person_handle)
        # LDS Ordinance citations
#        for lds_ord in person.get_lds_ord_list():
#            for citation_handle in lds_ord.get_citation_list():
#                self._add_citation(citation_handle, Person, person_handle)
        # Attribute citations
#        for attr in person.get_attribute_list():
#            for citation_handle in attr.get_citation_list():
#                self._add_citation(citation_handle, Person, person_handle)
        # Person families
#        family_handle_list = person.get_family_handle_list()
#        if family_handle_list:
#            for family_handle in person.get_family_handle_list():
#                self._add_family(family_handle, Person, person_handle)
        # Person media
#        for media_ref in person.get_media_list():
#            media_handle = media_ref.get_reference_handle()
#            self._add_media(media_handle, Person, person_handle, media_ref)
        # Association citations
#        for assoc in person.get_person_ref_list():
#            for citation_handle in assoc.get_citation_list():
#                self._add_citation(citation_handle, Person, person_handle)
        # Addresses citations
#        for addr in person.get_address_list():
#            for citation_handle in addr.get_citation_list():
#                self._add_citation(citation_handle, Person, person_handle)

    def __person_name(self, person):
        """
        Construct person name.

        @param person: Person object.
        """
        maindenName = ''
        if int(person.get_primary_name().get_type()) == NameType.MARRIED:
            for alt_name in person.get_alternate_names():
                if int(alt_name.get_type()) == NameType.BIRTH:
                    maindenName = ' (' + alt_name.get_surname() + ')'

        return displayer.display_name(person.get_primary_name()) + maindenName

    def __is_person_valid(self, person):
        """
        Checks if person should be added to the book.

        @param person: Person object.
        """
        if person.get_primary_name().get_surname() == '':
            return False

        return True

    def __process_person(self, person):
        #!!!
        self.doc.start_paragraph('FSR-Normal')
        self.doc.write_text('\\chapter{')
        self.doc.write_text(self.__person_name(person))
        self.doc.write_text('}\n')
        self.doc.write_text('\\label{')
        self.doc.write_text(person.get_gramps_id())
        self.doc.write_text('}\n')
        self.doc.write_text(self.__person_name(person))
        self.doc.write_text('\\\\ \n')
        self.doc.write_text('Годы жизни: 1945--2015 \\\\\n')
        self.doc.write_text('Место рождения: Москва \\\\\n')
        self.doc.write_text('Место смерти: Москва \\\\\n')
        self.doc.end_paragraph()
        #!!!

#------------------------------------------------------------------------
#
# MenuReportOptions
#
#------------------------------------------------------------------------
class FamilyBookOptions(MenuReportOptions):
    """
    Defines options and provides handling interface.
    """

    RECURSE_NONE = 0
    RECURSE_SIDE = 1
    RECURSE_ALL = 2

    def __init__(self, name, dbase):
        self.__db = dbase
        self.__pid = None
        MenuReportOptions.__init__(self, name, dbase)

    def get_subject(self):
        """ Return a string that describes the subject of the report. """
        gid = self.__pid.get_value()
        person = self.__db.get_person_from_gramps_id(gid)
        return displayer.display(person)

    def add_menu_options(self, menu):

        ##########################
        category_name = _("Report Options")
        ##########################

        self.__pid = PersonOption(_("Center person"))
        self.__pid.set_help(_("The person who is used to deterine the relatives' titles"))
        menu.add_option(category_name, "pid", self.__pid)

    def make_default_style(self, default_style):
        """Make default output style for the Family Book Report."""

        #Paragraph Styles
        font = docgen.FontStyle()
        font.set_type_face(docgen.FONT_SANS_SERIF)
        font.set_size(10)
        font.set_bold(0)
        para = docgen.ParagraphStyle()
        para.set_font(font)
        para.set_description(_('The basic style used for the text display'))
        default_style.add_paragraph_style('FSR-Normal', para)

        font = docgen.FontStyle()
        font.set_type_face(docgen.FONT_SANS_SERIF)
        font.set_size(10)
        font.set_bold(0)
        para = docgen.ParagraphStyle()
        para.set_font(font)
        para.set_alignment(docgen.PARA_ALIGN_RIGHT)
        para.set_description(_('The style used for the page key on the top'))
        default_style.add_paragraph_style('FSR-Key', para)

        font = docgen.FontStyle()
        font.set_type_face(docgen.FONT_SANS_SERIF)
        font.set_size(12)
        font.set_bold(1)
        para = docgen.ParagraphStyle()
        para.set_font(font)
        para.set_description(_("The style used for names"))
        default_style.add_paragraph_style('FSR-Name', para)

        font = docgen.FontStyle()
        font.set_type_face(docgen.FONT_SANS_SERIF)
        font.set_size(12)
        font.set_bold(1)
        para = docgen.ParagraphStyle()
        para.set_font(font)
        para.set_alignment(docgen.PARA_ALIGN_CENTER)
        para.set_description(_("The style used for numbers"))
        default_style.add_paragraph_style('FSR-Number', para)

        font = docgen.FontStyle()
        font.set_type_face(docgen.FONT_SANS_SERIF)
        font.set_size(8)
        font.set_bold(0)
        para = docgen.ParagraphStyle()
        para.set_font(font)
        para.set_description(_(
            'The style used for footnotes (notes and source references)'))
        default_style.add_paragraph_style('FSR-Footnote', para)

        #Table Styles
        cell = docgen.TableCellStyle()
        cell.set_padding(0.1)
        cell.set_top_border(1)
        cell.set_left_border(1)
        cell.set_right_border(1)
        default_style.add_cell_style('FSR-HeadCell', cell)

        cell = docgen.TableCellStyle()
        cell.set_padding(0.1)
        cell.set_left_border(1)
        default_style.add_cell_style('FSR-EmptyCell', cell)

        cell = docgen.TableCellStyle()
        cell.set_padding(0.1)
        cell.set_top_border(1)
        cell.set_left_border(1)
        default_style.add_cell_style('FSR-NumberCell', cell)

        cell = docgen.TableCellStyle()
        cell.set_padding(0.1)
        cell.set_top_border(1)
        cell.set_right_border(1)
        cell.set_left_border(1)
        default_style.add_cell_style('FSR-DataCell', cell)

        cell = docgen.TableCellStyle()
        cell.set_padding(0.1)
        cell.set_top_border(1)
        default_style.add_cell_style('FSR-FootCell', cell)

        table = docgen.TableStyle()
        table.set_width(100)
        table.set_columns(3)
        table.set_column_width(0, 7)
        table.set_column_width(1, 7)
        table.set_column_width(2, 86)
        default_style.add_table_style('FSR-Table', table)
