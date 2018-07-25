# -*- coding: utf-8 -*-
import scrapy
from pluralsight.items import PluralsightItem
import re
from scrapy_splash import SplashRequest
from datetime import datetime

script = """
function main(splash)
    local url = splash.args.url
    splash.resource_timeout = 240.0
    assert(splash:go(url))
    assert(splash:wait(2))

    -- go back 1 month in time and wait a little (1 second)
    --local element = splash:select('#search-results-section-load-more')
    local get_dimensions = splash:jsfunc([[
        function () {
            if (document.getElementById('search-results-section-load-more')){
                var rect = document.getElementById('search-results-section-load-more').getClientRects()[0];
                return {"x": rect.left, "y": rect.top}
            } else{
                return false
            }
        }
    ]])
    local get_element = splash:jsfunc([[
        function () {
            return document.getElementById('search-results-section-load-more')
        }
    ]])
    splash:set_viewport_full()
    splash:wait(0.1)
    dimensions = get_dimensions()

    while dimensions do
        splash:mouse_click(dimensions.x, dimensions.y)
        assert(splash:wait(2))
        dimensions = get_dimensions()
    end
    --local element = splash:select('#search-results-section-load-more')
    --local element = get_element()
    --print(element)
    --while element do
    --  local bounds = element:bounds()
    --  assert(element:mouseclick{x = bounds.width/2, y = bounds.height/2})
    --  assert(splash:wait(5))
    --  element = get_element()
    --end

    -- return result as a JSON object
    return {
        html = splash:html(),
        -- we don't need screenshot or network activity
        --png = splash:png(),
        --har = splash:har(),
    }
end
"""

pattern = re.compile(r'[0-9]+')
hour_pattern = re.compile(r'([0-9]+)h')
minute_pattern = re.compile(r'([0-9]+)m')


class PluralSpider(scrapy.Spider):
    name = "plural"
    #allowed_domains = ["pluralsight.com"]
    start_urls = ['https://www.pluralsight.com/browse']

    def parse(self, response):
        link_group_one = response.xpath('//div[contains(@class,"header_roles")]/a[1]')
        link_group_two = response.xpath('//a[contains(@class,"header_roles")]')
        all_links = link_group_one + link_group_two
        for item in all_links:
            link = item.xpath('@href').extract_first()
            category = item.xpath('text()').extract_first()
            request = scrapy.Request(response.urljoin(link), self.parse_category)
            request.meta['category'] = category
            yield request

    def parse_category(self, response):
        main_category = response.meta['category']
        subs = response.xpath('//div[@id="tab-subjects"]/div[contains(@class,"tab-content-item")]/a')
        subs_list = []
        for item in subs:
            link = item.xpath('@href').extract_first()
            category_text = item.xpath('text()').extract_first()
            try:
                category = category_text.split('(')[0].strip()
            except Exception:
                category = category_text
            try:
                count = int(pattern.findall(category_text)[-1])
            except Exception:
                count = 0
            subs_list.append([link, category, count])

        ordered_subs_list = sorted(subs_list, key=lambda x: x[2])

        for sub in ordered_subs_list:
            #request = scrapy.Request('https://www.pluralsight.com'+ sub[0], self.parse_subcategory)
            if sub[2] > 25:
                request = SplashRequest('https://www.pluralsight.com' + sub[0],
                                        callback=self.parse_author,
                                        errback=self.errback_author,
                                        args={'wait': 1, },)
            else:
                request = SplashRequest('https://www.pluralsight.com' + sub[0],
                                        callback=self.parse_subcategory,
                                        errback=self.errback_subcategory,
                                        args={'wait': 1, },)
            request.meta['category'] = main_category
            request.meta['subcategory'] = sub[1]
            yield request

    def parse_author(self, response):

        category = response.meta['category']
        subcategory = response.meta['subcategory']

        for author in response.xpath('//a[contains(@data-label,"authors")]/@data-value').extract():
            request = SplashRequest(response.url + '&authors='+author,
                                    callback=self.parse_subcategory,
                                    errback=self.errback_subcategory,
                                    args= {'lua_source': script, 'wait': 1, },
                                    endpoint='execute',)

            request.meta['category'] = category
            request.meta['subcategory'] = subcategory
            yield request

    def parse_subcategory(self, response):

        category = response.meta['category']
        subcategory = response.meta['subcategory']

        for listing in response.xpath('//div[contains(@class,"search-result__info")]'):
            course = PluralsightItem()
            course['Course_Name'] = listing.xpath(
                'div[contains(@class,"title")]/a/text()').extract_first(default='').strip()
            link = listing.xpath('div[contains(@class,"title")]/a/@href').extract_first(default='')
            course['URL'] = 'https://www.pluralsight.com' + link if link else ''
            course['Instructors'] = listing.xpath(
                'div[contains(@class,"details")]/div[contains(@class,"author")]/a/text()').extract_first(default='').strip()
            if ' ' not in course['Instructors']:
                author_link = listing.xpath(
                    'div[contains(@class,"details")]/div[contains(@class,"author")]/a/@href').extract_first(default='')
                author_list = author_link.split('/')
                if len(author_list) > 1 and '-' in author_list[-1]:
                    author = author_list[-1].replace('-', ' ').title()
                    course['Instructors'] = author.strip()

            course['Provider'] = ''
            course['Difficulty'] = listing.xpath(
                'div[contains(@class,"details")]/div[contains(@class,"level")]/text()').extract_first(default='').strip()
            duration_text = listing.xpath(
                'div[contains(@class,"details")]/div[contains(@class,"length")]/text()').extract_first(default='')
            hours = float(hour_pattern.findall(duration_text)[0]) if hour_pattern.findall(duration_text) else 0
            minutes = float(minute_pattern.findall(duration_text)[0]) / 60.0 if minute_pattern.findall(duration_text) else 0
            course['Duration'] = str(round(hours + minutes, 2)).strip()
            created_text = listing.xpath(
                'div[contains(@class,"details")]/div[contains(@class,"date")]/text()').extract_first(default='')
            created = datetime.strptime(created_text, '%b %d %Y')
            course['Created'] = datetime.strftime(created, '%Y-%m-%d').strip()
            course['Category'] = category.strip()
            course['Subcategory'] = subcategory.strip()
            course['Language'] = 'English'
            review_text = ''.join(listing.xpath(
                'div[contains(@class,"details")]/div[contains(@class,"rating")]//text()').extract()).strip()
            count_list = pattern.findall(review_text)
            course['Number_of_reviews'] = count_list[0].strip() if count_list else ''
            full_star_count = len(listing.xpath(
                'div[contains(@class,"details")]//i[contains(@class,"fa-star") '
                'and not(contains(@class,"half")) '
                'and not(contains(@class,"gray"))]').extract())
            half_star_count = len(listing.xpath(
                'div[contains(@class,"details")]//i[contains(@class,"half")]').extract()) / 2.0
            course['Avg_rating'] = str(full_star_count + half_star_count).strip()
            yield course

    def errback_author(self, failure):
            try:
                url = failure.value.response.url
                category = failure.value.response.meta['category']
                subcategory = failure.value.response.meta['subcategory']
            except Exception:
                url = failure.request.url
                category = failure.request.meta['category']
                subcategory = failure.request.meta['subcategory']
            request = SplashRequest(url, callback=self.parse_author,
                                    args={'lua_source': script, 'wait': 10, },
                                    endpoint='execute',)
            request.meta['category'] = category
            request.meta['subcategory'] = subcategory
            yield request

    def errback_subcategory(self, failure):
            try:
                url = failure.value.response.url
                category = failure.value.response.meta['category']
                subcategory = failure.value.response.meta['subcategory']
            except Exception:
                url = failure.request.url
                category = failure.request.meta['category']
                subcategory = failure.request.meta['subcategory']
            request = SplashRequest(url, callback=self.parse_subcategory,
                                    args={'wait': 10, },)
            request.meta['category'] = category
            request.meta['subcategory'] = subcategory
            yield request
