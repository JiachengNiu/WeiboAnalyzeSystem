# -*- coding: utf-8 -*-  
import urllib
import urllib2
import base64
import re
import json  
import rsa  
import binascii  
import requests  
from bs4 import BeautifulSoup
import time
import web
import random
import jieba
from sklearn.externals import joblib

def loaddata():
    count_vect = joblib.load('model/count.t')
    tfidf_transformer = joblib.load('model/tfidf.t')
    NB_clf = joblib.load('model/NB.model')
    return NB_clf, count_vect, tfidf_transformer


def onetype(content, NB_clf, count_vect, tfidf_transformer):
    try:
        data = [" ".join(jieba.cut(content))]
        count_data = count_vect.transform(data)
        predicted = NB_clf.predict(count_data)
        return predicted[0]
    except:
        return 'Other'
def build_word_id(items):
    word_id = {}
    for i in items:
        if i.keyword not in word_id:
            word_id.setdefault(i.keyword, [i.id])
        else:
            word_id[i.keyword].append(i.id)
    return word_id

def classify(word_id):
    for word in word_id:
        content = word
        weibo_items = db.select('weiboitem', where='hotspot=$word', vars=locals())
        for weibo in weibo_items:
            content += weibo.content
        print word,
        atype = onetype(content, NB_clf, count_vect, tfidf_transformer).encode('utf8')
        print atype
        for id in word_id[word]:
            db.query('UPDATE realtimehot SET type = $type WHERE id=$id', vars={'type': atype, 'id': id})

NB_clf, count_vect, tfidf_transformer = loaddata()
db = web.database(
        dbn='mysql',
        db='weibo',
        user='root',
        pw=''
    )

class weibo:
    def __init__(self):
        self.db = web.database(dbn='mysql', db='weibo', user='niujiac', pw='n353081024')
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
            request = urllib2.Request(url)
            response = urllib2.urlopen(request)
            return response.read().decode('utf-8')
        except urllib2.URLError, e:
            print u"连接失败,错误原因",e.reason
            return None

    def getlist(self):
        page = self.getpage('http://s.weibo.com/top/summary?cate=realtimehot')
        soup = BeautifulSoup(page, "html.parser")
        script = soup.find_all('script')
        for sc in script:
            if sc.string and "<\/td>" in sc.string:
                #print(re.findall('{.*}', sc.string)[0])
                x = json.loads(re.findall('{.*}', sc.string)[0], encoding="utf-8")
                break
        data = x['html']
        data = str(data.encode('utf8')).replace('\n', '')
        #print(data)
        ranks = re.findall('<em>(.*?)</em></span></td>', data)
        links = re.findall('<td class="td_02"><div class="rank_content"><p class="star_name">   <a href="(.*?)" target="_blank"', data)
        titles = re.findall('<a href=".*?" target="_blank"    suda-data="key=tblog_search_list&value=.*?">(.*?)</a>', data)
        numbers = re.findall(' <td class="td_03"><p class="star_num"><span>(.*?)</span></p></td>', data)
        list_data = []
        for i in range(len(ranks)):
            try:
                print ranks[i], titles[i], numbers[i]
                list_data.append([ranks[i],('http://s.weibo.com'+links[i]).replace('Refer=top', 'nodup=1'), titles[i], numbers[i]])
            except:
                time.sleep(30)
                return self.getlist()
        return list_data

    def insertdb(self, listdata):
        date = str(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
        for item in list_data:
            self.db.insert('realtimehot', rank=item[0], link=item[1], keyword=item[2], freq=item[3], date=date)
        print date, 'Hotlist插入数据库成功'
        return date

    def gettext(self, listdata):
        rank = 1
        for item in listdata:
            weiboitems = self.db.select('weiboitem', where='hotspot=$item[2]', vars=locals())
            print 'rank:', rank, ' keyword:', item[2]
            if weiboitems != None and len(weiboitems) > 1:
                print str(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))), item[2], '微博已存在----', rank, '----'
                rank += 1
                continue
            page = self.getpage(item[1])
            #page = session.get(item[1]).text
            soup = BeautifulSoup(page, "html.parser")
            script = soup.find_all('script')
            x = None
            for sc in script:
                if sc.string and '"pid":"pl_weibo_direct"' in sc.string:
                    x = json.loads(re.findall('{.*}', sc.string)[0], encoding="utf-8")
                    break
            try:
                data = x['html']
            except:
                print "被封了", "http://s.weibo.com"
                return 0
            #print data
            soup = BeautifulSoup(data, "html.parser")
            contents = soup.find_all('p', {"class": "comment_txt"})
            for i in range(len(contents)):
                try:
                    print i, contents[i].text.replace('\n', '').strip()
                    text = contents[i].text.replace('\n', '').strip()
                    self.db.insert('weiboitem', hotspot=item[2], content=text)
                except:
                    print i, contents[i].text.replace('\n', '').strip(), 'Unicode error'
                    pass
            print str(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))), item[2], '微博抓取完毕----', rank, '----'
            rank += 1
            time.sleep(random.randint(50, 70))
        return 1
            


if __name__ == '__main__':
    while True:
        test = weibo()
        #session = test.login('13717776265', 'n353081024')
        list_data = test.getlist()
        program_start = time.time()
        test.insertdb(list_data)
        is_true = test.gettext(list_data)
        if not is_true:
            print str(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))), 'Spider Over'
            break
        items = db.select('realtimehot', where='type=NULL or type=""')
        word_id = build_word_id(items)
        classify(word_id)
        
        program_end = time.time()
        program_runtime = round((program_end - program_start) , 1)
        if program_runtime < 600:
            time.sleep(600 - program_runtime)
        print str(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))), '----Finish Once Successfully----'

