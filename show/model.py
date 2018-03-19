# -*- coding: utf-8 -*-
import web
import jieba
from sklearn.externals import joblib
from os import path
from scipy.misc import imread
import matplotlib.pyplot as plt
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
from urllib import quote

db = web.database(
    dbn='mysql',
    db='weibo',
    user='root',
    pw=''
)

def get_items():
    return db.select('realtimehot', order='date DESC, rank ASC', limit=1000)

def get_item(keyword):
    '''
    try:
        item = db.select('realtimehot', where='id=$id', vars=locals())[0]
    except IndexError:
        print 'error'
        return None, None, None
    keyword = item.keyword
    '''
    items = db.select('realtimehot', where='keyword=$keyword', order='date ASC', vars=locals())
    dates = []
    freqs = []
    for item in items:
        dates.append(str(item.date)[5:].encode('utf8'))
        freqs.append(int(item.freq))
    items = db.select('weiboitem', where='hotspot=$keyword', order='id ASC', vars=locals())
    content = keyword
    for i in items:
        content += i.content
    items = db.select('weiboitem', where='hotspot=$keyword', order='id ASC', vars=locals())
    results, wordfreq, types, values, type = get_content_tags(content)
    words = sorted(wordfreq.iteritems(), key=lambda a:a[1], reverse=True)

    generate_cloud(keyword, wordfreq)
    #imgsrc = 'static/pictures/' + quote(keyword.decode('utf8').encode('gb2312')) + '.png'
    imgsrc = '/static/pictures/' + quote(keyword.encode('gb2312')) + '.png'
    
    if len(words) > 20:
        words = words[0:20]
        
    return dates, freqs, items, results, words, types, values, type, imgsrc

def generate_cloud(keyword, words):
    #if path.exists("static/pictures/" + keyword.decode('utf8') + ".png") and keyword != 'data':
    if path.exists("static/pictures/" + keyword + ".png") and keyword != 'data':
        return
    bgpicture = imread("static/pictures/base1.png")
    wc = WordCloud(background_color="white", #背景颜色
    max_words=3000,# 词云显示的最大词数
    mask=bgpicture,#设置背景图片
    stopwords=STOPWORDS.add("said"),
    #max_font_size=40, #字体最大值
    random_state=50,
    width=600,height=450)
    try:
        wc.generate_from_frequencies(words)
    except:
        wc.generate_from_frequencies({'None':1})
    image_colors = ImageColorGenerator(bgpicture)
    wc.recolor(color_func=image_colors)
    #wc.to_file("static/pictures/" + keyword.decode('utf8') + ".png")
    wc.to_file("static/pictures/" + keyword + ".png")

def get_timeline():
    total = db.select('realtimehot', order='date DESC, rank ASC')
    dict_word = {}
    dict_time = {}
    for item in total:
        if dict_word.get(item.keyword) == None:
            dict_word.setdefault(item.keyword, [item])
        else:
            dict_word[item.keyword].append(item)
    for word in dict_word:
        freq_items = sorted(dict_word[word], key=lambda a:a.freq, reverse=True)
        time_items = sorted(dict_word[word], key=lambda a:a.date)
        if time_items[0].rank <= 50:
            if dict_time.get(time_items[0].date) == None:
                dict_time.setdefault(time_items[0].date, [[time_items[0], 0]])
            else:
                dict_time[time_items[0].date].append([time_items[0], 0])
        if freq_items[0] != time_items[0] and freq_items[0] != time_items[-1] and freq_items[0].rank <=50:
            if dict_time.get(freq_items[0].date) == None:
                dict_time.setdefault(freq_items[0].date, [[freq_items[0], 1]])
            else:
                dict_time[freq_items[0].date].append([freq_items[0], 1])
    for date in dict_time:
        dict_time[date].sort(key = lambda a:a[0].rank)
        dict_time[date].sort(key = lambda a:a[1], reverse=True)
    return dict_time

def get_weibo():
    return db.query('SELECT realtimehot.id, type, link, rank, keyword, date, freq, content FROM realtimehot INNER JOIN weiboitem ON keyword = hotspot ORDER BY date DESC , rank ASC , realtimehot.id DESC LIMIT 2000')

def search(x):
    keys = ['keywords', 't_rank', 't_type', 't_keyword', 't_date', 't_freq']
    for key in keys:
        if not key in x:
            x[key] = None
    query = 'SELECT * FROM realtimehot WHERE '
    is_true = 0
    flag = ''
    
    if x['keywords'] != None and x['keywords'] != '':
        query += 'keyword like"%' + x['keywords'] + '%"'
        flag = ' AND '
        is_true = 1
    
    if x['t_rank'] != None and x['t_rank'] !='':
        if x['t_rank'] == '1 - 3':
            query = query + flag + 'rank<=3'
            flag = ' AND '
            is_true = 1
        elif x['t_rank'] == '4 - 10':
            query = query + flag + 'rank>3 AND rank<=10'
            flag = ' AND '
            is_true = 1
        elif x['t_rank'] == '11 - 50':
            query = query + flag + 'rank>10'
            flag = ' AND '
            is_true = 1

    if x['t_type'] != None and x['t_type'] != '':
        query = query + flag + 'type="' + x['t_type'] +'"'
        flag = ' AND '
        is_true = 1
    
    if x['t_keyword'] != None and x['t_keyword'] != '':
        query = query + flag + 'keyword="' + x['t_keyword'] +'"'
        flag = ' AND '
        is_true = 1

    if x['t_date'] != None and x['t_date'] != '':
        query = query + flag + 'date="' + x['t_date'] + '"'
        flag = ' AND '
        is_true = 1

    if x['t_freq'] != None and x['t_freq'] !='':
        if x['t_freq'] == '<= 30000':
            query = query + flag + 'freq<=30000'
            is_true = 1
        elif x['t_freq'] == '30001 - 100000':
            query = query + flag + 'freq>30000 AND freq<=100000'
            is_true = 1
        elif x['t_freq'] == '100001 - 500000':
            query = query + flag + 'freq>100000 AND freq<=500000'
            is_true = 1
        elif x['t_freq'] == '> 500000':
            query = query + flag + 'freq>500000'
            is_true = 1

    if is_true:
        query += ' ORDER BY date DESC, rank ASC'
    else:
        query += '1 ORDER BY date DESC, rank ASC'

    print query
    if x['t_date'] != None and x['t_date'] != '':
        try:
            x['t_date'] = db.query(query)[0].date
        except:
            pass
    return db.query(query), x

def get_content_tags(content):
    def loaddata():
        count_vect = joblib.load('classifier/count.t')
        tfidf_transformer = joblib.load('classifier/tfidf.t')
        NB_clf = joblib.load('classifier/NB.model')
        f = open('classifier/worddict.txt', 'rb')
        items = f.readlines()
        worddict = {}
        for i in items:
            i = i.replace('\n', '').decode('utf8').split()
            if worddict.get(i[0]) == None:
                worddict.setdefault(i[0], {})
            worddict[i[0]].setdefault(i[1], float(i[2]))
        return worddict, NB_clf, count_vect, tfidf_transformer

    def classify(content, worddict):
        stopwords = ['...', '\r\n', '\n']
        types = {}
        wordfreq = {}
        values = []
        typelist = []
        for word in jieba.cut(content):
            if word in wordfreq:
                wordfreq[word] += 1
            elif len(word) > 1 and word not in stopwords:
                wordfreq.setdefault(word, 1)
            if word in worddict:
                for type in worddict[word]:
                    if types.get(type) == None:
                        types.setdefault(type, worddict[word][type])
                    else:
                        types[type] += worddict[word][type]
        sorted_types = sorted(types.iteritems(), key=lambda a:a[1], reverse=True)
        if len(wordfreq) == 0:
            for word in jieba.cut(content):
                if word in wordfreq:
                    wordfreq[word] += 1
                else:
                    wordfreq.setdefault(word, 1)
        words = sorted(wordfreq.iteritems(), key=lambda a:a[1], reverse=True)
        if len(sorted_types) == 0:
            return [], wordfreq, [], []
        results = [sorted_types[0]]
        for i in range(len(sorted_types)):
            #print sorted_types[i][0], sorted_types[i][1]
            if i > 0 and sorted_types[i][1] > 0.05 and sorted_types[i][1]/sorted_types[0][1] > 0.66 and len(results) < 5:
                results.append(sorted_types[i])
            elif i > 0:
                break
        for i in range(min(10, len(sorted_types))):
            typelist.append(sorted_types[i][0])
            values.append(sorted_types[i][1])
        return results, wordfreq, typelist, values

    def onetype(content, NB_clf, count_vect, tfidf_transformer):
        try:
            data = [" ".join(jieba.cut(content))]
            count_data = count_vect.transform(data)
            predicted = NB_clf.predict(count_data)
            return predicted[0]
        except:
            return 'Other'
        

    worddict, NB_clf, count_vect, tfidf_transformer = loaddata()
    results,wordfreqs, types, values = classify(content, worddict)
    type = onetype(content, NB_clf, count_vect, tfidf_transformer)
    return results, wordfreqs, types, values, type
    
    
