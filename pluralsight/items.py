# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class PluralsightItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
	Course_Name = scrapy.Field()
	Instructors = scrapy.Field()
	Provider = scrapy.Field()
	#Availability = scrapy.Field()
	#Pacing_Type = scrapy.Field()
	#Mobile_Available = scrapy.Field()
	Difficulty  = scrapy.Field()
	Duration  = scrapy.Field()
	#Weeks_per_Course = scrapy.Field()
	#Hours_per_Week = scrapy.Field()
	#Course_Effort = scrapy.Field()
	#Total_Effort = scrapy.Field()
	#Start_Date = scrapy.Field()
	Created = scrapy.Field()
	#Course_Type = scrapy.Field()
	#Assoc_Prog = scrapy.Field()
	Category = scrapy.Field()
	Subcategory  = scrapy.Field()
	Language = scrapy.Field()
	Number_of_reviews = scrapy.Field()
	Avg_rating = scrapy.Field()
	#Short_Description = scrapy.Field()
	URL = scrapy.Field()
	pass
