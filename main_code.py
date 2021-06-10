from requests_html import HTMLSession
from bs4 import BeautifulSoup
from colorthief import ColorThief
from urllib.request import urlopen
import io
import praw
import os
import pickle
from create_token import create_token


# is_color_req = True  # check if required to find dominant color

# given_col_tuple = (145, 115, 108)  # this would be gotten from the user input

# create an HTML Session object
session = HTMLSession()

# Get token file to log into reddit.
# You must enter your....
# client_id, client secret, user_agent, username and password
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

    def get_link(self, sub, lim, url_min_len, url_max_len, is_color_req, given_color, color_bound):
        self.sub = sub
        self.lim = lim
        self.url_min_len = url_min_len
        self.url_max_len = url_max_len
        self.is_color_req = is_color_req
        self.given_col_tuple = given_color
        self.color_bound = color_bound

        # dictionary for top url results
        self.raw_json = {submission.url: submission.num_comments for submission in reddit.subreddit("all").search(self.sub, limit=self.lim) if submission.url.find('imgur.com') != -1 or submission.url.find('reddit.com/gallery/') != -1 and submission.url.find(".gif") == -1 and submission.is_video is False}
        self.sorted_json = sorted(self.raw_json.items(), key=lambda x: x[1])

        # check if color search is selected
        if self.is_color_req:
            for count, value in enumerate(self.sorted_json):

                # if it finds only single images
                if self.sorted_json[count][0].find('imgur.com') != -1:
                    try:

                        # get the html
                        resp = session.get(self.sorted_json[count][0])

                        # Run JavaScript code on web page
                        resp.html.render(retries=50, sleep=1)

                        # format the html properly
                        soup = BeautifulSoup(resp.html.html, 'html.parser')

                        # for imgur
                        image = soup.find("img", attrs={"class": "image-placeholder"})
                        image_link = image["src"]

                        # check if dominant color matches the input colors
                        self.result_col_tuple = self.get_color.get_dom_color(image_link)
                        test = all(x - self.color_bound < y < x + self.color_bound for x, y in zip(self.result_col_tuple, self.given_col_tuple))
                        if test:
                            result1 = {self.sorted_json[count][0]: self.sorted_json[count][1]}  # or result = {image_link: sorted_json[count][1]} if you need the direct link
                            self.sorted_result_list.append(result1)

                    except Exception as e:
                        print(e)

                # if it finds a gallery link
                elif self.sorted_json[count][0].find('reddit.com/gallery/') != -1:
                    try:
                        # get the html
                        resp = session.get(self.sorted_json[count][0])

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


if __name__ == '__main__':
    top_three = OutputLinks()
    list_link = ProcessLinks()
    result = top_three.get_top_three(list_link.get_link("cars", 100, 110, 120, False, (145, 115, 108), 120))
    print(result)
