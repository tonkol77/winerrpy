import os
import requests
import sys, getopt
from bs4 import BeautifulSoup


class WinErrParser:
    
    pages = {}
    current_folder = os.getcwd()
    
    # Categories and urls
    def _init_categories(self):
        self.categories = {
            'HRESULT': {
                'url': "https://msdn.microsoft.com/en-us/library/cc704587.aspx",
                'parser': self.default_parser
            },
            'NTSTATUS': {
                'url': "https://msdn.microsoft.com/en-us/library/cc704588.aspx",
                'parser': self.default_parser
            },
            'WIN32ERROR': {
                'url': "https://msdn.microsoft.com/en-us/library/cc231199.aspx",
                'parser': self.default_parser
            },
            'SYSTEMERRORCODES': {
                'url': "https://msdn.microsoft.com/en-us/library/windows/desktop/ms681382(v=vs.85).aspx",
                'parser': self.alt_parser
            }
        }

    def get_categories(self):
        return list(self.categories.keys())

    def _get_cache_filename(self, category):
        return "{0}.cache".format(category)
        
    def _check_cache(self, category):
        filename = self._get_cache_filename(category)
        fp = os.path.join(self.current_folder, filename)
        return os.path.exists(fp)

    def _get_category(self, category):
        return self.categories.get(category)

    def _get_category_file(self, category):
        result = self._get_category(category)
        return result.get('file')
    
    def _get_category_url(self, category):
        result = self._get_category(category)
        return result.get('url')

    def _load_page(self, filename):
        with open(filename, 'r') as fh:
            return fh.read()
            
    def _get_page(self, category, verbose=False):
        filename = self._get_cache_filename(category)
        fp = os.path.join(self.current_folder, filename)

        if self._check_cache(category):
            if verbose:
                print("File already exists.")            
        else:
            url = self._get_category_url(category)
            print("Retrieving URL:", url)            
            with open(fp, 'wb') as fh:
                resp = requests.get(url, stream=True)
                if resp.ok:
                    for block in resp.iter_content(1024):
                        fh.write(block)
            print("Created", fp)
        page = self._load_page(fp)
        return page  

    def _parse_page(self, page, verbose=False):
        soup = BeautifulSoup(page, 'html.parser')
        table = soup.find('table')
        if table:
            # This is important, skip the first tr element
            rows = table.find_all('tr')[1:]
            if verbose:
                print("Contains {0} rows.".format(len(rows)))
            d = {}
            for row in rows:
                d.update(self._parse_row(row))
            return d
    
    def _parse_row(self, row):
        td1, td2 = tuple(row.select("td[data-th]"))
        td1_p1, td1_p2 = tuple(td1.find_all('p'))
        td2_p = td2.find('p')
        x = [i.strip() for i in td2_p.contents[0].splitlines()]
        description = " ".join(x).rstrip('\n')
        value, code = td1_p1.contents[0], td1_p2.contents[0]

        return {
            value: {
                'value': value,
                'code': code,
                'description': description
            }
        }

    def __init__(self):
        self.default_parser = self._parse_page
        self.alt_parser = None
        self._init_categories()
        

    def _get(self, category=None, code=None, verbose=False):
        page = None
        item = None
        if not category in self.pages:
            page = self._get_page(category)
            page = self.default_parser(page)
            if page:
                self.pages[category] = page
        else:
            page = self.pages.get(category)
        
        if page:
            if code:
                if verbose:
                    print("Getting by code:", code)
                item = page.get(code)                
            else:
                if verbose:
                    print("Getting single item.")
                item = page.popitem()[1]
        else:
            print("No page?")
        if verbose:        
            print("Item:", item)                
        return item

    def _print_item(self, item, key):
        print("Category:", key)        
        print("Value:", item.get('value'))
        print("Code:", item.get('code'))
        print("Description:", item.get('description'))
        print()

    def print_result(self, result):
        for x in result:
            key, item = x
            self._print_item(item, key)
            
    
    def get(self, category=None, code=None, verbose=False):        
        result = []
        item = None
        if category:
            if verbose:
                print("Search by category:", category)
            item = self._get(category, code)
            if item:
                result.append(tuple((category, item)))
            else:
                if verbose:
                    print("Item not found!", type(item))
        else:
            for category in self.categories.keys():
                if verbose:
                    print("Search by category:", category)
                item = self._get(category, code)
                if item:
                    result.append(tuple((category, item)))
        return result

def main(argv):
    script_name = argv[0]
    argv = argv[1:]    
    type=None
    value=None
    
    try:
        opts, args = getopt.getopt(argv, "ht:v:", ["type=", "value="])
    except getopt.GetoptError:
        sys.exit(2)

    p = WinErrParser()
    for opt, arg in opts:
        if opt in ("-h"):
            options = [o for o in p.get_categories()]
            options_text = "|".join(options)
            text = "{0} -t {1} -v <error_value>".format(script_name, options_text)
            print(text)            
            sys.exit()
        elif opt in ("-t", "--type"):
            arg_value = arg.strip()
            if arg_value in p.get_categories():
                type = arg_value
        elif opt in ("-v", "--value"):
            value = arg.strip()

    
    r = p.get(category=type, code=value)
    p.print_result(r)

if __name__ == "__main__":
    main(sys.argv)
