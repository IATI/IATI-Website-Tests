import json
import os
import re
import requests
from lxml import etree

ACTIVITY_URL = "https://iatiregistry.org/api/3/action/package_search?q=extras_filetype:activity&facet.field=[%22extras_activity_count%22]&start=0&rows=0&facet.limit=1000000"


def locate_xpath_result(request, xpath):
    """
    Takes a Request object and an xpath.
    Locates all instances of the specified xpath content within the html
    associated with the request.
    Returns a list of all the content matching the xpath
    """
    parser = etree.HTMLParser()
    tree = etree.fromstring(request.text, parser)
    return tree.xpath(xpath)


def get_links_from_page(request):
    """
    Locates the location of all <a href="...">...</a> tags on the page
    associated with the provided request.
    Returns a list of strings containing the linked URLs
        ie. the contents of the `href` attribute
    """
    return locate_xpath_result(request, "//a[@href]/@href")


def get_text_from_xpath(request, xpath):
    """
    Locates the nodes within the HTML at the specific xpath.
    Returns a list of strings containing the contents of these nodes.
    """
    return locate_xpath_result(request, xpath + "/text()")


def get_single_int_from_xpath(request, xpath):
    """
    Locates the nodes within the HTML at the specific xpath.
    Finds a single string containing the contents of this node.
    Ensures the string can be a positive integer.
    Returns the located value.
    """
    node_text_arr = get_text_from_xpath(request, xpath)
    node_text_arr = [s for s in node_text_arr if len(s.strip()) > 0]
    node_str = re.sub(r'\D', '', node_text_arr[0])
    if len(node_str) == 0:
        raise ValueError
    return int(node_str)


def get_joined_text_from_xpath(request, xpath):
    """
    Locates the nodes within the HTML at the specific xpath.
    Returns a string containing the contents of the concatented
    list of strings containing the contents of these nodes.
    """
    return ' '.join(get_text_from_xpath(request, xpath))


def substring_in_list(substr_to_find, list_to_search):
    """
    Returns a boolean value to indicate whether or not a given substring
    is located within the strings of a list.
    """
    result = [s for s in list_to_search if substr_to_find in s]

    return len(result) > 0


def regex_match_in_list(regex_str_to_find, list_to_search):
    """
    Returns a boolean value to indicate whether or not a given regex matches
    any of the strings in a list.
    """
    regex = re.compile(regex_str_to_find)

    result = [s for s in list_to_search if re.search(regex, s)]

    return len(result) > 0


def get_data_folder():
    """
    Returns the location of the folder containing data files.
    """
    path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'data')
    return os.path.normpath(path)


def get_data_file(file_name):
    """
    Returns a path to a data file with the given name.
    """
    return os.path.join(get_data_folder(), file_name)


def load_file_contents(file_name):
    """
    Reads the contents of a file into a string.
    Returns a string containing the file contents.
    """
    # TODO: Improve error handling
    with open(get_data_file(file_name), 'r') as myfile:
        data = myfile.read()
    return data


def get_total_num_activities():
    """Query the IATI registry and return a faceted list of activity counts and their frequencies.

    The total number of activities is then calculated as the sum of the product of a count and a frequency.
    E.g. if "30" is the count and the frequency is 2, then the total number of activities is 60.
    """
    activity_request = requests.get(ACTIVITY_URL)
    if activity_request.status_code == 200:
        activity_json = json.loads(activity_request.content.decode('utf-8'))
        activity_count = 0
        for key in activity_json["result"]["facets"]["extras_activity_count"]:
            activity_count += int(key) * activity_json["result"]["facets"]["extras_activity_count"][key]
        return activity_count
    else:
        raise Exception('Unable to connect to IATI registry to query activities.')
