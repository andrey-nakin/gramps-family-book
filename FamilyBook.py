# $Id$

"""Reports/Text Reports/Family Book"""

#------------------------------------------------------------------------
#
# Standard Python modules
#
#------------------------------------------------------------------------
import string
from collections import defaultdict
from functools import partial

#------------------------------------------------------------------------
#
# Gramps modules
#
#------------------------------------------------------------------------
from gramps.gen.display.name import displayer
from gramps.gen.display.place import displayer as place_displayer
from gramps.gen.lib import Date, Event, EventType, FamilyRelType, Name, NameType, Person, Family, Place, EventRoleType
from gramps.gen.lib import StyledText, StyledTextTag, StyledTextTagType
from gramps.gen.plug import docgen
from gramps.gen.plug.menu import BooleanOption, EnumeratedListOption, PersonOption
from gramps.gen.plug.report import MenuReportOptions
from gramps.gen.plug.report import Report
from gramps.gen.plug.report import stdoptions
from gramps.gen.plug.report import utils
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
        self.citation_handles = set()

        self.set_locale(options.menu.get_option_by_name('trans').get_value())
        stdoptions.run_date_format_option(self, menu)
        self.rlocale = self._locale
        
        self.person_id    = menu.get_option_by_name('pid').get_value()
        self.document_class = 'memoir'
        self.styleName = 'default'
        self.language = 'russian'

    def write_report(self):
        """
        Build the actual report.
        """

        mark1 = docgen.IndexMark(_('Family Book'), docgen.INDEX_TYPE_TOC, 1)
        self.doc.start_paragraph('FSR-Key')
        self.doc.write_text('', mark1) # for use in a TOC in a book report
        self.doc.end_paragraph()

        self.doc.start_paragraph('FSR-Normal')
        self.doc.write_text('\\documentclass[12pt, msmallroyalvopaper, openany]{')
        self.doc.write_text(self.document_class)
        self.doc.write_text('}\n')
        self.doc.write_text('\\usepackage[utf8]{inputenc}\n')
        self.doc.write_text('\\usepackage[')
        self.doc.write_text(self.language)
        self.doc.write_text(']{babel}\n')
        self.doc.write_text('\\usepackage{graphicx}\n')
        self.doc.write_text('\\usepackage{wrapfig}\n')
        self.doc.write_text('\\usepackage{multicol}\n')
        self.doc.write_text('\\usepackage[superscript,biblabel]{cite}\n')
        self.doc.write_text('\\usepackage{enumitem}\n')
        self.doc.write_text('\\usepackage{pgfornament}\n')
        self.doc.write_text('\\setcounter{secnumdepth}{-1}\n')
        self.doc.write_text('\\chapterstyle{bringhurst}\n')
        self.doc.write_text('\\begin{document}\n')
        self.doc.write_text('\\tableofcontents\n')
        self.doc.write_text('\\tightlists\n')
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
        self.doc.write_text('\\begin{thebibliography}{99}\n')
        for cit_handle in self.citation_handles:
            self.doc.write_text(self.__make_bib_item(cit_handle))
        self.doc.write_text('\\end{thebibliography}\n')
        self.doc.write_text('\\end{document}\n')
        self.doc.end_paragraph()

    def __make_bib_item(self, cit_handle):
        cit = self.database.get_citation_from_handle(cit_handle)
        src_handle = cit.get_reference_handle()
        src = self.database.get_source_from_handle(src_handle)
        s = '\\bibitem{'
        s = s + cit.get_gramps_id()
        s = s + '} '
        s = s + src.get_title()
        if not s.endswith('.'):
            s = s + '.'
        if src.get_author() != '':
            a = src.get_author()
            if not a.endswith('.'):
                a = a + '.'
            s = s + ' {\\itshape '
            s = s + a
            s = s + '}'
        if src.get_publication_info() != '':
            pub = ' '
            pub = pub + src.get_publication_info()
            if not pub.endswith('.'):
                pub = pub + '.'
            s = s + pub
        s = s + '~// '
        s = s + cit.get_page()
        if not s.endswith('.'):
            s = s + '.'
        s = s + '\n'
        return s
        
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
        event_ref = person.get_birth_ref()
        if event_ref is None:
            return False

        return True

    def __lowercase_first_letter(self, str):
        res = str[0].lower() + str[1:]
        return res

    def __add_person_overview(self, title, value):
        if value is not None:
            self.doc.write_text('\\item[')
            self.doc.write_text(title)
            self.doc.write_text('] ')
            self.doc.write_text(value)
            self.doc.write_text('\n')

    def __get_source_cites(self, event):
        cites = ''
        for cit_handle in event.get_citation_list():
            if cit_handle:
                cit = self.database.get_citation_from_handle(cit_handle)
                if cites != '':
                    cites = cites + ', '
                cites = cites + cit.get_gramps_id()
                self.citation_handles.add(cit_handle)
        if cites != '':
            cites = '~\cite{' + cites + '}'
        return cites
        
    def __add_person_birth_death(self, person, event_ref, date_title):
        if event_ref is None:
            return None
        if event_ref.get_role() != EventRoleType.PRIMARY:
            return None
        event = self.database.get_event_from_handle(event_ref.ref)
        desc = ''
        if event.get_description():
            desc = '~(' + self.__lowercase_first_letter(event.get_description()) + ')'
        cites = self.__get_source_cites(event)
            
        dt = self.rlocale.get_date(event.get_date_object())
        if dt:
            self.__add_person_overview(date_title, '\\mbox{' + dt + '}' + desc + cites)
            desc = ''
        
    def __add_person_birth(self, person):
        self.__add_person_birth_death(person, person.get_birth_ref(), _("Born"))
    
    def __add_person_death(self, person):
        self.__add_person_birth_death(person, person.get_death_ref(), _("Died"))
            
    def __make_parents(self, person):
        s = ''
        s = s + '\\item[' + _("Father") + '] Свидригайлов Свидригайло Свидригайлович (с.~123)\n'
        s = s + '\\item[' + _("Mother") + '] Свидригайлова Свидригайла Свидригайловна (Пупкина) (с.~123)\n'
        return s
        
    def __process_person(self, person):
        self.doc.start_paragraph('FSR-Normal')
        self.doc.write_text('\\chapter{')
        self.doc.write_text(self.__person_name(person))
        self.doc.write_text('}\n')
        self.doc.write_text('\\label{')
        self.doc.write_text(person.get_gramps_id())
        self.doc.write_text('}\n')
        self.doc.write_text('\\begin{description}[style=multiline,font=\\normalfont\\scshape]\n')
        
        self.__add_person_birth(person)
        self.__add_person_death(person)
            
        self.doc.write_text(self.__make_parents(person))
        self.doc.write_text('\\end{description}\n\n')

        s = '\\begin{center}\n'
        s = s + '\\noindent \\pgfornament[width=0.618\\textwidth]{88}\n'
        s = s + '\\medskip\n'
        s = s + '\\end{center}\n\n'
        
        s = s + 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.'
        s = s + '\n\n'
        
        self.doc.write_text(s)
        self.doc.end_paragraph()
        

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
        self.__add_report_options(menu)
        self.__add_report_display(menu)

    def __add_report_options(self, menu):
        ##########################
        category_name = _("Report Options")
        ##########################

        self.__pid = PersonOption(_("Center person"))
        self.__pid.set_help(_("The person who is used to deterine the relatives' titles"))
        menu.add_option(category_name, "pid", self.__pid)

    def __add_report_display(self, menu):
        """
        How to display names, datyes, ...
        """
        category_name = _("Display")
        addopt = partial(menu.add_option, category_name)

        stdoptions.add_name_format_option(menu, category_name)

        locale_opt = stdoptions.add_localization_option(menu, category_name)
        stdoptions.add_date_format_option(menu, category_name, locale_opt)

#        stdoptions.add_gramps_id_option(menu, category_name)

#        birthorder = BooleanOption(
#            _('Sort all children in birth order'), False)
#        birthorder.set_help(
#            _('Whether to display children in birth order or in entry order?'))
#        addopt("birthorder", birthorder)

#        coordinates = BooleanOption(
#            _('Do we display coordinates in the places list?'), False)
#        coordinates.set_help(
#            _('Whether to display latitude/longitude in the places list?'))
#        addopt("coordinates", coordinates)

#        reference_sort = BooleanOption(
#            _('Sort places references either by date or by name'), False)
#        reference_sort.set_help(
#            _('Sort the places references by date or by name.'
#              ' Not set means by date.'))
#        addopt("reference_sort", reference_sort)

#        self.__graphgens = NumberOption(_("Graph generations"), 4, 2, 10)
#        self.__graphgens.set_help(_("The number of generations to include in "
#                                    "the ancestor graph"))
#        addopt("graphgens", self.__graphgens)
#        self.__graph_changed()

#        notes = BooleanOption(
#            _('Include narrative notes just after name, gender'), True)
#        notes.set_help(
#            _('Include narrative notes just after name, gender and'
#              ' age at death (default) or include them just before'
#              ' attributes.'))
#        addopt("notes", notes)
        
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
