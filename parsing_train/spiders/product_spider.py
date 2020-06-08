from scrapy.spiders import Spider
import re
from ..items import ProductItem
import mysql.connector


class ProductSpider(Spider):

    name = 'product_spider'

    custom_settings = {
        'ITEM_PIPELINES': {
            'parsing_train.pipelines.ProductPipeline': 400,
        }
    }

    start_urls = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.site_url = 'https://epicentrk.ua/'
        self.connect_db()
        self.get_urls_from_db()
        self.close_connection()

    def connect_db(self):
        self.db = mysql.connector.connect(
            host='localhost',
            user='monitor',
            passwd='1234monitor',
            database='epicentr'
        )
        self.curr = self.db.cursor()

    def get_urls_from_db(self):
        self.curr.execute("""select * from categories where children = FALSE""")
        rows = self.curr.fetchall()
        for row in rows:
            self.start_urls.append(row[2])

    def close_connection(self):
        self.curr.close()
        self.db.close()

    def parse(self, response, category_url=''):
        items = ProductItem()
        items['products'] = []
        if category_url != '':
            items['category_url'] = category_url
        else:
            items['category_url'] = response.url

        products = response.css("#bottom-sticky .card-wrapper .card")
        for product in products:
            item = dict().fromkeys(['name', 'href', 'description', 'price', 'old price'])
            item['name'] = ''.join(product.css('.card__name').css('b.nc::text').extract()).strip()
            item['name'] = item['name'].replace('\xa0', ' ').strip()
            item['href'] = self.site_url + product.css('.card__name').css('a').attrib['href'][1:]
            item['price'] = ' '.join(product.css('.card__price-actual .card__price-sum').
                                     css('span::text').extract()).strip()
            item['old price'] = ' '.join(product.css('.card__price-label::text , .card__price-sum--old::text').
                                         extract()).strip()
            if item['old price'] == '':
                item['old price'] = None
            if item['price'] == '':
                item['price'] = ' '.join(product.css('.card__price').css('div::text').extract()).strip()
            description = product.css('.card__characteristics').css('li::text').extract()
            item['description'] = ''
            for text in description:
                if text.strip() != '':
                    item['description'] += text.strip() + '; '
            item['description'] = item['description'].replace('\xa0', ' ').strip()
            extra_info = ''.join(product.css('.card__action-text').css('b::text').extract()).strip()
            if extra_info != '':
                item['description'] = extra_info + '; ' + item['description']
            item['image'] = product.css('.card__photo img').attrib['src']
            items['products'].append(item)
        yield items

        this_page = response.css('.custom-pagination__item--active::text').extract_first()
        if this_page is not None and int(this_page) == 1:
            pagination = re.findall(r'\?PAGEN_(\d+)=\d+', response.css('.custom-pagination__item')[1].attrib['href'])
            pagination = max(pagination)
            for page in range(2, int(response.css('.custom-pagination__item::text').extract()[-1]) + 1):
                yield response.follow(items['category_url'] + '?PAGEN_' + pagination + '=' + str(page),
                                      callback=self.parse, cb_kwargs=dict(category_url=items['category_url']))
