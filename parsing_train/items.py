# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


# class ParsingTrainItem(scrapy.Item):
#     level1_category = scrapy.Field()
#     level2_categories = scrapy.Field()

class CategoryItem(scrapy.Item):
    name = scrapy.Field()
    url = scrapy.Field()
    image_src = scrapy.Field()
    parent_url = scrapy.Field()


class ProductItem(scrapy.Item):
    products = scrapy.Field()
    category_url = scrapy.Field()
