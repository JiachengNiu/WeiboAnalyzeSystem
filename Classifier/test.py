#-*-coding:utf-8-*-
import jieba
import web
def loaddata():
    f = open('worddict.txt', 'rb')
    items = f.readlines()
    worddict = {}
    for i in items:
        i = i.replace('\n', '').decode('utf8').split()
        if worddict.get(i[0]) == None:
            worddict.setdefault(i[0], {})
        worddict[i[0]].setdefault(i[1], float(i[2]))
    return worddict

def classify(content, worddict):
    types = {}
    for word in jieba.cut(content):
        if word in worddict:
            for type in worddict[word]:
                if types.get(type) == None:
                    types.setdefault(type, worddict[word][type])
                else:
                    types[type] += worddict[word][type]
    sorted_types = sorted(types.iteritems(), key=lambda a:a[1], reverse=True)
    results = [sorted_types[0]]
    for i in range(len(sorted_types)):
        #print sorted_types[i][0], sorted_types[i][1]
        if i > 0 and (sorted_types[i][1]/sorted_types[i-1][1]) > 0.87 and sorted_types[i][1]/sorted_types[0][1] > 0.7 and sorted_types[i][1] > 0.05 and len(results) < 3:
            results.append(sorted_types[i])
        elif i > 0:
            break
    return results

if __name__ == '__main__':

    worddict = loaddata()

    db = web.database(
        dbn='mysql',
        db='weibo',
        user='niujiac',
        pw='n353081024',
        host='120.77.44.206',
        port=3306
    )
    items = db.select('realtimehot')
    for i in items:
        content = i.keyword
        weibo_items = db.select('weiboitem', where='listid=$i.id', vars=locals())
        if len(weibo_items) == 0:
            continue
        for weibo in weibo_items:
            content += weibo.content
        print i.keyword
        results = classify(content, worddict)
        for result in results:
            print result[0], result[1]