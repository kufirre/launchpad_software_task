from PyQt5 import QtCore, QtGui, QtWidgets

from requests_html import HTMLSession
from bs4 import BeautifulSoup
from colorthief import ColorThief
from urllib.request import urlopen
import io
import praw
import os
import pickle
from create_token import create_token
import threading


# class to get the dominant color from a url
class GetDominantColor:
    def __init__(self):
        self.link = ''

    def get_dom_color(self, img_link):
        self.link = img_link
        fd = urlopen(self.link)
        f = io.BytesIO(fd.read())  # convert image to bytes
        color_thief = ColorThief(f)  # instantiate the dominant color grabber class
        return color_thief.get_color(quality=10)


#  class to get link
class ProcessLinks:
    def __init__(self):
        self.sorted_result_list = []
        self.raw_json = {}
        self.sorted_json = ()
        self.lim = 0
        self.sub = ''
        self.is_color_req = False  # class that gets inputs from tkinter sets this
        self.url_min_len = 110
        self.url_max_len = 120
        self.color_bound = 50
        self.result_col_tuple = ()
        self.given_col_tuple = ()
        self.get_color = GetDominantColor()

        # create an HTML Session object
        self.session = HTMLSession()

        # Get token file to log into reddit.
        # You must enter your....
        # client_id, client secret, user_agent, username and password
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                self.cred = pickle.load(token)
        else:
            self.cred = create_token()
            pickle_out = open("token.pickle", "wb")
            pickle.dump(self.cred, pickle_out)

        self.reddit = praw.Reddit(client_id=self.cred['client_id'],
                                  client_secret=self.cred['client_secret'],
                                  user_agent=self.cred['user_agent'],
                                  username=self.cred['username'],
                                  password=self.cred['password']
                                  )

    def get_link(self, sub, lim, url_min_len, url_max_len, is_color_req, given_color, color_bound):
        self.sub = sub
        self.lim = lim
        self.url_min_len = url_min_len
        self.url_max_len = url_max_len
        self.is_color_req = is_color_req
        self.given_col_tuple = given_color
        self.color_bound = color_bound

        # dictionary for top url results
        self.raw_json = {submission.url: submission.num_comments for submission in self.reddit.subreddit("all").search(self.sub, limit=self.lim) if (submission.url.find('imgur.com') != -1 or submission.url.find('reddit.com/gallery/') != -1) and submission.url.find('.gif') == -1 and submission.is_video is False}
        self.sorted_json = sorted(self.raw_json.items(), key=lambda x: x[1])

        # check if color search is selected
        if self.is_color_req:
            for count, value in enumerate(self.sorted_json):

                # if it finds only single images
                if self.sorted_json[count][0].find('imgur.com') != -1:

                    # check if dominant color matches the input colors
                    self.result_col_tuple = self.get_color.get_dom_color(self.sorted_json[count][0])
                    test = all(x - self.color_bound < y < x + self.color_bound for x, y in zip(self.result_col_tuple, self.given_col_tuple))
                    if test:
                        result1 = {self.sorted_json[count][0]: self.sorted_json[count][1]}
                        self.sorted_result_list.append(result1)

                # if it finds a gallery link
                elif self.sorted_json[count][0].find('reddit.com/gallery/') != -1:
                    try:
                        # get the html
                        resp = self.session.get(self.sorted_json[count][0])

                        # Run JavaScript code on web page
                        resp.html.render(retries=50, sleep=1)

                        # format the html properly
                        soup = BeautifulSoup(resp.html.html, 'html.parser')

                        images = soup.find_all('img')

                        for i, image in enumerate(images):
                            image_link = image["src"]
                            if self.url_max_len >= len(image_link) >= self.url_min_len:
                                self.result_col_tuple = self.get_color.get_dom_color(image_link)

                        test = all(x - self.color_bound < y < x + self.color_bound for x, y in zip(self.result_col_tuple, self.given_col_tuple))
                        if test:
                            result2 = {self.sorted_json[count][0]: self.sorted_json[count][1]}  # or result = {image_link: sorted_json[count][1]} if you need the direct link
                            self.sorted_result_list.append(result2)

                    except Exception as e:
                        print(e)

        else:
            self.sorted_result_list = self.sorted_json

        return self.sorted_result_list


# class OutPutLinks
class OutputLinks:
    def __init__(self):
        self.j = -1
        self.result_list = []

    def get_top_three(self, sorted_json):
        # iterate through the results and return the top3
        try:
            for k in 'top':
                self.result_list.append(sorted_json[self.j])
                self.j = self.j - 1
            return self.result_list

        except IndexError:
            pass


# class for GUI
class UiMainWindow(object):
    def __init__(self):
        self.centralwidget = QtWidgets.QWidget(main_window)
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.line = QtWidgets.QFrame(self.centralwidget)
        self.gridLayoutWidget = QtWidgets.QWidget(self.centralwidget)
        self.gridLayout = QtWidgets.QGridLayout(self.gridLayoutWidget)
        self.label_3 = QtWidgets.QLabel(self.gridLayoutWidget)
        self.label_2 = QtWidgets.QLabel(self.gridLayoutWidget)
        self.label_4 = QtWidgets.QLabel(self.gridLayoutWidget)
        self.label_5 = QtWidgets.QLabel(self.centralwidget)
        self.lineEdit_2 = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.checkBox = QtWidgets.QCheckBox(self.gridLayoutWidget)
        self.lineEdit = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.line_2 = QtWidgets.QFrame(self.centralwidget)
        self.lineEdit_3 = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        self.tableWidget = QtWidgets.QTableWidget(self.centralwidget)
        self._translate = QtCore.QCoreApplication.translate

        self.post_num = 0
        self.sub_text = ''
        self.is_color = False
        self.color_tuple = ()

    def setup_ui(self, main_window):
        main_window.setObjectName("MainWindow")
        main_window.resize(655, 557)
        main_window.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.centralwidget.setObjectName("centralwidget")
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
        self.gridLayoutWidget.setGeometry(QtCore.QRect(10, 60, 631, 151))
        self.gridLayoutWidget.setObjectName("gridLayoutWidget")
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setObjectName("gridLayout")
        font = QtGui.QFont()
        font.setPointSize(14)
        self.label_3.setFont(font)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 0, 0, 1, 1)
        font = QtGui.QFont()
        font.setPointSize(14)
        self.label_2.setFont(font)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)
        font = QtGui.QFont()
        font.setPointSize(14)
        self.label_4.setFont(font)
        self.label_4.setObjectName("label_4")
        self.gridLayout.addWidget(self.label_4, 2, 0, 1, 1)
        font = QtGui.QFont()
        font.setPointSize(14)
        self.lineEdit_2.setFont(font)
        self.lineEdit_2.setStyleSheet("height:35px;\n"
                                      "border: 3px solid black;\n"
                                      "border-radius:10px;")
        self.lineEdit_2.setObjectName("lineEdit_2")
        self.gridLayout.addWidget(self.lineEdit_2, 1, 2, 1, 1)
        font = QtGui.QFont()
        font.setFamily("DejaVu Sans")
        font.setPointSize(10)
        self.checkBox.setFont(font)
        self.checkBox.setAcceptDrops(False)
        self.checkBox.setAutoFillBackground(False)
        self.checkBox.setStyleSheet("")
        self.checkBox.setCheckable(True)
        self.checkBox.setObjectName("checkBox")
        self.gridLayout.addWidget(self.checkBox, 1, 3, 1, -3)
        font = QtGui.QFont()
        font.setPointSize(14)
        self.lineEdit.setFont(font)
        self.lineEdit.setStyleSheet("height:35px;\n"
                                    "border: 3px solid black;\n"
                                    "border-radius:10px;")
        self.lineEdit.setObjectName("lineEdit")
        self.gridLayout.addWidget(self.lineEdit, 0, 2, 1, 2)
        font = QtGui.QFont()
        font.setPointSize(14)
        self.lineEdit_3.setFont(font)
        self.lineEdit_3.setStyleSheet("height:35px;\n"
                                      "border: 3px solid black;\n"
                                      "border-radius:10px;")
        self.lineEdit_3.setObjectName("lineEdit_3")
        self.gridLayout.addWidget(self.lineEdit_3, 2, 2, 1, 2)
        self.pushButton.setGeometry(QtCore.QRect(300, 210, 130, 61))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.pushButton.setFont(font)
        self.pushButton.setMouseTracking(True)
        self.pushButton.setStyleSheet("*{\n"
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
        self.pushButton.setObjectName("pushButton")
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
        self.tableWidget.setGeometry(QtCore.QRect(20, 360, 610, 170))
        self.tableWidget.setStyleSheet("background-color: rgb(190, 190, 190);\n"
                                       "width:100%;")
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setColumnCount(2)
        self.tableWidget.setRowCount(3)
        item = QtWidgets.QTableWidgetItem()
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        item.setForeground(brush)
        self.tableWidget.setVerticalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        item.setForeground(brush)
        self.tableWidget.setVerticalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        item.setForeground(brush)
        self.tableWidget.setVerticalHeaderItem(2, item)
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
        self.tableWidget.setHorizontalHeaderItem(0, item)
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
        self.tableWidget.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setItem(0, 0, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setItem(0, 1, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setItem(1, 0, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setItem(1, 1, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setItem(2, 0, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setItem(2, 1, item)
        self.tableWidget.horizontalHeader().setDefaultSectionSize(100)
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        self.tableWidget.verticalHeader().setStretchLastSection(False)
        main_window.setCentralWidget(self.centralwidget)

        self.retranslate_ui(main_window)
        QtCore.QMetaObject.connectSlotsByName(main_window)

    def retranslate_ui(self, main_window):

        main_window.setWindowTitle(self._translate("MainWindow", "REDDIT APP UI"))
        self.label.setText(self._translate("MainWindow", "SEARCH PARAMETERS"))
        self.label_3.setText(self._translate("MainWindow", "Keyword"))
        self.label_2.setText(self._translate("MainWindow", "R, G, B "))
        self.label_4.setText(self._translate("MainWindow", "Post Num."))
        self.pushButton.setText(self._translate("MainWindow", "Search"))
        self.label_5.setText(self._translate("MainWindow", "SEARCH RESULT"))
        item = self.tableWidget.horizontalHeaderItem(0)
        item.setText(self._translate("MainWindow", "S/No"))
        item = self.tableWidget.horizontalHeaderItem(1)
        item.setText(self._translate("MainWindow", "Link"))
        __sortingEnabled = self.tableWidget.isSortingEnabled()
        self.tableWidget.setSortingEnabled(False)
        item = self.tableWidget.item(0, 0)
        item.setText(self._translate("MainWindow", "LINK 1:"))
        item = self.tableWidget.item(0, 1)
        item.setText(self._translate("MainWindow", " "))
        item = self.tableWidget.item(1, 0)
        item.setText(self._translate("MainWindow", "LINK 2:"))
        item = self.tableWidget.item(1, 1)
        item.setText(self._translate("MainWindow", " "))
        item = self.tableWidget.item(2, 0)
        item.setText(self._translate("MainWindow", "LINK 3:"))
        item = self.tableWidget.item(2, 1)
        item.setText(self._translate("MainWindow", " "))
        self.tableWidget.setSortingEnabled(__sortingEnabled)

        self.pushButton.clicked.connect(self.thread)

    def thread(self):
        t1 = threading.Thread(target=self.button_click)
        t1.start()

    def button_click(self):
        # this should call a thread
        top_three = OutputLinks()
        list_link = ProcessLinks()

        self.update_table(" ", " ", " ")

        # get R, G, B tuple
        try:
            color = tuple(map(int, self.lineEdit_2.text().split(', ')))
            if len(color) == 3 and -1 < color[0] < 226 and -1 < color[1] < 226 and -1 < color[2] < 226:
                print(color)  # 0 if not selected and 2 if selected
                self.color_tuple = color
                print(self.color_tuple)
            else:
                self.update_table("INVALID VALUE ENTERED", " ", " ")

        except Exception:
            pass

        # get state of checkBox
        if self.checkBox.checkState() == 2:
            self.is_color = True

        else:
            self.is_color = False

        # get search term
        try:
            search_term = self.lineEdit.text()
            if type(search_term) == str:
                self.sub_text = search_term

        except Exception:
            self.update_table("INVALID SEARCH TERM", "", "")
            pass

        # get search term
        try:
            search_number = int(self.lineEdit_3.text())
            if search_number > 0:
                self.post_num = search_number

            else:
                self.update_table("INVALID NUMBER ENTERED!", "", "")

        except Exception:
            print("INVALID TERM")
            pass

        result = top_three.get_top_three(list_link.get_link(self.sub_text, self.post_num, 110, 120, self.is_color, self.color_tuple, 120))

        if result is not None:
            print(result)
            try:
                self.update_table(result[0][0], result[1][0], result[2][0])
            except KeyError:
                self.update_table(list(result[0])[0], list(result[1])[0], list(result[2])[0])

        else:
            self.update_table("NO IMAGES FOUND... TRY INCREASING POST NUM.", " ", " ")

    def update_table(self, row1, row2, row3):
        __sortingEnabled = self.tableWidget.isSortingEnabled()
        item = self.tableWidget.item(0, 1)
        item.setText(self._translate("MainWindow", row1))
        item = self.tableWidget.item(1, 1)
        item.setText(self._translate("MainWindow", row2))
        item = self.tableWidget.item(2, 1)
        item.setText(self._translate("MainWindow", row3))
        self.tableWidget.setSortingEnabled(__sortingEnabled)


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    main_window = QtWidgets.QMainWindow()
    ui = UiMainWindow()
    ui.setup_ui(main_window)
    main_window.show()
    sys.exit(app.exec_())
