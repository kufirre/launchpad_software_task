"""Displays on a simple interface top 3 links of popular posts
related to a subject on Reddit.
Also scans image URL's for a given R,G,B  dominant color (given as a tuple)
Checks that the values entered range between 0 and 255
"""
import os
import io
from urllib.request import urlopen
import threading
import pickle

from PyQt5 import QtCore, QtGui, QtWidgets
from requests_html import HTMLSession
from bs4 import BeautifulSoup
from colorthief import ColorThief
import praw


def get_dom_color(img_link):
    """Get the dominant color from a url

    :param str img_link: The URL of the image
    :return: a tuple 3 colors representing R,G,B
    :rtype: tuple
    """
    link = img_link
    image = urlopen(link)
    image_byte = io.BytesIO(image.read())  # convert image to bytes
    color_thief = ColorThief(image_byte)  # instantiate the dominant color grabber class
    return color_thief.get_color(quality=10)


#  class to get link
def create_token():
    """Get login details for reddit which would be saved in rhe token.pickel file later:
    client_id, client secret, user_agent, username and password

    :return dict cred: a dictionary containing the login details and the tokens
    :rtype: dict

    """
    cred = {"client_id": input("Client_id: "),
            "client_secret": input("client_secret: "),
            "user_agent": input("user_agent: "),
            "username": input("username: "),
            "password": input("password: ")}
    return cred


def get_link(sub, lim, color_req, given_color, color_bound):
    """Get the top links on Reddit related to a search term (sub)

    :param str sub: this is the search term to check Reddit for
    :param int lim: this the number of top posts on Reddit to search for
    :param bool color_req: states if a color check should be performed or not
    :param tuple given_color: tuple containing R,G,B dominant color value to search for
    :param color_bound: boundary that determines colors that are close to the given dominant color
    :return: list of dictionaries containing image links and number of comments
    :rtype: list
    """

    _lim = lim
    _sub = sub
    _color_req = color_req
    _url_min_len = 110
    _url_max_len = 120
    _given_color = given_color
    _color_bound = color_bound

    sorted_result_list = []
    result_col_tuple = ()

    # create an HTML Session object
    session = HTMLSession()

    # load the credentials to login to Reddit
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            cred = pickle.load(token)
    else:
        cred = create_token()
        pickle_out = open("token.pickle", "wb")
        pickle.dump(cred, pickle_out)

    reddit = praw.Reddit(client_id=cred['client_id'],
                         client_secret=cred['client_secret'],
                         user_agent=cred['user_agent'],
                         username=cred['username'],
                         password=cred['password']
                         )

    # list of URL's gotten from the search
    raw_list = {submission.url: submission.num_comments for submission in
                reddit.subreddit("all").search(_sub, limit=_lim) if
                (submission.url.find('imgur.com') != -1
                 or submission.url.find('reddit.com/gallery/') != -1)
                and submission.url.find('.gif') == -1 and submission.is_video is False}
    sorted_list = sorted(raw_list.items(), key=lambda x: x[1])

    # check if color search is selected
    if _color_req:
        for count, _ in enumerate(sorted_list):

            # if it finds only single images
            if sorted_list[count][0].find('imgur.com') != -1:

                # check if dominant color matches the input colors
                result_col_tuple = get_dom_color(sorted_list[count][0])
                test = all(x - _color_bound < y < x + _color_bound
                           for x, y in zip(result_col_tuple, _given_color))
                if test:
                    result1 = {sorted_list[count][0]: sorted_list[count][1]}
                    sorted_result_list.append(result1)

            # if it finds a gallery link
            elif sorted_list[count][0].find('reddit.com/gallery/') != -1:
                try:
                    # get the html
                    resp = session.get(sorted_list[count][0])

                    # Run JavaScript code on web page to get the complete HTML tags
                    resp.html.render(retries=50, sleep=1)

                    # format the html properly
                    soup = BeautifulSoup(resp.html.html, 'html.parser')

                    images = soup.find_all('img')

                    for image in images:
                        image_link = image["src"]
                        if _url_max_len >= len(image_link) >= _url_min_len:
                            result_col_tuple = get_dom_color(image_link)

                    test = all(x - _color_bound < y < x + _color_bound
                               for x, y in zip(result_col_tuple, _given_color))
                    if test:
                        result2 = {sorted_list[count][0]: sorted_list[count][1]}
                        sorted_result_list.append(result2)

                except IndexError as error_:
                    print(error_)

    else:
        sorted_result_list = sorted_list

    return sorted_result_list


def get_top_three(sorted_list):
    """
    Iterate through the sorted list of image URLS and return the top 3
    based on number of comments

    :param list sorted_list: list of top image URL's
    :return: list containing top 3 image URL's based on number of comments
    :rtype: list
    """
    j = -1
    result_list = []

    try:
        for _ in 'top':
            result_list.append(sorted_list[j])
            j = j - 1
        return result_list

    except IndexError:
        return -1


# class for GUI
class UiMainWindow:
    """Class to display results on a simple GUI
    Runs an infinite loop when called and listens for search button clicks.
    """
    def __init__(self):
        """Constructor class"""
        self.central_widget = QtWidgets.QWidget(main_window)
        self.label = QtWidgets.QLabel(self.central_widget)
        self.line = QtWidgets.QFrame(self.central_widget)
        self.grid_layout_widget = QtWidgets.QWidget(self.central_widget)
        self.grid_layout = QtWidgets.QGridLayout(self.grid_layout_widget)
        self.label_3 = QtWidgets.QLabel(self.grid_layout_widget)
        self.label_2 = QtWidgets.QLabel(self.grid_layout_widget)
        self.label_4 = QtWidgets.QLabel(self.grid_layout_widget)
        self.label_5 = QtWidgets.QLabel(self.central_widget)
        self.line_edit_2 = QtWidgets.QLineEdit(self.grid_layout_widget)
        self.check_box = QtWidgets.QCheckBox(self.grid_layout_widget)
        self.line_edit = QtWidgets.QLineEdit(self.grid_layout_widget)
        self.line_2 = QtWidgets.QFrame(self.central_widget)
        self.line_edit_3 = QtWidgets.QLineEdit(self.grid_layout_widget)
        self.push_button = QtWidgets.QPushButton(self.central_widget)
        self.table_widget = QtWidgets.QTableWidget(self.central_widget)
        self._translate = QtCore.QCoreApplication.translate

        self.post_num = 0
        self.sub_text = ''
        self.is_color = False
        self.color_tuple = ()

    def setup_ui(self, main_window_2):
        """
        Configure GUI main window elements and widgets

        :param main_window_2:
        """
        main_window_2.setObjectName("MainWindow")
        main_window_2.resize(655, 557)
        main_window_2.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.central_widget.setObjectName("centralwidget")
        self.label.setGeometry(QtCore.QRect(160, 10, 350, 31))
        font = QtGui.QFont()
        font.setBold(True)
        font.setPointSize(16)
        self.label.setFont(font)
        self.label.setLineWidth(0)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName("label")
        self.line.setGeometry(QtCore.QRect(0, 40, 701, 20))
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.grid_layout_widget.setGeometry(QtCore.QRect(10, 60, 631, 151))
        self.grid_layout_widget.setObjectName("gridLayoutWidget")
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setObjectName("gridLayout")
        font = QtGui.QFont()
        font.setPointSize(14)
        self.label_3.setFont(font)
        self.label_3.setObjectName("label_3")
        self.grid_layout.addWidget(self.label_3, 0, 0, 1, 1)
        font = QtGui.QFont()
        font.setPointSize(14)
        self.label_2.setFont(font)
        self.label_2.setObjectName("label_2")
        self.grid_layout.addWidget(self.label_2, 1, 0, 1, 1)
        font = QtGui.QFont()
        font.setPointSize(14)
        self.label_4.setFont(font)
        self.label_4.setObjectName("label_4")
        self.grid_layout.addWidget(self.label_4, 2, 0, 1, 1)
        font = QtGui.QFont()
        font.setPointSize(14)
        self.line_edit_2.setFont(font)
        self.line_edit_2.setStyleSheet("height:35px;\n"
                                       "border: 3px solid black;\n"
                                       "border-radius:10px;")
        self.line_edit_2.setObjectName("lineEdit_2")
        self.grid_layout.addWidget(self.line_edit_2, 1, 2, 1, 1)
        font = QtGui.QFont()
        font.setFamily("DejaVu Sans")
        font.setPointSize(10)
        self.check_box.setFont(font)
        self.check_box.setAcceptDrops(False)
        self.check_box.setAutoFillBackground(False)
        self.check_box.setStyleSheet("")
        self.check_box.setCheckable(True)
        self.check_box.setObjectName("checkBox")
        self.grid_layout.addWidget(self.check_box, 1, 3, 1, -3)
        font = QtGui.QFont()
        font.setPointSize(14)
        self.line_edit.setFont(font)
        self.line_edit.setStyleSheet("height:35px;\n"
                                     "border: 3px solid black;\n"
                                     "border-radius:10px;")
        self.line_edit.setObjectName("lineEdit")
        self.grid_layout.addWidget(self.line_edit, 0, 2, 1, 2)
        font = QtGui.QFont()
        font.setPointSize(14)
        self.line_edit_3.setFont(font)
        self.line_edit_3.setStyleSheet("height:35px;\n"
                                       "border: 3px solid black;\n"
                                       "border-radius:10px;")
        self.line_edit_3.setObjectName("lineEdit_3")
        self.grid_layout.addWidget(self.line_edit_3, 2, 2, 1, 2)
        self.push_button.setGeometry(QtCore.QRect(300, 210, 130, 61))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.push_button.setFont(font)
        self.push_button.setMouseTracking(True)
        self.push_button.setStyleSheet("*{\n"
                                       "  background-color: #4CAF50; /* Green */\n"
                                       "  border: none;\n"
                                       "  color: white;\n"
                                       "  text-align: center;\n"
                                       "  text-decoration: none;\n"
                                       "  display: inline-block;\n"
                                       "  margin: 4px 2px;\n"
                                       "  transition-duration: 0.4s;\n"
                                       "  cursor: pointer;\n"
                                       "}\n"
                                       "*:hover{\n"
                                       "  background-color: white; \n"
                                       "  color: black; \n"
                                       "  border: 2px solid #4CAF50;\n"
                                       "}")
        self.push_button.setObjectName("pushButton")
        self.line_2.setGeometry(QtCore.QRect(-10, 280, 671, 20))
        self.line_2.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_2.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_2.setObjectName("line_2")
        self.label_5.setGeometry(QtCore.QRect(170, 300, 301, 31))
        font = QtGui.QFont()
        font.setPointSize(16)
        font.setBold(True)
        self.label_5.setFont(font)
        self.label_5.setLineWidth(0)
        self.label_5.setAlignment(QtCore.Qt.AlignCenter)
        self.label_5.setObjectName("label_5")
        self.table_widget.setGeometry(QtCore.QRect(20, 360, 610, 170))
        self.table_widget.setStyleSheet("background-color: rgb(190, 190, 190);\n"
                                        "width:100%;")
        self.table_widget.setObjectName("tableWidget")
        self.table_widget.setColumnCount(2)
        self.table_widget.setRowCount(3)
        item = QtWidgets.QTableWidgetItem()
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        item.setForeground(brush)
        self.table_widget.setVerticalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        item.setForeground(brush)
        self.table_widget.setVerticalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        item.setForeground(brush)
        self.table_widget.setVerticalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(75)
        item.setFont(font)
        item.setBackground(QtGui.QColor(255, 255, 255))
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        item.setForeground(brush)
        self.table_widget.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(75)
        item.setFont(font)
        item.setBackground(QtGui.QColor(255, 255, 255))
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        item.setForeground(brush)
        self.table_widget.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.table_widget.setItem(0, 0, item)
        item = QtWidgets.QTableWidgetItem()
        self.table_widget.setItem(0, 1, item)
        item = QtWidgets.QTableWidgetItem()
        self.table_widget.setItem(1, 0, item)
        item = QtWidgets.QTableWidgetItem()
        self.table_widget.setItem(1, 1, item)
        item = QtWidgets.QTableWidgetItem()
        self.table_widget.setItem(2, 0, item)
        item = QtWidgets.QTableWidgetItem()
        self.table_widget.setItem(2, 1, item)
        self.table_widget.horizontalHeader().setDefaultSectionSize(100)
        self.table_widget.horizontalHeader().setStretchLastSection(True)
        self.table_widget.verticalHeader().setStretchLastSection(False)
        main_window.setCentralWidget(self.central_widget)

        self.retranslate_ui(main_window)
        QtCore.QMetaObject.connectSlotsByName(main_window)

    def retranslate_ui(self, main_window_2):
        """Populate the GUI window with all the elements and widgets

        :param main_window_2: Main GUI window
        """

        main_window_2.setWindowTitle(self._translate("MainWindow", "REDDIT APP UI"))
        self.label.setText(self._translate("MainWindow", "SEARCH PARAMETERS"))
        self.label_3.setText(self._translate("MainWindow", "Keyword"))
        self.label_2.setText(self._translate("MainWindow", "R, G, B "))
        self.label_4.setText(self._translate("MainWindow", "Post Num."))
        self.push_button.setText(self._translate("MainWindow", "Search"))
        self.label_5.setText(self._translate("MainWindow", "SEARCH RESULT"))
        item = self.table_widget.horizontalHeaderItem(0)
        item.setText(self._translate("MainWindow", "S/No"))
        item = self.table_widget.horizontalHeaderItem(1)
        item.setText(self._translate("MainWindow", "Link"))
        sorting_enabled = self.table_widget.isSortingEnabled()
        self.table_widget.setSortingEnabled(False)
        item = self.table_widget.item(0, 0)
        item.setText(self._translate("MainWindow", "LINK 1:"))
        item = self.table_widget.item(0, 1)
        item.setText(self._translate("MainWindow", " "))
        item = self.table_widget.item(1, 0)
        item.setText(self._translate("MainWindow", "LINK 2:"))
        item = self.table_widget.item(1, 1)
        item.setText(self._translate("MainWindow", " "))
        item = self.table_widget.item(2, 0)
        item.setText(self._translate("MainWindow", "LINK 3:"))
        item = self.table_widget.item(2, 1)
        item.setText(self._translate("MainWindow", " "))
        self.table_widget.setSortingEnabled(sorting_enabled)

        self.push_button.clicked.connect(self.thread)

    def thread(self):
        """Start a thread to listen for Search button clicks and perform an action."""
        button_click_thread = threading.Thread(target=self.button_click)
        button_click_thread.start()

    def button_click(self):
        """
        An action to perform when search button is clicked.
        Checks if the check_box is selected in order to determine whether
        to search for dominant colors.
        Searches Reddit for top links containing images and returns the top URL's
        Updates the table with top 3 image URL's based on number of comments
        """

        self.update_table(" ", " ", " ")

        # get R, G, B tuple
        try:
            color = tuple(map(int, self.line_edit_2.text().split(', ')))
            # check is RGB values given are between 0 and 255
            if len(color) == 3 and -1 < color[0] < 226 \
                    and -1 < color[1] < 226 and -1 < color[2] < 226:
                print(color)  # 0 if not selected and 2 if selected
                self.color_tuple = color
                print(self.color_tuple)
            else:
                self.update_table("INVALID VALUE ENTERED", " ", " ")

        except ValueError:
            pass

        # get state of checkBox
        if self.check_box.checkState() == 2:
            self.is_color = True

        else:
            self.is_color = False

        # get search term
        search_term = self.line_edit.text()
        if isinstance(search_term, str):
            self.sub_text = search_term

        else:
            self.update_table("INVALID SEARCH TERM", "", "")

        # get search number
        search_number = int(self.line_edit_3.text())
        if isinstance(search_number, int):
            self.post_num = search_number

        else:
            self.update_table("INVALID NUMBER ENTERED!", "", "")

        result = get_top_three(get_link(self.sub_text, self.post_num,
                                        self.is_color, self.color_tuple, 120))

        if isinstance(result, (list, dict)):
            print(result)
            self.update_table(result[0][0], result[1][0], result[2][0])

        else:
            self.update_table("NO IMAGES FOUND... TRY INCREASING POST NUM.", " ", " ")

    def update_table(self, row1, row2, row3):
        """Update table in the main window

        :param str row1: first row of second column of table
        :param str row2: second row of second column of table
        :param str row3: third row of second column of table
        """
        sorting_enabled = self.table_widget.isSortingEnabled()
        self.table_widget.setItem(0, 1, QtWidgets.QTableWidgetItem(row1))
        self.table_widget.setItem(1, 1, QtWidgets.QTableWidgetItem(row2))
        self.table_widget.setItem(2, 1, QtWidgets.QTableWidgetItem(row3))
        self.table_widget.setSortingEnabled(sorting_enabled)


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    main_window = QtWidgets.QMainWindow()
    ui = UiMainWindow()
    ui.setup_ui(main_window)
    main_window.show()
    sys.exit(app.exec_())
