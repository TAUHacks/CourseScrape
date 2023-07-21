import argparse
import json
import requests
import urllib.parse
from time import sleep
from bs4 import BeautifulSoup

parser = argparse.ArgumentParser(prog="CourseScraper", description="scrapes courses because bidit is too slow")
parser.add_argument("year", type=int)
parser.add_argument("--sem", type=int, default=0, choices=[1, 2], required=False, help="1: sem A, 2: sem B, default: both in one json")
parser.add_argument("-v", "--verbose", action="store_true", required=False)
parser.add_argument("--not-just-exact-sciences", action="store_true", required=False)
args = parser.parse_args()

# Base query
base_fields = {"lstYear1": args.year, "txtShemKurs": "", "txtShemMore": ""}
if args.sem != 0:
    base_fields["ckSem"] = str(args.sem)

def print_v(*print_args, **print_kwargs):
    if args.verbose:
        print(*print_args, **print_kwargs)

sess = requests.Session()

# start by reading the search page - what are the departments?
search_page = sess.get("https://www.ims.tau.ac.il/Tal/KR/Search_P.aspx").text
search_soup = BeautifulSoup(search_page, features="lxml")

all_departments = search_soup.select(".table1 select.freeselect.list")
all_options = []

for department in all_departments:
    options = [x for x in department.select("option") if x.text != ""]
    if options[0].text.startswith("כל "):
        options = [options[0]]

    all_options.append((department["name"], [option["value"] for option in options]))

print_v(all_options)

queries = []

# Create query for every option
for select in all_options:
    for select_option in select[1]:
        new_fields = base_fields.copy()
        new_fields[select[0]] = select_option
        queries.append(new_fields)

# only exact sciences
if not args.not_just_exact_sciences:
    queries = [queries[5]]  # מדעים מדויקים


# example: "03683087", "01", "2023", "1"
# returns: [{"moed", "date", "hour", "type"}]
def get_exam_dates(course_id, group, year, semester):
    base_url = "https://www.ims.tau.ac.il/Tal/KR/Bhina_L.aspx?"
    base_url += urllib.parse.urlencode({"kurs": course_id.replace("-", ""), "kv": group, "sem": str(year) + str(semester)})
    result_soup = BeautifulSoup(sess.get(base_url).text, features="lxml")

    if result_soup.select(".msgerrs"):
        # an error - assume no exam
        return []

    all_rows = result_soup.select_one(".tableblds").select("tr")
    header_row = all_rows[0]
    all_rows = all_rows[1:]
    assert(str(header_row) == '<tr class="listth"><th>מועד</th><th>תאריך</th><th>שעה</th><th>סוג מטלה</th></tr>')

    result = []
    for row in all_rows:
        cols = row.select("td")
        item = {"moed": cols[0].text.strip(), "date": cols[1].text.strip(), "hour": cols[2].text.strip(), "type": cols[3].text.strip()}
        result.append(item)

    return result


def parse_result_page(result_soup):
    all_rows = result_soup.select_one("#frmgrid table[dir=rtl]").select("tr")
    pagenum_row = all_rows[0]
    all_rows = all_rows[1:]
    i = 0
    courses = []
    while i < len(all_rows):
        try:
            if "kotcol" in all_rows[i]["class"] and len(list(all_rows[i].children)) == 2:
                course = {}
                courses.append(course)
                # start of course
                i += 1
                # next row is the course name + id
                course["name"] = list(all_rows[i].children)[1].text
                course["id"] = next(next(all_rows[i].children).children).strip()
                course["group"] = all_rows[i].select_one("span").next_element.next_element.strip()
                i += 1
                # this row has the faculty
                course["faculty"] = list(all_rows[i].children)[1].text
                i += 1
                # look for the times and instructor section
                while not ("kotcol" in all_rows[i - 1]["class"]):
                    i += 1
                lecturer = None

                lessons = []
                course["lessons"] = lessons

                # store a set of the semesters of the course
                semester_set = set()

                while len(list(all_rows[i].children)) == 7:
                    curr_lecturer, ofen_horaa, building, room, day, time, semester = [x.text.strip() for x in all_rows[i].children]
                    if lecturer == None and len(curr_lecturer) != 0:
                        lecturer = curr_lecturer
                        lecturer_found = True
                    lessons.append({"ofen_horaa": ofen_horaa, "building": building, "room": room, "day": day, "time": time, "semester": semester})
                    semester_set.add(semester)
                    i += 1

                course["lecturer"] = lecturer

                # look up the exam if listing is only in one semester
                if len(semester_set) == 1 and lessons[0]["semester"] in ["א'", "ב'"]:
                    sem = ["א'", "ב'"].index(lessons[0]["semester"]) + 1
                    exam_dates = get_exam_dates(course["id"], course["group"], args.year, sem)
                    course["exam_dates"] = exam_dates

                print_v(course)
            else:
                i += 1
        except KeyError:
            i += 1

    return courses

headers = {"Accept": "text/html,application/xhtml+xml,application/xml", "Content-Type": "application/x-www-form-urlencoded", "User-Agent": "CourseScrape"}
print_v(queries)

courses = []
for query in queries:
    print_v("Sleeping...")
    sleep(5)
    print_v("Requesting...", end="")
    result_soup = BeautifulSoup(sess.post("https://www.ims.tau.ac.il/Tal/KR/Search_L.aspx", data=query, headers=headers).text, features="lxml")
    print_v("Done!")
    try:
        courses += parse_result_page(result_soup)
    except:
        continue  # probably a wrong page
    pagenum = 1

    # go to next pages
    while len(result_soup.select("#next")) > 0:
        pagenum += 1
        # get the "dir1": "1" is for the next button
        next_page_query = {}
        for hidden_input in result_soup.select("input[type=hidden]"):
            try:
                next_page_query[hidden_input["name"]] = hidden_input["value"]
            except KeyError:
                pass

        next_page_query["dir1"] = "1"
        print_v("Sleeping...")
        sleep(5)
        print_v(f"Requesting... (Page {pagenum})", end="")
        result_soup = BeautifulSoup(sess.post("https://www.ims.tau.ac.il/Tal/KR/Search_L.aspx", data=next_page_query, headers=headers).text, features="lxml")
        print_v("Done!")
        courses += parse_result_page(result_soup)

# write out the json results
with open("out.json", "w") as out_file:
    json.dump(courses, out_file, separators=(',', ':'), ensure_ascii=False, sort_keys=True)
