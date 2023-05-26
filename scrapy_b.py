# -*- coding: utf-8 -*-
import random
import time
from bs4 import BeautifulSoup
from selenium import webdriver
import os
import pandas as pd
# import requests
from tqdm import tqdm
import math
import re
import datetime

# 这些始终要用到，作为全局，可以加快code运行速度
chrome_options = webdriver.ChromeOptions()
# 使用headless无界面浏览器模式
chrome_options.add_argument('--headless') # 增加无界面选项
chrome_options.add_argument('--disable-gpu') #如果不加这个选项，有时定位会出现问题
# 启动浏览器
driver = webdriver.Chrome(options=chrome_options)
# 隐式等待
driver.implicitly_wait(10)
# 防止被识别， 设置随机等待秒数
rand_seconds = random.choice([1, 3]) + random.random()

# 给url获取soup
def get_soup(url):
    # print(url)
    # 获取网页源代码
    driver.get(url)
    content = driver.page_source
    soup = BeautifulSoup(content, 'lxml')
    return soup


# 获取番剧的链接list
def getFirstContent(soup):
    # print(content)
    # soup = BeautifulSoup(content, "html.parser")
    # 搜索的页面出来得到视频部分信息
    next_urls = []
    infos = soup.find_all('a','bangumi-title')
    for info in infos:
        next_urls.append(info['href'].strip())
    # print(len(infos))

    return next_urls


# 获取番剧的一些信息
def getDetail(path,fname_detail):
    links_ = pd.read_csv(path)
    links = links_.drop_duplicates()  # 可能有重复的需要去重
    urls = links['links']
    cont_id = 0
    print("start!")
    v_ids = []  # id
    titles = []  # 标题
    genres = []  # 类型
    years = []  # 年份
    long_comms = []  # 长评论数
    short_comms = []  # 短评论数
    detail_link = []  # 当前页面链接
    for url2 in tqdm(urls):
        try:
            soup1 = get_soup(r'http:' + url2)
            next_link = soup1.find('a', 'mediainfo_media_desc_section__bOFBw')['href']
            soup2 = get_soup(r'http:' + next_link + r'#long')  # 长评页面

            '''
                soup2.find('div', 'media-tab-nav').find('ul').find_all('li'):
                [<li class="">作品详情</li>,
                 <li class="on">长评 ( 572 )</li>,
                 <li class="">短评 ( 117867 )</li>,
                 <li class="">相关视频</li>]
            '''
            # 评分数， '长评 ( 572 )' 取数字572,变为int,没有评论等信息的不需要，进行跳过
            try:
                long = int(soup2.find('div', 'media-tab-nav').find('ul').find_all('li')[1].string[5:-2])
                short = int(soup2.find('div', 'media-tab-nav').find('ul').find_all('li')[2].string[5:-2])
            except:
                long=0
                short=0
            long_comms.append(long)
            short_comms.append(short)
            # 取标题
            title = soup2.find('span', 'media-info-title-t').string
            titles.append(title)
            # 取标签
            tags = ''
            for tag in soup2.find('span', 'media-tags').children:
                tags = tags + str(tag.string) + ','  # tags='漫画改,战斗,热血,声控,'
            genres.append(tags)
            # 截取年份：'2019年4月7日开播'
            year = soup2.find('div','media-info-time').span.string
            years.append(year)

            # 增加id的
            v_ids.append(soup1.find('a','mediainfo_avLink__bN7nf').string)
            cont_id += 1
            # v_ids.append(cont_id)
            # 获取当前页面链接
            detail_link.append(r'http:' + next_link)

            # soup2.find('div','review-list-wrp type-long').find('ul').contents
            if cont_id % 10 == 0:
                print('已爬取%d条' % cont_id)
            # 每5条写入一次，防止中断导致数据丢失
            if cont_id % 5 == 0:
                # 写入
                Data_detail = {'v_id': v_ids, 'title': titles, 'genres': genres, 'year': years,
                               'long_comm': long_comms,
                               'short_comm': short_comms, 'detail_link': detail_link}
                wirte2csv(Data_detail, fname_detail)
                # 清空
                v_ids = []  # id
                titles = []  # 标题
                genres = []  # 类型
                years = []  # 年份
                long_comms = []  # 长评论数
                short_comms = []  # 短评论数
                detail_link = []  # 当前页面链接
            time.sleep(5)

        except Exception:
            pass
    return


# 获取番剧的相关推荐
def getRecommond(path,fname_detail):
    detail_data = pd.read_csv(path)
    detail_data_ = detail_data.drop_duplicates()  # 可能有重复的需要去重
    urls = detail_data_['detail_link']
    cont_id = 0
    print("start!")
    v_ids = []  # id
    rec_id = []  # 推荐id
    rec_title = []  # 推荐名字
    for url2 in tqdm(urls):
        try:
            soup1 = get_soup(url2)
            # 增加count
            cont_id += 1

            v_ids.append(detail_data_.loc[cont_id,'v_id'])
            # 获取推荐番剧的title
            tmp_title = []
            for title in soup1.find_all('div','slide-item-title'):
                tmp_title.append(title.string)
            rec_title.append(tmp_title)
            # 获取推荐番剧的link
            rec_links = []
            for l in soup1.find_all('div','slide-item-info'):
                rec_links.append(l.find('a')['href'])
            # 获取推荐番剧的id
            tmp_id = []
            for link in rec_links:
                soup2 = get_soup(r'http:'+link)
                tmp_id.append(soup2.find('a', 'av-link').string)

            rec_id.append(tmp_id)

            if cont_id % 10 == 0:
                print('已爬取%d条' % cont_id)

            # 每5条写入一次，防止中断导致数据丢失
            if cont_id % 5 == 0:
                # 写入
                Data_detail = {'v_id': v_ids, 'rec_id': rec_id,'rec_title':rec_title}
                wirte2csv(Data_detail, fname_detail)
                # 清空
                v_ids = []  # id
                rec_id = []  # 推荐id
                rec_title = []  # 推荐名字

            time.sleep(rand_seconds)

        except Exception:
            pass
    return



def process_time(rat_time):
    #  2020-05-07 len = 10
    if len(rat_time) == 10:
        return rat_time
    else:
        if len(re.findall(r'^\d+小时前$', rat_time)):
            return (datetime.datetime.now() - datetime.timedelta(hours=int(rat_time[:-3]))).strftime("%Y-%m-%d")

        elif len(re.findall(r'^\d+分钟前$', rat_time)):
            return (datetime.datetime.now()).strftime("%Y-%m-%d")

        elif rat_time == '昨天':
            return (datetime.datetime.now()-datetime.timedelta(days=1)).strftime("%Y-%m-%d")

        elif len(rat_time) == 5:  # 如果没有年份
            return str(datetime.datetime.now().year) + '-' + rat_time


# 滚动获取评论信息的方法
def get_rating(url,page_num):
    # 获取网页源代码
    driver.get(url)
    # driver.get(url + r'#long')
    # page_num = long_page_num
    id_names = []
    ratings = []
    rating_times = []
    # 循环几次  滚动几次
    for i in range(page_num):
        # 让浏览器执行简单的js代码，document.body.scrollHeight：窗口高度
        js = "window.scrollTo(0,document.body.scrollHeight)"
        driver.execute_script(js)
        time.sleep(rand_seconds)
        # 具体看网页是怎么样的，b站是滑动到哪里，上面的都会加载进来，因此选取滑动之后的网页
        if i == page_num-1:
            # 获取页面
            content = driver.page_source
            # 放入解析
            soup = BeautifulSoup(content, 'lxml')
            # 找到这页id
            for li in soup.find_all('li','clearfix'):
                id_names.append(li.find('div',re.compile('review-author-name')).string.strip())
                rat = len(li.find_all('i', 'icon-star icon-star-light'))  # 评分
                ratings.append(rat)

                rat_time = li.find('div', 'review-author-time').string
                # 对特殊时间做处理
                rat_time_2 = process_time(rat_time)
                rating_times.append(str(rat_time_2))

    return id_names,ratings,rating_times


# 获取rating，相关信息，并存入csv
def get_rating_data(path):
    detail = pd.read_csv(path)
    # print(min(detail['short_comm']+detail['long_comm']))  # 230;
    # print(detail.columns)  # ['v_id', 'title', 'genres', 'year', 'long_comm', 'short_comm','detail_link']
    minn = min(detail['short_comm'] + detail['long_comm'])
    rating_links = detail['detail_link']
    long_num = detail['long_comm']
    short_num = detail['short_comm']
    v_ids = detail['v_id']
    for ind, url in enumerate(tqdm(rating_links)):
        # print(ind,url)
        # if ind< 425:
        #     continue
        # 按比例取长短评价
        # print(v_ids[61])
        # 因为长评论会比短评论少，可能用单纯的通过最小总评论数进行比例计算，可能会出现长评数不够，最终会有一些数据的丢失，为此这里进行最小的比较
        lon = min(int((long_num[ind] / (long_num[ind] + short_num[ind])) * minn),long_num[ind])
        sho = minn - lon

        long_page_num = math.ceil(lon / 20)  # 一页20个数据，看需要滑动几页
        short_page_num = math.ceil(sho / 20)  # 一页20个数据，看需要滑动几页

        id_l, rat_l,time_l = get_rating(url + r'#long', long_page_num)
        id_s, rat_s,time_s = get_rating(url + r"#short", short_page_num)
        # print(len(id_l))
        # print(len(id_s))

        # 需要把之前的长短评价各自分配的数目取到
        id_total = id_l[0:lon]+id_s[0:sho]
        rat_total = rat_l[0:lon]+rat_s[0:sho]
        rating_time_total = time_l[0:lon]+time_s[0:sho]
        # print(len(id_total))
        # print(len(rat_total))

        # 封装到DataFrame
        Data_rating = {'user_id_name': id_total,'v_id':[v_ids[ind]]*minn,'rating':rat_total,'rating_time':rating_time_total}
        # print(Data_rating)
        fname_rating = "rating_data.csv"
        wirte2csv(Data_rating, fname_rating)
    return


# 写入csv
def wirte2csv(Data,fname):
    try:
        if os.path.exists(fname):
            DataFrame = pd.DataFrame(Data)
            DataFrame.to_csv(fname, index=False, sep=',', mode='a', header=False)
            print('追加成功！')
        else:
            DataFrame = pd.DataFrame(Data)
            DataFrame.to_csv(fname, index=False, sep=',')
            print('save!')
    except:
        print('fail')


if __name__ == '__main__':
    flag1 = 1  # 要不要爬取番剧列表页
    flag2 = 1  # 要不要爬取番剧信息
    flag3 = 1  # 要不要爬取评分
    flag4 = 1  # 要不要爬取相关推荐
    if flag1:
        # step1
        for i in tqdm(range(21)):
            # 从0开始的原因是，对于第一次访问的页面会连续访问两次，导致重复爬取，所以i=0时获取页面，但是不去存入信息
            # 剧番页面，从1-20页
            url = 'https://www.bilibili.com/anime/index/#season_version=-1&area=-1' \
              '&is_finish=-1&copyright=-1&season_status=-1&season_month=-1&year=-1' \
              '&style_id=-1&order=3&st=1&sort=0&page='+str(i+1)
            #  刷新，重要！！！否则可能会导致重复爬取第一个页面
            driver.refresh()
            # print(url)
            soup = get_soup(url)
            if i == 0:
                continue
            #driver.find_element_by_class_name('p next-page').click()
            next_urls = getFirstContent(soup)
            print(next_urls)
            # 写入csv
            Data_link = {'links': next_urls}
            fname_link = "link_data.csv"
            wirte2csv(Data_link, fname_link)
            print('爬到第%d页' % i)
            # 暂停
            time.sleep(5)
    if flag2:
        # step2
        path = r'./link_data.csv'
        # 爬取细节并存入新的csv
        getDetail(path,fname_detail = "video_data.csv")
    if flag3:
        # step3
        detail_data_path = r'./video_data.csv'
        get_rating_data(detail_data_path)
    if flag4:
        # step2
        path = r'./video_data.csv'
        # 爬取细节并存入新的csv
        getRecommond(path, fname_detail="recommend_data.csv")
    driver.close()
