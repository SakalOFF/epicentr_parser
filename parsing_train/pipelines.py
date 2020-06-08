# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import mysql.connector


class ProductPipeline(object):

    def __init__(self):
        self.connect_db()
        self.create_table()

    def connect_db(self):
        self.db = mysql.connector.connect(
            host='localhost',
            user='parser',
            passwd='1234parser',
            database='epicentr'
        )
        self.curr = self.db.cursor()

    def create_table(self):
        self.curr.execute("""create table if not exists products(
                                        id integer primary key auto_increment,
                                        name text,
                                        url varchar(255) unique,
                                        price text,
                                        old_price text,
                                        description text,
                                        image_src text,
                                        category_url varchar(255),
                                        foreign key (category_url) references categories(url))""")

    def check_item(self, url):
        self.curr.execute('''select * from products where url = %s''', (url, ))
        result = self.curr.fetchall()
        return len(result) != 0

    def process_item(self, item, spider):
        for product in item['products']:
            if self.check_item(product['href']):
                self.curr.execute("""update products set name = %s, price = %s, old_price = %s, description = %s, 
                image_src = %s, category_url = %s where url = %s""",
                                  (product['name'], product['price'], product['old price'],
                                   product['description'], product['image'], item['category_url'], product['href']))
            else:
                self.curr.execute("""insert into products
                (name, url, price, old_price, description, image_src, category_url) 
                values (%s,%s,%s,%s,%s,%s,%s)""",
                                  (product['name'], product['href'], product['price'], product['old price'],
                                   product['description'], product['image'], item['category_url']))
        self.db.commit()

        return item


class CategoriesPipeline(object):

    def __init__(self):
        self.connect_db()
        self.create_tables()
        self.counter = 0

    def connect_db(self):
        self.db = mysql.connector.connect(
            host='localhost',
            user='parser',
            passwd='1234parser',
            database='epicentr'
        )
        self.curr = self.db.cursor()

    def create_tables(self):
        self.curr.execute("""create table if not exists categories_1(
                                    id integer unique auto_increment,
                                    name varchar(100) not null,
                                    url varchar(255) primary key not null,
                                    image_src text,
                                    children boolean,
                                    parent_url varchar(255),
                                    foreign key (parent_url) references categories_1(url))""")
        self.curr.execute("""ALTER TABLE categories_1 MAX_ROWS=10000""")

    def check_item(self, url):
        self.curr.execute('''select * from categories_1 where url = %s''', (url, ))
        result = self.curr.fetchall()
        return len(result) != 0

    def process_item(self, item, spider):
        if item['parent_url'] is None:
            if not self.check_item(item['url']):
                self.curr.execute("""insert into categories_1 (name, url, image_src, children, parent_url) 
                values(%s,%s,%s,FALSE, null)""", (item['name'], item['url'], item['image_src']))
            else:
                self.curr.execute("update categories_1 set name = %s, image_src = %s,parent_url = null where url = %s",
                                  (item['name'], item['url'], item['image_src']))
        else:
            if not self.check_item(item['url']):
                self.curr.execute("""insert into categories_1 (name, url, image_src, children, parent_url)
                                                                    values(%s,%s,%s,FALSE,%s)""",
                                  (item['name'], item['url'], item['image_src'], item['parent_url']))

                self.curr.execute("""update categories_1 set children = TRUE where url = %s""", (item['parent_url'],))
            else:
                self.curr.execute("update categories_1 set name = %s, image_src = %s where url = %s",
                                  (item['name'], item['image_src'], item['url']))

        self.db.commit()

        return item
