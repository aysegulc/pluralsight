
Pluralsight Scraping Project
-------------------------

This scrapy project is built to extract information about online courses at pluralsight.

Details such as course name, author, duration, difficulty, average rating are scraped.

Scrapy-splash library is used to handle the cases that requires js-rendering such as loading multiple items.

Errback functions are implemented to catch errors in splash requests and for repeating the requests.

To scrape all available course data, spider searches the website by category, subcategory and author.

```bash
# Save items to csv file
scrapy crawl pluralsight -o online_course_data.csv
# save items to json file
scrapy crawl pluralsight -o online_course_data.json
```
