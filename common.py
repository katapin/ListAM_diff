import textwrap
import dataclasses
import json


## Settings
sleeptime = 17  # The pause between requests.
base_url = 'https://www.list.am'
base_headers = {
    "Host": "www.list.am",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:129.0) Gecko/20100101 Firefox/129.0",
    "content-type": "text/html; charset=utf-8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8",
    'Upgrade-Insecure-Requests': '1',
    "Cookie": 'lang=0'
}


## Data model
@dataclasses.dataclass
class Card:
    """One single card."""
    id: str
    fullurl: str
    price: int
    caption: str
    img: str
    hints: str
    date_created: str = None
    date_updated: str = None
    text: str = None
    status: str = None

    def html(self) -> str:
        _lst = [
            f'<a href = "{self.fullurl}" style="width:calc((100% - 24px)/5.2)">',
            f'<img src = "https://{self.img}" style = "" >',
            f'<div class ="p" > {self.price} ֏ </div >',
            f'<div class ="l" > {self.caption} </div >',
            f'<div class ="at"> {self.hints} </div> </a>'
        ]
        return ''.join(_lst)

    # @classmethod
    # def from_tag(cls, tag):
    #     """Create Card object from urllib.request.Tag."""
    #     url = tag.attrs['href']
    #     id = url.split('/')[-1]
    #     children = list(tag.children)
    #     img = children[0].attrs.get('data-original',None)
    #     # Remove 'dram' sign and the coma separating thousands: '15,000 ֏ '
    #     pricetxt = children[1].text.replace(' ֏ ', '').replace(',', '')
    #     caption = children[2].text
    #     hints = children[3].text
    #     fullurl = base_url + url
    #     return cls(id, fullurl, int(pricetxt), caption, img, hints)

    @classmethod
    def from_tag(cls, tag):
        """Create Card object from urllib.request.Tag."""
        url = tag.attrs['href']
        id = url.split('/')[-1]
        a_children = list(tag.children)
        img = a_children[0].attrs.get('data-original', None)
        div = a_children[1]
        d_children = list(div.children)
        caption = list(d_children[0].children)[0].text
        # Remove 'dram' sign and the coma separating thousands: '15,000 ֏ '
        pricetxt = list(d_children[1].children)[0].text.replace(' ֏ ', '').replace(',', '')
        hints = d_children[2].text
        date_updated = d_children[3].text
        fullurl = base_url + url

        try:
            price = int(pricetxt)
        except ValueError:
            price = 0  # Dollars can't be processed correctly yet
        return cls(id, fullurl, price, caption, img, hints,
                   date_updated=date_updated)


def parse_showcase(soup) -> list:
    """Parse a single page with many cards."""
    gal = soup.findAll('div', attrs={'class': 'dl'})[0]  # 'gallery' inside the <div class="dl"> tag
    # gl = gls[-1]  # gls[0] - VIP cards, gls[1] - regular
    result = []
    for child in gal:  # <a href> tag
        if not child.attrs.get('href'):  # We're expecting <a href=...
            continue
        card = Card.from_tag(child)
        result.append(card)
    return result



@dataclasses.dataclass
class Gallery:
    """Collection of cards under a common title."""
    cards: list[Card]
    title: str

    def html(self) -> str:
        head = f'<div class="glheader">{self.title}</div>\n' \
               '<div class="gl">\n'

        items = [c.html() for c in self.cards]
        return head + '\n'.join(items) + '\n</div>\n'

    def __len__(self):
        return len(self.cards)


## Some helpers
class EnhancedJSONEncoder(json.JSONEncoder):
    """Make JSON loader able to treat dataclasses."""
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


def read_json(filepath: str):
    with open(filepath, 'r') as f:
        data = json.load(f)
    return data


def write_json(filepath: str, data: dict):
    with open(filepath, 'w') as f:
        json.dump(data, f, cls=EnhancedJSONEncoder, ensure_ascii=True, indent=4)


def save_html(reportfile: str, galleries: list, pagetitle: str = ''):
    gallereis_code = '\n'.join([g.html() for g in galleries if len(g) > 0])
    code = textwrap.dedent(f"""\
    <html lang="en">
    <head>
    <title>{pagetitle}</title>
    <link href="https://list.am/l-63.css" rel="stylesheet" type="text/css">
    <link href="https://list.am/m-f25.css" rel="stylesheet" type="text/css" media="screen and (max-device-width:980px),screen and (max-device-width:1024px) and (orientation:portrait)">
    </head>
    <body>
    <div class="dl">
    {gallereis_code}
    </div>
    </body>
    </html>
    """)
    with open(reportfile, 'w') as f:
        f.write(code)

