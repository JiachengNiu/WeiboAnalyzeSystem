#-*-coding:utf-8-*-
import jieba
import web
from sklearn.externals import joblib

def loaddata():
    count_vect = joblib.load('count.t')
    tfidf_transformer = joblib.load('tfidf.t')
    NB_clf = joblib.load('NB.model')
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
        user='niujiac',
        pw='n353081024',
        host='120.77.44.206',
        port=3306
    )
if __name__ == '__main__':
    items = db.select('realtimehot', where='type is NULL or type=""')
    word_id = build_word_id(items)
    classify(word_id)
