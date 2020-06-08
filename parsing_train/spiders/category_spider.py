from scrapy.spiders import Spider
from ..items import CategoryItem
import re


class FirstSpider(Spider):
    name = 'category_spider'

    custom_settings = {
        'ITEM_PIPELINES': {
            'parsing_train.pipelines.CategoriesPipeline': 400,
        }
    }

    start_urls = ['https://epicentrk.ua/ua/shop/']

    def parse_level1_category(self, level1_category):
        this = CategoryItem()
        this['name'] = ''.join(level1_category.css('.menu-link::text').extract()).strip()
        this['url'] = self.start_urls[0] + level1_category.css('.menu-link').attrib['href'][1:]
        this['image_src'] = None
        this['parent_url'] = None

        level2_categories = level1_category.css('.catalog-menu__level-2')
        level2 = self.parse_level2_categories(level2_categories, this['url'])

        return this, level2

    def parse_level2_categories(self, level2_categories, parent_url):
        categories = []
        for category in level2_categories:
            this = CategoryItem()
            this['name'] = ''.join(category.css('::text').extract()).strip()
            this['url'] = self.start_urls[0] + category.attrib['href'][1:]
            this['image_src'] = category.css('img').attrib['data-src']
            if this['image_src'][0] == '/':
                this['image_src'] = self.start_urls[0] + this['image_src'][1:]
            this['parent_url'] = parent_url
            categories.append(this)
        return categories

    @staticmethod
    def format_url(url):
        if re.search('/ua/shop/', url):
            return url
        if re.search('/ua/', url):
            return re.sub('/ua/', '/ua/shop/', url)
        if re.search('/shop/', url):
            return re.sub('/shop/', '/ua/shop/', url)
        return url[:20] + '/ua/shop/' + url[21:]

    def parse_category(self, response, parent_url, f=True):
        if f:
            next_level = response.css('.shop-categories__item-link')
        else:
            next_level = response.css('.shop-category__picture')
            if not parent_url:
                self.start_urls[0] = self.start_urls[0][:-8]
        if len(next_level) != 0:
            categories = []
            flag = True
            for category in next_level:
                this = CategoryItem()
                if f:
                    this['name'] = ''.join(category.css('span::text').extract()).strip()
                else:
                    this['name'] = category.css('img').attrib['data-title']
                this['url'] = self.format_url(self.start_urls[0] + category.attrib['href'][1:])
                this['image_src'] = category.css('img').attrib['src']
                if this['image_src'][0] == '/':
                    this['image_src'] = self.start_urls[0] + this['image_src'][1:]
                if this['url'] == parent_url:
                    flag = False
                    break
                this['parent_url'] = parent_url
                categories.append(this)
            if flag:
                for category in categories:
                    yield category
                    if not parent_url:
                        yield response.follow(category['url'], callback=self.parse_category,
                                              cb_kwargs=dict(parent_url=category['url'], f=False))
                    else:
                        yield response.follow(category['url'], callback=self.parse_category,
                                              cb_kwargs=dict(parent_url=category['url'],))

    def parse(self, response):
        # level1_categories = Selector(response).css('.catalog-menu__category').css('.catalog-menu__level-1')
        # for level1_category in level1_categories:
        #     this_category, level_2_categories = self.parse_level1_category(level1_category)
        #     yield this_category
        #     for category in level_2_categories:
        #         yield category
        #         yield response.follow(category['url'], callback=self.parse_category,
        #                               cb_kwargs=dict(parent_url=category['url'],))
        yield from self.parse_category(response, None, False)
