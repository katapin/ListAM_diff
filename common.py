
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

    @classmethod
    def from_tag(cls, tag):
        """Create Card object from urllib.request.Tag."""
        url = tag.attrs['href']
        id = url.split('/')[-1]
        children = list(tag.children)
        img = children[0].attrs.get('data-original',None)
        # Remove 'dram' sign and the coma separating thousands: '15,000 ֏ '
        pricetxt = children[1].text.replace(' ֏ ', '').replace(',', '')
        caption = children[2].text
        hints = children[3].text
        fullurl = base_url + url
        return cls(id, fullurl, int(pricetxt), caption, img, hints)


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



