import sys, os, inspect, platform
import copy

from PyQt5.QtCore import QRegExp, Qt
from PyQt5 import QtGui, QtWidgets

version = "3.2"
appName =  "ThermAP"

DBnames = []          # List of database names
DBtitles = []         # List of database titles
curDBidx = 0          # Index of the current database
Elems = []            # List of the Elements in current database
Species = []          # List of the Species in current database

# - Element class ------------------------------------------------------------

class Element(object):
    """ Elem' contains information about each element """
    def __init__(self, name="", state = '', So_298=0.0):
        self.name = name             # elem name
        self.state = state           # elem state (= L,S,G)
        self.So_298 = So_298         # entropy of element in its standard state


# - Specie class ------------------------------------------------------------

class Specie(object):
    """ Specie contains information about each species """

    def __init__(self, col=0, name="", charge=0.0, g=0.0, s=0.0, DGaq=0.0, elem=[], coef=0.0):
        self.col = col               # column where the specie is displayed in inputDlg
        self.name = name             # specie name
        self.charge = charge         # charge
        self.g = g                   # Gibbs energy contribution
        self.s = s                   # entropy contribution
        self.DGaq = DGaq             # Gibbs energy of the specie dissolved in water
        self.elem = elem             # list of elements (name, number) in specie
        self.coef = coef

# ----------------------------------------------------------------------------

def IsNumber(s):
    """
       Return True if 's' can be converted in a float
    """
    try:
        v = float(s)
        return True
    except ValueError:
        return False


def getSpecie(name):
    """ Return the Specie which name is "name"

    :param name: a String containing the name of the Specie
    :return: the required Specie or None if not found.
    """
    for spec in Species:
        if spec.name == name:
            return spec
    return None


def lookForDB():
    """ Look for database files

        There are two files for each database ElemeDBn.txt and SpeciesDBn.txt
    :return: An error message (="" if no error).
    """
    done = False
    msg = ""
    i = 0
    while not done:
        dbfilnam = "SpeciesDB{}.txt".format(i+1)
        path = os.path.join(progpath, dbfilnam)
        if os.path.exists(path):
            with open(path) as f:
                lines = f.read().splitlines()
                if len(lines):
                    title = ""
                    for l, lin in enumerate(lines):
                        if l == 0:
                           DBnames.append(lines[0].strip("# "))
                           i += 1
                        else:
                            lin = lin.strip("# ")
                            if lin == "" or lin.startswith("List of species"):
                                DBtitles.append(title)
                                break
                            else:
                                title += "{}<br>".format(lin)
                else:
                    msg = "No data in the file {}".format(dbfilnam)
                    done = True
        else:
            done = True
    if i == 0:
        msg = "No database were found !"
    if msg == "":
        return True
    QtWidgets.QMessageBox.critical(None, appName, msg)
    return False


def loadElems(filename):
    """

    :param filename:
    :return:
    """
    global Elems
    Elems = []
    err = 0
    l = 0
    try:
        for line in open(filename):
            l += 1
            lin = line.strip()
            if len(lin):                          # is it an empty line ?
                if lin[0] != '#':
                    items = lin.split()
                    n = len(items)
                    if n != 3:
                        err = 1
                        errmsg = "The number of items in line {} must be 3".format(l)
                        break
                    elem = Element()
                    for i, item in enumerate(items):
                        item.strip()
                        if i == 0:
                           elem.name = item
                        elif i == 1:
                            if item in ['S', 'G', 'L']:
                                elem.state = item
                            else:
                                err = 1
                                break
                        elif i == 2:
                            if IsNumber(item):
                                elem.So_298 = float(item)
                            else:
                                err = 1
                                break
                    if err:
                        errmsg = "Bad format for {0} in line {1}".format(item, l)
                        break
                    else:
                        Elems.append(elem)
    except IOError as ioerr:
        err = 1
        errmsg = str(ioerr)
    if err:
        msg = "Error in reading Element data file\n"
        msg += errmsg
        QtWidgets.QMessageBox.critical(None, appName, msg)
        return False
    return True



def loadSpecies(filename):
    """

    :param filename:
    :return:
    """
    global Species
    Species = []
    err = 0
    try:
        for line in open(filename):
            lin = line.strip()
            if len(lin):                          # is it an empty line ?
                if lin[0] != '#':
                    items = lin.split()
                    spec = Specie()
                    for i, item in enumerate(items):
                        item.strip()
                        if i == 0:
                            if IsNumber(item):
                               spec.col = int(item)
                            else:
                                err = 1
                                break
                        if i == 1:
                           spec.name = item
                        elif i == 2:
                            if IsNumber(item):
                                spec.charge = float(item)
                            else:
                                err = 1
                                break
                        elif i == 3:
                            if IsNumber(item):
                                spec.g = float(item) * 1000
                            else:
                                err = 1
                                break
                        elif i == 4:
                            if IsNumber(item):
                                spec.s = float(item)
                            else:
                                err = 1
                                break
                        elif i == 5:
                            if IsNumber(item):
                                spec.DGaq = float(item) * 1000
                            else:
                                err = 1
                                break
                    if err:
                        errmsg = "Bad format for {0} in line {1}".format(item, i + 1)
                        break
                    else:
                        Species.append(spec)
    except IOError as ioerr:
        errmsg = str(ioerr)
        err = 1
    if err:
        msg = "Error in reading Specie data file\n"
        msg += errmsg
        QtWidgets.QMessageBox.critical(None, appName, msg)
        return False
    return True


def addElem2Specie():
    """ Build the list of element names in Elems

    :return: a boolean = True if not error
    """
    elnames = []
    for elem in Elems:
        elnames.append(elem.name)
    # Build the list of elements for each specie
    for speci in Species:
        elemlst = []
        nam = speci.name
        if nam.endswith("2+") or nam.endswith("3+") or nam.endswith("4+"):
            nam = nam[:-2]
        elif nam.endswith('+') or nam.endswith('-'):
            nam = nam[:-1]
        if nam in elnames:
            # It is easy, there is only one element
            elemlst.append((nam, 1))
        else:
            while len(nam):
                find = False
                for elnam in elnames:
                    if nam.startswith(elnam):
                        l = len(elnam)
                        if len(nam) > l and IsNumber(nam[l]):
                            n = int(nam[l])
                            nam = nam[l + 1:]
                        else:
                            n = 1
                            nam = nam[l:]
                        elemlst.append((elnam, n))
                        find = True
                        break
                if not find:
                    msg = "Missing element required by {0} specie".format(speci.name)
                    QtWidgets.QMessageBox.critical(None, appName, msg)
                    return False
        speci.elem = copy.copy(elemlst)
    return True


def initDataBase():
    """ Initialize data on element and species

    :return: a boolean = True if ok.
    """
    if len(Elems):
        if not addElem2Specie():
            return False
    return True


def aboutThermAP():
    """ Open ThermAP_presentation.pdf in the Web Browser.

    :return: nothing.
    """
    import webbrowser
    url = os.path.join(progpath, "ThermAP_presentation.pdf")
    if platform.system() == "Darwin":
        webbrowser._browsers['safari'][1].open(url)
    else:
        webbrowser.open(url)


# - QHLine class ------------------------------------------------------------

class QHLine(QtWidgets.QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QtWidgets.QFrame.HLine)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)


# - initDlg class ------------------------------------------------------------

class initDlg(QtWidgets.QDialog):
    def __init__(self, parent=None):
        """ Init dialog.

            self.label.setFont(QFont('Arial', 10))
            self.label.setFont.setStyleSheet("font-weight: bold")
            label.setText("x<sub>1</sub><sup>2</sup>")
        """
        super (initDlg, self).__init__(parent)
        self.setWindowTitle(appName)
        self.seldbno = 0

        L1Llab = QtWidgets.QLabel("ThermAP")
        font = QtGui.QFont('Arial', 24, QtGui.QFont.Bold)
        font.setItalic(True)
        L1Llab.setFont(font)

        L1Rlab = QtWidgets.QLabel("Version {} - April 2021".format(version))
        L1Rlab.setFont(QtGui.QFont('Arial', 14))
        L1Rlab.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        L2lab = QtWidgets.QLabel("Applied Predictive Thermodynamics")
        L2lab.setFont(QtGui.QFont('Arial', 16))

        Welcome1lab = QtWidgets.QLabel("Welcome to the ThermAP program!")
        Welcome1lab.setFont(QtGui.QFont('Arial', 16, QtGui.QFont.Bold))
        Welcome1lab.setStyleSheet("color: blue;")
        Welcome1lab.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)

        sWelcome2 = " Predicting standard thermodynamic properties for complex oxides (298 K, 1 bar) \n"
        sWelcome2 += " from their chemical composition using ion-refined contributions "
        Welcome2lab = QtWidgets.QLabel(sWelcome2)
        font = QtGui.QFont('Arial', 14)
        font.setItalic(True)
        Welcome2lab.setFont(font)
        Welcome2lab.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        #Welcome2lab.setWordWrap(True)

        sAuthorsL = "All rights reserved\n"
        sAuthorsL += "Copyright: Christophe Drouet, Pierre Alphonse\n"
        sAuthorsL += "CIRIMAT (UMR CNRS 5085), University of Toulouse, France"
        AuthorsLlab =  QtWidgets.QLabel(sAuthorsL)
        AuthorsLlab.setWordWrap(True)

        sAuthorsR = 'Contact: <span style="color:blue; text-decoration:underline">christophe.drouet@cirimat.fr</span>'
        AuthorsRlab = QtWidgets.QLabel(sAuthorsR)
        AuthorsRlab.setAlignment(Qt.AlignRight | Qt.AlignBottom)

        sCitation1 = "<u>Program citation:</u> C. Drouet, P. Alphonse, ThermAP, "
        sCitation1 += '<span style="color:blue; text-decoration:underline">www.christophedrouet.com/thermAP.html</span>'
        sCitation1 += ", Toulouse, France (2015)"
        sCitation2 = "<u>Initial reference:</u> C. Drouet, Journal of Chemical Thermodynamics 81 (2015) 143-159."
        Citationlab1 = QtWidgets.QLabel(sCitation1)
        Citationlab1.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        Citationlab2 = QtWidgets.QLabel(sCitation2)
        Citationlab2.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        aboutbut = QtWidgets.QPushButton("ThermAP overview")
        aboutbut.setFont(QtGui.QFont('Arial', 16, QtGui.QFont.Bold))
        dbButtons = []
        for dbnam in DBnames:
            butnam = " Access the {} database ".format(dbnam)
            but = QtWidgets.QPushButton(butnam)
            but.setFont(QtGui.QFont('Arial', 16))
            dbButtons.append(but)

        # set the layout
        tophbox = QtWidgets.QHBoxLayout()
        tophbox.addWidget(L1Llab)
        tophbox.addWidget(L1Rlab)
        l2hbox = QtWidgets.QHBoxLayout()
        l2hbox.addWidget(L2lab)
        welcomevbox = QtWidgets.QVBoxLayout()
        welcomevbox.addWidget(Welcome1lab)
        welcomevbox.addSpacing(20)
        welcomevbox.addWidget(Welcome2lab)

        buttonvbox = QtWidgets.QVBoxLayout()
        buttonhbox = QtWidgets.QHBoxLayout()
        buttonhbox.addStretch(1)
        buttonhbox.addWidget(aboutbut)
        buttonhbox.addStretch(1)
        buttonvbox.addLayout(buttonhbox)
        for but in dbButtons:
            buttonhbox = QtWidgets.QHBoxLayout()
            buttonhbox.addStretch(1)
            buttonhbox.addWidget(but)
            buttonhbox.addStretch(1)
            buttonvbox.addLayout(buttonhbox)

        authorhbox = QtWidgets.QHBoxLayout()
        authorhbox.addWidget(AuthorsLlab)
        authorhbox.addWidget(AuthorsRlab)
        citationvbox = QtWidgets.QVBoxLayout()
        citationvbox.addWidget(Citationlab1)
        citationvbox.addWidget(Citationlab2)
        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(tophbox)
        vbox.addLayout(l2hbox)
        vbox.addSpacing(20)
        vbox.addLayout(welcomevbox)
        vbox.addSpacing(20)
        vbox.addLayout(buttonvbox)
        vbox.addSpacing(20)
        vbox.addLayout(authorhbox)
        vbox.addSpacing(10)
        vbox.addLayout(citationvbox)
        self.setLayout(vbox)

        aboutbut.clicked.connect(aboutThermAP)
        for but in dbButtons:
            but.clicked.connect(self.setdbno)


    def setdbno(self):
        source = self.sender()
        for i, dbnam in enumerate(DBnames):
            if dbnam in source.text():
                self.seldbno = i+1
                break
        self.accept()



# - inputDlg class ------------------------------------------------------------

class inputDlg(QtWidgets.QDialog):
    def __init__(self, parent=None):
        """ Input dialog.
        """
        super (inputDlg, self).__init__(parent)
        self.setWindowTitle(appName)

        # Save current values of species in 'currdata.txt'
        fo = open('currdata.txt', 'w')
        fo.write('Name\tcharge\t   g(i)\t   s(i)\t   DG(aq)\tElements\n')
        for specie in Species:
            lin = ""
            lin += '{:7s}\t'.format(specie.name)
            lin += '{:>+3.0f}\t'.format(specie.charge)
            lin += '{:>+7.2f}\t'.format(specie.g/1000.0)
            lin += '{:>+7.2f}\t'.format(specie.s)
            lin += '{:>+9.2f}\t'.format(specie.DGaq/1000.0)
            for i, item in enumerate(specie.elem):
                lin += '{0},{1}'.format(item[0], item[1])
                if i < len(specie.elem)-1:
                    lin +='; '
            lin += '\n'
            fo.write(lin)
        fo.close()

        titlelab = QtWidgets.QLabel(DBtitles[curDBidx])
        titlelab.setFont(QtGui.QFont('Arial', 14, QtGui.QFont.Bold))
        titlelab.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        titlelab.setWordWrap(True)

        font = QtGui.QFont('Arial', 12)
        regex = QRegExp("[0-9][.0-9][0-9][0-9]")
        validator = QtGui.QRegExpValidator(regex)

        lablst = []
        self.inputlst = []
        for i, spec in enumerate(Species):
            if spec.name.endswith("4+"):
                sSpec = spec.name[:-2] + "<sup>4+</sup>"
            if spec.name.endswith("3+"):
                sSpec = spec.name[:-2] + "<sup>3+</sup>"
            elif spec.name.endswith("2+"):
                sSpec = spec.name[:-2] + "<sup>2+</sup>"
            elif spec.name.endswith("+"):
                sSpec = spec.name[:-1] + "<sup>+</sup>"
            elif spec.name.endswith("-"):
                sSpec = spec.name[:-1] + "<sup>-</sup>"
            else:
                sSpec = spec.name
                if spec.name == "PO4":
                    sSpec += "<sup>3-</sup>"
                elif spec.name == "H+":
                    sSpec = "HPO<sub>4</sub><sup>2-</sup>  (<sup>*</sup>)"
                elif spec.name == "H2O":
                    sSpec = "H<sub>2</sub>O"
                else:
                    sSpec = "?"
            lab = QtWidgets.QLabel(sSpec)
            lab.setFont(font)
            lablst.append(lab)
            inp = QtWidgets.QLineEdit(self)
            inp.setFont(font)
            inp.setValidator(validator)
            inp.setText("")
            #inp.setText(str(Species[i].coef))
            self.inputlst.append(inp)

        sfoot = "<sup>*</sup>the HPO<sub>4</sub><sup>2-</sup> ion being treated in "
        sfoot += "this additive model as the sum PO<sub>4</sub><sup>3-</sup>  +  H<sup>+</sup>"
        footlab = QtWidgets.QLabel(sfoot)

        computeButton = QtWidgets.QPushButton("Compute")
        computeButton.setFont(font)
        clearButton = QtWidgets.QPushButton("Clear")
        clearButton.setFont(font)
        homeButton = QtWidgets.QPushButton("HOME")
        homeButton.setFont(QtGui.QFont('Arial', 12, QtGui.QFont.Bold))
        aboutButton = QtWidgets.QPushButton("About")
        aboutButton.setFont(font)
        quitButton = QtWidgets.QPushButton("Quit")
        quitButton.setFont(font)

        # set the layout
        titlevbox = QtWidgets.QVBoxLayout()
        titlevbox.addWidget(titlelab)
        titlevbox.addWidget(QHLine())

        # These Grids contain the label and input text for each specie
        gridbox1 = QtWidgets.QGridLayout()
        gridbox2 = QtWidgets.QGridLayout()
        gridbox3 = QtWidgets.QGridLayout()
        # addWidget (widget, row, column[, alignment=0])
        n1 = n2 = n3 = 0
        for i, spec in enumerate(Species):
            # First column
            if spec.col == 1:
                gridbox1.addWidget(lablst[i], i, 0)
                gridbox1.addWidget(self.inputlst[i], i, 1)
                n1 += 1
            # 2nd column
            if spec.col == 2:
                gridbox2.addWidget(lablst[i], n2, 0)
                gridbox2.addWidget(self.inputlst[i], n2, 1)
                n2 += 1
            # 3rd column
            if spec.col == 3:
                if spec.name == "H2O":
                    # Separate H2O from anions with an empty line
                    emptylab = QtWidgets.QLabel(" ")
                    gridbox3.addWidget(emptylab, n3, 0)
                    gridbox3.addWidget(lablst[i], n3+1, 0)
                    gridbox3.addWidget(self.inputlst[i], n3+1, 1)
                else:
                    gridbox3.addWidget(lablst[i], n3, 0)
                    gridbox3.addWidget(self.inputlst[i], n3, 1)
                n3 += 1

        gridbox1.setContentsMargins(20, 0, 50, 0)
        gridbox2.setContentsMargins(20, 0, 50, 0)
        gridbox3.setContentsMargins(0, 0, 20, 0)
        col1vbox = QtWidgets.QVBoxLayout()
        col1vbox.addLayout(gridbox1)
        col1vbox.addStretch()
        col2vbox = QtWidgets.QVBoxLayout()
        col2vbox.addLayout(gridbox2)
        col2vbox.addStretch()
        col3vbox = QtWidgets.QVBoxLayout()
        col3vbox.addLayout(gridbox3)
        col3vbox.addStretch()

        colshbox = QtWidgets.QHBoxLayout()
        colshbox.addLayout(col1vbox)
        colshbox.addStretch()
        colshbox.addLayout(col2vbox)
        colshbox.addStretch()
        colshbox.addLayout(col3vbox)

        btnhbox = QtWidgets.QHBoxLayout()
        btnhbox.addWidget(computeButton)
        btnhbox.addWidget(clearButton)
        btnhbox.addWidget(homeButton)
        btnhbox.addWidget(aboutButton)
        btnhbox.addWidget(quitButton)

        footvbox = QtWidgets.QVBoxLayout()
        footvbox.addSpacing(20)
        footvbox.addWidget(footlab)
        footvbox.addWidget(QHLine())

        mainvbox = QtWidgets.QVBoxLayout()
        mainvbox.addLayout(titlevbox)
        mainvbox.addLayout(colshbox)
        mainvbox.addLayout(footvbox)
        mainvbox.addLayout(btnhbox)
        self.setLayout(mainvbox)

        computeButton.clicked.connect(self.compute)
        clearButton.clicked.connect(self.clear)
        homeButton.clicked.connect(self.accept)
        aboutButton.clicked.connect(self.about)
        quitButton.clicked.connect(self.reject)


    def getSoElem(self, name):
        for elem in Elems:
            if elem.name == name:
                return elem.So_298
        return None


    def clear(self):
        """ Clear all the coefficient values

        :return: Nothing
        """
        for inp in self.inputlst:
            inp.setText("")


    def about(self):
        aboutThermAP()



    def compute(self, event):
        """
            Expected results for fluorapatite Ca(10)PO4(6)F(2):
            DGf = -12836 kJ/mol
            DHf = -13598 kJ/mol
            DSf =  -2557 J/mol/K
            So  =    770 J/mol.K
            pKsp = 109
        """
        errmsg = ''
        # Retrieve the value of coefficients
        for i, spec in enumerate(Species):
            if IsNumber(self.inputlst[i].text()):
                spec.coef = float(self.inputlst[i].text())
            else:
                spec.coef = 0.0
        # Check electroneutrality
        S = 0.0
        for specie in Species:
            if specie.coef != 0.0:
                S += specie.coef * specie.charge
        if abs(S) > 1e-10:
            errmsg = 'Check the electroneutrality !'
        else:
            Sg = 0.0  # Sum of G for species
            Ss = 0.0  # Sum of S for species
            SSelem = 0.0  # Sum of S for elements
            SDGaq = 0.0
            aqflag = False  # if True DGdisso is calculated
            for specie in Species:
                if aqflag == False and specie.coef == 0:
                    if specie.name == 'H+':
                        aqflag = True
                Sg += specie.coef * specie.g
                Ss += specie.coef * specie.s
                SDGaq += specie.coef * specie.DGaq
                S = 0.0
                for elem in specie.elem:
                    Selm = self.getSoElem(elem[0])
                    if Selm is not None:
                        S += Selm * elem[1]
                    else:
                        errmsg = 'Unknown element: ' + elem[0]
                        break
                if errmsg:
                    break
                else:
                    SSelem += specie.coef * S
            DS = Ss - SSelem
            DH = Sg + 298 * DS
            if aqflag:
                DGdisso = SDGaq - Sg
                logKsp = -1.0 * DGdisso / (2.303 * 8.314 * 298)

        if errmsg:
            QtWidgets.QMessageBox.critical(self, appName, errmsg)
        else:
            # Build stresults
            st = '<TABLE BORDER=0 CELLSPACING=5 CELLPADDING=1>'
            st += '<TR>'
            st += '<TD WIDTH=150>  Estimated &Delta;G<sub>f</sub><sup>o</sup> :</TD>'
            st += '<TD ALIGN="right"> {:.0f}</TD>'.format(Sg/1000.0)
            st += '<TD> kJ.mol<sup>-1</sup></TD>'
            st += '</TR>'
            st += '<TR>'
            st += '<TD>   Estimated &Delta;H<sub>f</sub><sup>o</sup> : </TD>'
            st += '<TD ALIGN="right"> {:.0f}</TD>'.format(DH/1000.0)
            st += '<TD> kJ.mol<sup>-1</sup></TD>'
            st += '</TR>'
            st += '<TR>'
            st += '<TD>   Estimated &Delta;S<sub>f</sub><sup>o</sup> : </TD>'
            st += '<TD ALIGN="right"> {:.0f}</TD>'.format(DS)
            st += '<TD> J.mol<sup>-1</sup>.K<sup>-1</sup></TD>'
            st += '</TR>'
            st += '<TR>'
            st += '<TD>   Estimated S<sup>o</sup> : </TD>'
            st += '<TD ALIGN="right"> {:.0f}</TD>'.format(Ss)
            st += '<TD> J.mol<sup>-1</sup>.K<sup>-1</sup></TD>'
            st += '</TR>'
            if DBnames[curDBidx] != "Apatites":
                st += '</TABLE>'
                st += '<br><br>'
            else:
                if aqflag:
                    st += '<TR>'
                    st += '<TD>  </TD>'
                    st += '</TR>'
                    st += '<TR>'
                    st += '<TD>   Estimated pK<sub>sp</sub><sup>*</sup> : </TD>'
                    st += '<TD ALIGN="right"> {:.0f}</TD>'.format(-1 * logKsp)
                    st += '</TR>'
                    st += '</TABLE>'
                    st += '<br><br><br>'
                    st += '<sup>*</sup>Considering equation of the type : <br><br>'
                    st += '&nbsp;&nbsp; M<sub>10</sub>(PO<sub>4</sub>)<sub>6</sub> X<sub>2</sub>  &#x2192;'
                    st += ' 10 M<sup>2+</sup>(aq) + 6 PO<sub>4</sub><sup>3-</sup>(aq) + 2 X<sup>-</sup>(aq)'
                    st += '<br><br>'
                    st += 'These K<sub>sp</sub> estimates should be considered only as first '
                    st += 'approximation taking into account propagated uncertainties.'
                else:
                    st += '</TABLE>'
                    st += '<br><br>'
                    st += 'In the case of non-stoichiometric samples, the existence of a '
                    st += 'metastable equilibrium solubility (MSE) behavior has been <br>'
                    st += 'evidenced at least in some cases, leading to a non-fixed value '
                    st += 'of the solubility product.<br>'
                    st += 'Therefore, in such cases, K<sub>sp</sub> was not calculated.'

            dlg = resultDlg(self)
            dlg.text.setText(st)
            dlg.exec_()
            if dlg.ok != True:
                self.close()



# - resultDlg class ------------------------------------------------------------

class resultDlg(QtWidgets.QDialog):
    def __init__(self, parent=None):
        """ Result dialog.
        """
        super(resultDlg, self).__init__(parent)
        self.setWindowTitle(appName)
        self.ok = False
        self.ini = True
        self.text = QtWidgets.QTextEdit()
        self.text.setReadOnly(True)
        self.font = QtGui.QFont('Arial', 12)
        self.text.setFont(self.font)
        newCalcButton = QtWidgets.QPushButton("Back to chemical composition")
        newCalcButton.setFont(self.font)
        quitButton = QtWidgets.QPushButton("Quit")
        quitButton.setFont(self.font)

        # Set layout
        mainvbox = QtWidgets.QVBoxLayout()
        texthbox = QtWidgets.QHBoxLayout()
        texthbox.addWidget(self.text)
        mainvbox.addLayout(texthbox)
        buttonhbox = QtWidgets.QHBoxLayout()
        buttonhbox.addWidget(newCalcButton)
        buttonhbox.addWidget(quitButton)
        mainvbox.addLayout(buttonhbox)
        self.setLayout(mainvbox)

        self.text.textChanged.connect(self.onChanged)
        newCalcButton.clicked.connect(self.onNewCalc)
        quitButton.clicked.connect(self.onExit)


    def onChanged(self):
        if self.ini:
            self.ini = False
            self.fontMetrics = QtGui.QFontMetrics(self.font)
            textSize = self.fontMetrics.size(0, self.text.toPlainText())
            sampletxt = "-- Estimated DGfo:\t -10000 kJ.mol-1 ---"
            mintextSize = self.fontMetrics.size(0, sampletxt)
            if textSize.width() < mintextSize.width():
                width = int(mintextSize.width())
            else:
                width = int(textSize.width())
            w = width + 50
            h = int(textSize.height() * 0.7)
            self.text.setMinimumSize(w, h)
            self.text.setMaximumSize(w, h)
            self.text.resize(w, h)


    def onExit(self, evt):
        self.ok = False
        self.close()

    def onNewCalc(self, evt):
        self.ok = True
        self.close()


# ------------------------------------------------------------------
 
# Run the program
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    path = inspect.getfile(inspect.currentframe())
    progpath, f = os.path.split(path)
    # Load element data from file if the file exists
    path = os.path.join(progpath, "ElemDB.txt")
    ok = loadElems(path)
    if ok:
        # Look for database files
        ok = lookForDB()
    while ok:
        dlg = initDlg()
        ok = dlg.exec_()
        if ok:
            curDBidx = dlg.seldbno - 1
            DBtitle = DBtitles[curDBidx]
            # Load element data from file if the file exists
            path = os.path.join(progpath, "ElemDB.txt")
            ok = loadElems(path)
            if ok:
                # Load species data from file if the file 'exists
                dbfilnam = "SpeciesDB{}.txt".format(curDBidx+1)
                path = os.path.join(progpath, dbfilnam)
                ok = loadSpecies(path)
            if ok:
                if initDataBase():
                    dlg = inputDlg()
                    ok = dlg.exec_()
    sys.exit()
