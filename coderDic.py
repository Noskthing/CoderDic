#!/usr/bin/env python
# -*- coding:utf-8 -*-

import urllib2
import urllib

import requests
from bs4 import BeautifulSoup
import json

import pyperclip

import re
import os
import time
import string
import sys
reload(sys)
sys.setdefaultencoding('utf8')   

__VERSION = "1.0.0"
__CODERDICNAME = "code_dic"
__BOUNDARY = "------AKOVNEAOIDJFJIAEIOF"
__ENV_WORK_PATH_KEY = "ENV_CODERDIC_PATH"

def __stringHandle(str):
    return str.replace(" ",'').replace("\n","")

def searchWord(word):
    # get html text
    request = urllib2.Request('http://www.baidu.com/s?wd='+urllib.quote(word + "翻译"))
    response = urllib2.urlopen(request)

    #parse html
    soup = BeautifulSoup(response.read(), "lxml")
    content = soup.find_all("div", {'class':"op_dict_content"})

    if content:
        print "\033[1;32m%s\033[0m" %('\n' + word + " 查询成功!")
        print "\033[0;32m%s\033[0m" %('===============================')
        print "\n"

        #get word symbol
        symbol = ''
        symbols_table = soup.find(class_="op_dict_table")
        symbol_trs = symbols_table.find_all("tr")
        for tr in symbol_trs:
            for td in tr.find_all('td'):
                symbol += __stringHandle(td.getText()) + ' '
            print "\033[0;36m%s\033[0m" %(symbol + '\n')
        
        #输错部分百度会进行联想，这步获取实际查询的单词
        realWord = symbol.split(' ')[0]
        os.system('say ' + realWord)

        print "\033[0;34m%s\033[0m" %'[翻译]'

        #get translations
        translations = []
        translation_table = soup.find_all(class_ = re.compile("op_dict3_english_result_table"));
        for tr in translation_table:
            translation = ''
            for td in tr.find_all('td'):
                temp = __stringHandle(td.getText())
                if temp == '[其他]': 
                    temp = "\033[0;34m%s\033[0m" %('\n' + temp + '\n')
                translations.append(temp);
                translation += temp + ' '
            print translation

        print '\n'
        
        #get words example
        #即使单词不对，百度会联想相关的单词；但是例句接口不能联想
        sentences = __fetchExampleSentences(realWord)

        res = {
                'symbol':symbol,
                'translation':translations,
                'example_sentences':sentences}
        
        writeCotent(json.dumps(res))

        print "\n"
        print "\033[0;32m%s\033[0m" %('===============================')
        print "\n"
    else:
        print "\033[1;31m%s\033[0m" %("Error: Not found " + word + "! Please check your word is correct!")

    
#例句部分的内容并不在我们获取的html页面当中，通过查看源码可以发现这是由js
#动态获取的。相关代码包含在<script>标签里，搜索 [例句] 关键字可得。
#
#利用Chrome可以捕获这部分的请求。结合js代码来看,请求方式是Get，参数是wd, cb, callback和_
#wd是word缩写，也就是我们需要查询的关键词；
#cb是固定前缀 'bd_cb_dict3_' 加上当前时间戳；
#callback是Ajax请求指定的回调名称，和cb参数一致；
#_是当前时间戳r
#
#参照请求当时的Header，我们构建了一个类似的Header来模拟发起这个请求
#这部分的请求非常的简单，所以开始我就尽量避免模拟浏览器的环境来得到结果
#
#返回的结果是一个json字符串。不过前面有一个 /**/ + cb 的前缀
#所以我们在获取response之后会做一个截断，然后再处理转化
#
#里面有三个key: 分别是err_no err_msg和liju_result
#请求成功的情况err_no = 0，err_msg = 'success'
#liju_result是一个数组，通常情况是有四个对象。
#前两个是数组，分别包含了我们需要的例句的信息。后面是一个字符串和一个数字，应该是来源和ID
#两个数组，第一个是英文的句子，第二个是中文的翻译，数组里面包含了N个小数组
#两个数组都是把句子拆分成小块，一个数组标示一个小块
#第一个对象就是单词本身；第二个对象是 w_x 的一个字符串，x是第几个部分
#第三个对象是一个以 , 分割的字符串，里面有 2-3 个 w_x，意义不明
#第四个对象是 0和1，标示这个是不是你查询的单词。配合前端着重标出
#第五个对象是可选的。因为中英文有一个区别在于中文的每个字是连贯的，包括标点符号，
#而英语每个单词之间是空格分开，但是标点这部分是不需要空格的。第五个对象一般是一个 ' ' 的字符串
#当拼接每个部分后面需要接空格时，就会存在
base_url = 'https://sp1.baidu.com/5b11fzupBgM18t7jm9iCKT-xh_/sensearch?'

refererStr = ('https://www.baidu.com/s?ie=utf-8&f=8&'
        'rsv_bp=1&'
        'tn=baidu&'
        'wd=well%20%E7%BF%BB%E8%AF%91&' 
       'oq=learn%2520%25E7%25BF%25BB%25E8%25AF%2591&' 
       'rsv_pq=8a7812c70001e773&' 
       'rsv_t=85ae5zPCwmuK3yQhbD%2BYFkooE%2BMpMYpZQ5kot35E%2FTPqoYXS6tHMjVP4%2BYo&' 
       'rqlang=cn&' 
       'rsv_enter=1&' 
       'rsv_sug3=5&' 
       'rsv_sug1=5&' 
       'rsv_sug7=100&' 
       'rsv_sug2=0&' 
       'inputT=1168&rsv_sug4=2102')

headers = {
    'Host': 'sp1.baidu.com',
    'Referer': refererStr,
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest',
}

def __fetchExampleSentences(word):
    cbName = "bd_cb_dict3_" + str(int(time.time()));
    params = {
        'wd': word,
        'cb': cbName,
        'callback': cbName,
        '_':  str(int(time.time()))
    }
    url = base_url + urllib.urlencode(params)
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:

            jsonStr = response.text[27:-1]
            jsonDic = json.loads(jsonStr)
            
            if not jsonDic['err_no'] == 0:
                print('Error: Get example sentence request fail! ', jsonDic["err_msg"])
                return null

            words = jsonDic['liju_result']
            print "\033[0;34m%s\033[0m" %'[例句]'

            sentences = []
            for x in xrange(0,2):
                temp = ''
                content = ''
                word = words[x]
                for char in word:
                    extraStr = ''
                    if len(char) == 5:
                        extraStr = char[4]
                    content += (str(char[0]) + extraStr)
                    if char[3] == 1:
                        temp += "\033[0;31m%s\033[0m" % (str(char[0]) + extraStr)
                    else:
                        temp += (str(char[0]) + extraStr)
                print temp
                sentences.append(content)
                
            return sentences
        else:
            print "\033[1;31m%s\033[0m" %('Error: Get example sentence response fail! ', response.status_code)
    except requests.ConnectionError as e:
        print "\033[1;31m%s\033[0m" %('Error: Get example sentence fail! ', e.args)
        return null

def writeCotent(jsonStr):
    path = os.getenv('ENV_CODERDIC_PATH')
    if not path:
        path = os.getcwd()
        os.putenv('ENV_CODERDIC_PATH', path)

    if not os.path.exists(path):
        print "\033[1;31m%s\033[0m" %('Error: Path "' + path + '" is not exist!')
        return

    filePath = os.path.join(path, __CODERDICNAME)

    with open(filePath, 'a+') as f:
        f.write(jsonStr + '\n')
        f.write(__BOUNDARY + '\n')


if __name__ == '__main__':

    content = pyperclip.paste()
    searchWord(str(content))

