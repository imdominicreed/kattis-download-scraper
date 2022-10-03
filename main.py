from genericpath import exists
from os import stat
import os
from bs4 import BeautifulSoup
import requests

_HEADERS = {'User-Agent': 'kattis-scraper'}


def login(s, login_url, username, password=None, token=None):
    """Log in to Kattis.
    At least one of password or token needs to be provided.
    Returns a requests.Response with cookies needed to be able to submit
    """
    login_args = {'user': username, 'script': 'true'}
    if password:
        login_args['password'] = password
    if token:
        login_args['token'] = token

    return s.post(login_url, data=login_args, headers=_HEADERS)


def getSolvedProblems(username, password):
    """Get a list of all solved problems corresponding to the username.
    Username can be interchanged with email.
    """
    # Start a session and log in
    s = requests.Session()

    def wget(url):
        return s.get(url)

    loginurl = "https://open.kattis.com/login/email"
    if login(s, loginurl, username, password).text != "Login successful":
        print("Couldn't log you in. Are you sure you're using the right username/password?")
        return []

    # navigate to the solved problems page
    link = "https://open.kattis.com/problems?order=problem_difficulty&show_solved=on&show_tried=off&show_untried=off"

    r = s.get(link)
    r.raise_for_status()

    solved_problems = []
    while True:
        soup = BeautifulSoup(r.text, 'html.parser')
        body = soup.find("tbody")
        tr = body.findAll("tr")
        for problem in tr:
            td = problem.find("td").find("a")
            prob = td['href']
            solved_problems.append(prob[prob.rindex("/")+1:])

        buttons = soup.find("div", {"class": "table-pagination"})

        buttons = buttons.find_all("a")
        nxt = buttons[1]
        if not nxt.has_attr("href"):
            break
        link = nxt['href']
        link = "https://open.kattis.com/problems" + link
        r = s.get(link)
        soup = BeautifulSoup(r.text, 'html.parser')
    at = ['status', 'lang', 'actions']
    if not exists("files"):
        os.mkdir('files')
    for problem in solved_problems:
        link = f"https://open.kattis.com/users/{username}/submissions/{problem}"
        print(link)
        r = s.get(link)
        soup = BeautifulSoup(r.text, 'html.parser')
        body = soup.find('tbody')
        trs = body.find_all('tr')
        file_path = f"files/{problem}"
        if exists(file_path):
            continue
        os.mkdir(file_path)
        langs = set()
        for tr in trs:
            if not tr.has_attr("data-submission-id"):
                continue
            id = tr['data-submission-id']
            status = (tr.find('td', {"data-type": "status"})).get_text()
            lang = tr.find("td", {"data-type": "lang"}).get_text()
            link = f"https://open.kattis.com/submissions/{id}"
            if "Accepted" in status or lang in langs:
                continue
            langs.add(lang)
            sub_txt = wget(link)
            sub = BeautifulSoup(sub_txt.text, 'html.parser')
            download_link = "https://open.kattis.com" + \
                sub.find("a", {"target": "_blank"})['href']
            print(status, lang, link, download_link)
            data = s.get(download_link)
            file_name = download_link[download_link.rindex('/')+1:]
            open(f"files/{problem}/{file_name}", 'wb').write(data.content)


getSolvedProblems("USERNAME", "PASSWORD")
