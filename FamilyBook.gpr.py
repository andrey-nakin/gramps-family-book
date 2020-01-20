register(REPORT,
    id   = 'FamilyBook',
    name = _('Family Book'),
    description = _("Produces a Latex document showing full information "
                    "about the family."),
    version = '0.1.2',
    gramps_target_version = "5.0",
    status = STABLE,
    fname = 'FamilyBook.py',
    authors = ["Andrey Nakin"],
    authors_email = ["andrey.nakin@gmail.com"],
    category = CATEGORY_TEXT,
    reportclass = 'FamilyBook',
    optionclass = 'FamilyBookOptions',
    report_modes = [REPORT_MODE_CLI, REPORT_MODE_GUI, REPORT_MODE_BKI],
    require_active = True
    )

