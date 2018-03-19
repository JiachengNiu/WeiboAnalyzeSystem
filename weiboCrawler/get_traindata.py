# -*- coding: utf-8 -*-  
import urllib
import base64
import re
import json  
import rsa  
import binascii  
import requests  
from bs4 import BeautifulSoup
import csv
import time
import random


class weibo:
    def login(self, username, password):
        session = requests.Session()
        url_prelogin = 'http://login.sina.com.cn/sso/prelogin.php?entry=weibo&callback=sinaSSOController.preloginCallBack&su=&rsakt=mod&client=ssologin.js(v1.4.5)&_=1364875106625'
        url_login = 'http://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.4.5)'

        #get servertime,nonce, pubkey,rsakv
        resp = session.get(url_prelogin)
        json_data = re.findall(r'(?<=\().*(?=\))', resp.text)[0]
        data = json.loads(json_data)
        servertime = data['servertime']
        nonce = data['nonce']
        pubkey = data['pubkey']
        rsakv = data['rsakv']
        #print(urllib.parse.quote(username))
        su = base64.b64encode(username.encode(encoding="utf-8"))
        rsaPublickey= int(pubkey,16)
        key = rsa.PublicKey(rsaPublickey,65537)
        message = str(servertime) +'\t' + str(nonce) + '\n' + str(password)
        sp = binascii.b2a_hex(rsa.encrypt(message.encode(encoding="utf-8"),key))
        postdata = {
            'entry': 'weibo',
            'gateway': '1',
            'from': '',
            'savestate': '7',
            'userticket': '1',
            'ssosimplelogin': '1',
            'vsnf': '1',
            'vsnval': '',
            'su': su,
            'service': 'miniblog',
            'servertime': servertime,
            'nonce': nonce,
            'pwencode': 'rsa2',
            'sp': sp,
            'encoding': 'UTF-8',
            'url': 'http://weibo.com/ajaxlogin.php?framelogin=1&callback=parent.sinaSSOController.feedBackUrlCallBack',
            'returntype': 'META',
            'rsakv' : rsakv,
        }
        response = session.post(url_login, data=postdata)
        login_url = re.findall(r'http://weibo.*&retcode=0', response.text)[0]
        print ('登录成功')
        respo = session.get(login_url)
        uid = re.findall('"uniqueid":"(\d+)",', respo.text)[0]
        url = "http://weibo.com/u/"+uid
        print (url)
        return session

    def getpage(self, url):
        try:
            request = urllib.request.Request(url)
            response = urllib.request.urlopen(request)
            return response.read().decode('utf-8')
        except:
            print(u"连接失败")
            return None

    def getlist(self, session):
        stoplist = [u'视频', u'北京']
        page = session.get('http://d.weibo.com/').text
        soup = BeautifulSoup(page, "html.parser")
        script = soup.find_all('script')
        class_page = None
        for sc in script:
            if u'热门微博分类' in sc.string:
                #print(sc.string)
                class_page = json.loads(re.search('{.*?}', sc.string).group(0))['html']
                #print(class_page)
                break
        soup = BeautifulSoup(class_page, "html.parser")
        types = []
        li = soup.find_all('li', attrs={'class': 'li_text'})
        for l in li:
            text = str(l).replace('\n', '').replace('\t', '').strip()
            pair = re.search('href="(.*?)"><i class="item_icon">.*<span class="text width_fix W_autocut">(.*?)</span></a></li>', text).groups()
            if pair[1] not in stoplist:
                types.append([re.search('/(.*?)\?from', pair[0]).group(1), pair[1]])
        print(len(types), types)
        for t in types:
            print('http://d.weibo.com/'+t[0])
        for t in types:
            print(t[1])
        return types

    def setjsonurl(self, type, pagenum):
        if pagenum % 6 != 0:
            pagebar = pagenum % 6 - 1
            pre_page = int(pagenum / 6) + 1
            json_url = \
                'http://d.weibo.com/p/aj/v6/mblog/mbloglist?ajwvr=6&domain=' + type + '&from=faxian_hot&mod=fenle/page&pagebar=' + str(pagebar)\
                + '&tab=home&current_page=' + str(pagenum) + '&pre_page=' + str(pre_page) + '&page=' + str(pre_page) + '&pl_name=Pl_Core_NewMixFeed__3&id='\
                + type + '&script_uri=' + type + '&feed_type=1&domain_op=' + type
        else:
            pre_page = pagenum / 6
            json_url = \
                'http://d.weibo.com/p/aj/v6/mblog/mbloglist?ajwvr=6&domain=' + type + '&from=faxian_hot&mod=fenle&pre_page=' + str(pre_page) \
                + '&page=' + str(pre_page+1) + '&pre_page=' + str(pre_page) + '&pids=Pl_Core_NewMixFeed__3&current_page=' + str(pagenum) + '&since_id=&pl_name=Pl_Core_NewMixFeed__3&id=' \
                + type + '&script_uri=' + type + '&feed_type=1&domain_op=' + type

        print(json_url)
        return json_url

    def gettext(self, session, types):
        train_data = []
        file = open('train.txt', 'w', encoding='utf8')
        for item in types:
            print(item[1])
            number = 1
            for i in range(0, 200):
                json_url = self.setjsonurl(item[0], i)
                page = session.get(json_url).text
                content_page = json.loads(page)['data']
                #print(content_page)
                contents = re.findall('<div class="WB_text W_f14" node-type="feed_list_content">(.*?)</div>', content_page)
                if len(contents) == 0:
                    break
                for content in contents:
                    tags = re.findall('<.*?>', content)
                    content = content.replace('\n', '').strip()
                    for tag in tags:
                        content = content.replace(tag, '')
                    try:
                        print (item[1], number, content)
                        train_data.append([item[1], content])
                        file.write(item[1] + '|' + content + '\n')
                        number += 1
                    except:
                        pass
                page = None

        return train_data


if __name__ == '__main__':
    test = weibo()
    session = test.login('13717776265', 'n353081024')
    list_data = test.getlist(session)
    print(list_data)
    data = test.gettext(session, list_data)



