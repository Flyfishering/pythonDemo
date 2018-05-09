#coding:utf-8
# import sys
# reload(sys)
# sys.setdefaultencoding('utf-8')
from __future__ import unicode_literals
from lxml import etree
import requests
import string
import re
from datetime import datetime
from class_mysql import Mysql

#获取各省市url
def parse(url):
    try:
        html=requests.get(base_url,headers=headers)
        html.encoding=('gb2312')
        selector=etree.HTML(html.text)
        city_urls=[base_url+str(url_href) for url_href in selector.xpath('//div[@class="contentBox"][4]/div[@class="cityBox"]/a/@href')]
        for city_url in city_urls:
            #回调解析各省市行业url
            get_industry_cominfo(city_url)
    except Exception as e:
        print ("parse函数解析错误 错误为 %s" % e)

#获取页面上各省市行业url 回调解析获取公司url函数
def get_industry_cominfo(url):
    try:
        html=requests.get(url,headers=headers)
        html.encoding=('gb2312')
        selector=etree.HTML(html.text)
        industry_index=len(selector.xpath('//div[@class="contentBox"][2]/div[@class="provinceBox"]'))
        industry_urls=[]
        for i in range(1,industry_index):
            industry_first_url=base_url+selector.xpath('//div[@class="contentBox"][2]/div[@class="provinceBox"][%s]/a/@href'%i)[0]
            industry_urls.append(industry_first_url)
            industry_second_urls=selector.xpath('//div[@class="contentBox"][2]/div[@class="cityBox"][%s]/a/@href'%i)
            for industry_second_url in industry_second_urls:
                industry_urls.append(base_url+str(industry_second_url))
        for industry_url in industry_urls:
            get_company_urls(industry_url)
    except Exception as e:
        print ("get_industry_cominfo函数解析错误 错误为 %s" % e)

#进入各城市行业 获取公司url函数 进而回调解析公司信息函数 正则匹配
def get_company_urls(url):
    try:
        html=requests.get(url,headers=headers)
        html.encoding=('gb2312')
        company_ids=re.findall(r'<a href="/company/(.*?).html">',html.content)
        for company_id in company_ids:
            company_url=base_url+'/company/'+ str(company_id)+ '.html'
            #print company_url
            get_company_info(company_url)
    except Exception as e:
        print ("get_company_urls函数解析错误 错误为 %s" % e)

def get_company_info(url):
    print url
    item={}
    html=requests.get(url,headers=headers)
    html.encoding=('gb2312')
    selector=etree.HTML(html.content)
    com_total=[]
    #com_name 在base_infos里面也可以取到 为了方便字段顺序 单独取出
    com_name=selector.xpath('//div[@class="contentBox"][2]/div[@class="provinceBox"]/text()')[0]
    #base_infos有的会有行业四级 有的是行业三级 这里做了判断 etl数据 处理      
    base_infos=selector.xpath('//div[@class="contentBox"][1]/div[@class="description"]/a[position()>1]/text()')
    #com_district和com_industry字段判断处理
    if len(base_infos)<4:
        com_industry=''
        pass
    else:
        com_industry='-'.join(base_infos[3:])
        base_infos=base_infos[:3]
    #左下角 地址 电话 传真这些信息 在一个列表里
    com_detail_infos=selector.xpath('//div[@class="contentBox"][2]/div[@class="cityBox"]/div[@style="float:left; width:350px; padding-top:10px;"]/text()')
    com_total.append(com_name)
    for base_info in base_infos:
        com_total.append(base_info)
    com_total.append(com_industry)
    for com_detail_info in com_detail_infos:
        com_total.append(string.replace(com_detail_info,u'\xa0', u' ').strip() )
    com_total.append(url)
    #抓取时间
    create_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    com_total.append(create_time)
    #enumerate(列表) 方法，对列表索引 和对应的索引值迭代 类似字典的items()方法
    for index,info in enumerate(com_total):
        #字典的key和列表的索引值+1相等 值也对应相等 方便调用自己写的类 用字典存储数据 插入数据库
        item[index+1]=com_total[index]
        #print index+1,info
    project.insert(item)
if __name__ == '__main__':
    headers={
    'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding':'gzip, deflate, sdch',    'Accept-Language':'zh-CN,zh;q=0.8',
    'Cache-Control':'max-age=0',
    'Connection':'keep-alive',
    'Cookie':'JSESSIONID=F73E95FB6C067621C3C6E0289051164E; Hm_lvt_80fcc762f620de80d6c7c3c96e353d8c=1495814622; Hm_lpvt_80fcc762f620de80d6c7c3c96e353d8c=1495814661',
    'Host':'www.socom.cn',
    'Upgrade-Insecure-Requests':'1',
    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36'
    }
    #入口url
    base_url='http://www.socom.cn'
    #字段列表
    Field_list=['com_name','com_province','com_city','com_district','com_industry',\
                'com_addr','com_phone','com_fax','com_mobile','com_url','com_email','com_contactor',\
                'com_emploies_nums','com_reg_capital','com_type','com_product','com_desc','page_url','create_time']
    #实例化操作mysql
    project=Mysql('s_socom_data',Field_list,len(Field_list))
    #删表
    project.delete()
    #建表后下面函数 先不要执行 com_desc 改为text类型 避免字段过长
    project.create_table()
    #获取各省市url
    parse(base_url)