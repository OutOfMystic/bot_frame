import json
import requests
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning

from bs4 import BeautifulSoup

from .vis import *


class HrenDriver:
    """
    Available options: proxies, ChrTab
    """
    
    cookies_on_tabs = []

    def __init__(self, **options):
        self.session = requests.Session()
        self.page_source = ''
        self.current_url = ''
        self.elems = None
        self.options = options
        self.proxies = self.options['proxies'] if 'proxies' in self.options else None
        self.tab = self.options['ChrTab'] if 'ChrTab' in self.options else 0
        if 'user_agent' in self.options:
            user_agent = self.options['user_agent']
        else:
            user_agent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36'
        self.session.headers.update({'User-Agent': user_agent})
        
    def close(self):
        self.quit()
        
    def quit(self):
        self.session = None
        
    def refresh(self):
        self.get(self.current_url)
        
    def first_check(self, *args, **kwargs):
        return self.expl_wait(*args)
        
    def expl_wait(self, *args, **kwargs):
        def to_try():
            if len(args) == 1:
                conds = [self.elems.find_elements(*pair) for pair in args]
                if not any(conds):
                    raise RuntimeError('Ни один объект не был обнаружен')
            else:
                if not self.find_elements(*args):
                    raise RuntimeError('Element timeout exception')
        obj = 'ожидания' if len(args) == 1 else args[1]
        print_errors = self.options['print_errors'] if 'print_errors' in kwargs else True
        res = multi_try(to_try, fpass, 'Wait', 2, True, obj=obj, ChrTab=self.tab, print_errors=print_errors)
            
    def find_element(self, by_what, obj):
        if by_what == 'xpath':
            return self.find_element_by_xpath(obj)
        elif by_what == 'class name':
            return self.find_element_by_class_name(obj)
        elif by_what == 'name':
            return self.find_element_by_name(obj)
        elif by_what == 'tag name':
            return self.find_element_by_tag_name(obj)
            
    def find_elements(self, by_what, obj):
        if by_what == 'xpath':
            return self.find_elements_by_xpath(obj)
        elif by_what == 'class name':
            return self.find_elements_by_class_name(obj)
        elif by_what == 'name':
            return self.find_elements_by_name(obj)
        elif by_what == 'tag name':
            return self.find_elements_by_tag_name(obj)
        elif by_what == 'id':
            return self.find_elements_by_id(obj)
            
    def find_element_by_tag_name(self, obj):
        found = self.elems.find(obj)
        if not found:
            raise NotImplementedError
        return found
        
    def find_element_by_class_name(self, obj):
        found = self.elems.find(attrs={"class": obj})
        if not found:
            raise NotImplementedError
        return found
        
    def find_element_by_name(self, obj):
        found = self.elems.find(attrs={"name": obj})
        if not found:
            raise NotImplementedError
        return found
        
    def find_element_by_id(self, obj):
        found = self.elems.find(attrs={"id": obj})
        if not found:
            raise NotImplementedError
        return found
        
    def find_elements_by_tag_name(self, obj):
        return self.elems.find_all(obj)
        
    def find_elements_by_class_name(self, obj):
        return self.elems.find_all(attrs={"class": obj})
        
    def find_elements_by_name(self, obj):
        return self.elems.find_all(attrs={"name": obj})
        
    def find_elements_by_id(self, obj):
        return self.elems.find_all(attrs={"id": obj})
        
    def find_element_by_xpath(self, xpath):
        if not '//' in xpath:
            raise RuntimeError('Relative xpaths not supported')
        if 'contains' in xpath:
            raise RuntimeError('"Conatins" method not supported')
        name = double_split(xpath, '@', '=')
        if "'" in xpath:
            value = double_split(xpath, "'", "'")
        elif '"' in xpath:
            value = double_split(xpath, '"', '"')
        return self.elems.find(attrs={name: value})
        
    def find_elements_by_xpath(self, xpath):
        if not '//' in xpath:
            raise RuntimeError('Relative xpaths not supported')
        if 'contains' in xpath:
            raise RuntimeError('"Conatins" method not supported')
        name = double_split(xpath, '@', '=')
        if "'" in xpath:
            value = double_split(xpath, "'", "'")
        elif '"' in xpath:
            value = double_split(xpath, '"', '"')
        return self.elems.find_all(attrs={name: value})
        
    def send_request(decorated_request):
        def wrapper(self, url, **kwargs):
            if self.proxies:
                kwargs['proxies'] = self.proxies
            r = decorated_request(self, url, **kwargs)
            self.page_source = r.text
            self.current_url = r.url
            self.status_code = r.status_code
        return wrapper
        
    @send_request
    def get(self, url, **kwargs):
        self.elems = BeautifulSoup(self.page_source, 'lxml')
        request = request_init(self.session.get, url, **kwargs)
        return request
        
    @send_request
    def post(self, url, **kwargs):
        return request_init(self.session.post, url, **kwargs)
        
    @send_request
    def put(self, url, **kwargs):
        return request_init(self.session.put, url, **kwargs)
        
    @send_request
    def delete(self, url, **kwargs):
        return request_init(self.session.delete, url, **kwargs)
        
    @send_request
    def head(self, url, **kwargs):
        return request_init(self.session.head, url, **kwargs)
        
    @send_request
    def options(self, url, **kwargs):
        return request_init(self.session.options, url, **kwargs)
        
    def load_cookies(self):
        self.delete_all_cookies()
        if not self.cookies_on_tabs:
            with open(r'json\cookies.json', 'r') as read_file:
                self.cookies_on_tabs = json.load(read_file)
        if self.tab < len(self.cookies_on_tabs):
            cookies = self.cookies_on_tabs[self.tab]
            for cookie in cookies:
                self.add_cookie(cookie)
        
    def load(self, url, cookies=False, retry=None):
        if cookies:
            self.load_cookies()
        self.get(url)
        self.elems = BeautifulSoup(self.page_source, 'lxml')
        
    def add_cookie(self, cookie):
        if 'expiry' not in cookie:
            cookie['expiry'] = None
        cookie['expires'] = cookie['expiry']
        del cookie['expiry']
        self.session.cookies.set(**cookie)
        
    def delete_all_cookies(self):
        self.session.cookies = requests.cookies.RequestsCookieJar()
        
    def get_cookies_string(self):
        dict_ = requests.utils.dict_from_cookiejar(self.session.cookies)
        str_cookies = '; '.join(foo + '=' + boo for foo, boo in dict_.items())
        return str_cookies

    def get_cookies(self):
        all_cookies = []
        for cookie in self.session.cookies:
            to_cookie = {
                'name': cookie.name,
                'value': cookie.value,
                'domain': cookie.domain,
                'path': cookie.path,
                'expiry': cookie.expires
            }
            if not to_cookie['expiry']:
                del to_cookie['expiry']
            all_cookies.append(to_cookie)
        return all_cookies
        
    def save_cookies(self):
        if not self.cookies_on_tabs:
            with open(r'json\cookies.json', 'r') as read_file:
                self.cookies_on_tabs = json.load(read_file)
        length = len(self.cookies_on_tabs)
        if self.tab >= length:
            count = self.tab - length + 1
            empties = [[]] * count
            self.cookies_on_tabs.extend(empties)
        self.cookies_on_tabs[self.tab] = self.get_cookies()
        with open(r'json\cookies.json', 'w') as f:
            json.dump(self.cookies_on_tabs, f, indent=2)


def to_cjd(name, value, domain, path):
    cookie = {
        "version": 0, "name": name, "value": value,
        "port": None, "domain": domain, "path": path,
        "secure": False, "expires": None, "discard": True,
        "comment": None, "comment_url": None,
        "rest": {'HttpOnly': None}, "rfc2109": False
    }
    return cookie


def cookies_str_to_list(cookies_str, domain):
    cookies_list = []
    for str_cookie in cookies_str.split('; '):
        cookie_name, cookie_value = str_cookie.split('=')
        cookie = to_cjd(cookie_name, cookie_value, domain, '/')
        cookies_list.append(cookie)
    return cookies_list


def request_init(func, url, **kwargs):
    try:
        r = func(url, **kwargs)
    except requests.exceptions.SSLError:
        r = func(url, **kwargs, verify=False)
    return r


disable_warnings(InsecureRequestWarning)
