#-*-coding:utf-8-*-
import jieba
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.naive_bayes import MultinomialNB
from sklearn.externals import joblib
import csv


stoplist = [u'nbsp', u'xb0', u'quot', u'12', u'一个', u'170511', u'170512', u'gt', u'lr', u'hiv', u'展开', u'全文', u'秒拍', u'视频', u'微博']

def loaddata():
    f = open('train.txt', 'rb')
    items = f.readlines()
    distinctitems = []
    for i in items:
        if i not in distinctitems:
            distinctitems.append(i)
    contents = []
    types = []
    for i in distinctitems:
        i = i.replace('\n', '').strip().decode('utf8')
        if len(i.split('|')[0]) > 1 and len(i.split('|')[1]) > 8:
            words = jieba.cut(i.split('|')[1])
            content = ''
            for word in words:
                if not word in stoplist:
                    content = content + word + ' '
            contents.append(content)
            types.append(i.split('|')[0])
    print len(items)
    return types, contents

def dictdata(types, contents):
    dict = {}
    for i in range(len(types)):
        if types[i] not in dict:
            dict.setdefault(types[i], contents[i])
        else:
            dict[types[i]] += contents[i]
    return dict

def worddict(sum_types, sum_contents):
    word_dict = {}
    vectorizer = CountVectorizer()  # 该类会将文本中的词语转换为词频矩阵，矩阵元素a[i][j] 表示j词在i类文本下的词频
    transformer = TfidfTransformer()  # 该类会统计每个词语的tf-idf权值
    tfidf = transformer.fit_transform(
        vectorizer.fit_transform(sum_contents))  # 第一个fit_transform是计算tf-idf，第二个fit_transform是将文本转为词频矩阵
    word = vectorizer.get_feature_names()  # 获取词袋模型中的所有词语
    weight = tfidf.toarray()  # 将tf-idf矩阵抽取出来，元素a[i][j]表示j词在i类文本中的tf-idf权重
    for i in range(len(weight)):  # 打印每类文本的tf-idf词语权重，第一个for遍历所有文本，第二个for便利某一类文本下的词语权重
        for j in range(len(word)):
            if word[j] not in word_dict and weight[i][j] > 0.01:
                word_dict.setdefault(word[j], {})
            if weight[i][j] > 0.01:
                word_dict[word[j]].setdefault(sum_types[i], weight[i][j])
    return word_dict

def NBtrain(dataset, types):
    NB_clf = MultinomialNB().fit(dataset, types)
    return NB_clf

def dealtest(testdata, count_vect, tfidf_transformer):
    data = []
    for i in testdata:
        data.append(" ".join(jieba.cut(i)))
    count_data = count_vect.transform(data)
    tfidf_data = tfidf_transformer.transform(count_data)
    return count_data

if __name__ == '__main__':
    types, contents = loaddata()
    '''
    dict = dictdata(types, contents)
    sum_contents = []
    sum_types = []
    for i in dict:
        sum_types.append(i)
        sum_contents.append(dict[i])
    word_dict = worddict(sum_types, sum_contents)
    f = open('worddict.txt', 'w')
    for word in word_dict:
        for type in word_dict[word]:
            #writer.writerow([word.encode('utf8').decode('gb2312'), type.encode('utf8').decode('gb2312'), word_dict[word][type]])
            print word, type, word_dict[word][type]
            f.write(word.encode('utf8') + ' ' + type.encode('utf8') + ' ' + str(word_dict[word][type]).encode('utf8'))
            f.write('\n')
    f.close()
    '''
    tfidf_transformer = TfidfTransformer()
    count_vect = CountVectorizer()
    count_data = count_vect.fit_transform(contents)
    tfidf_data = tfidf_transformer.fit_transform(count_data)

    NB_clf = NBtrain(count_data, types)

    joblib.dump(tfidf_transformer, 'tfidf.t')
    joblib.dump(count_vect, 'count.t')
    joblib.dump(NB_clf, 'NB.model')

    test = contents
    testset = dealtest(test, count_vect, tfidf_transformer)
    predicted = NB_clf.predict(testset)
    '''
    for t, i in zip(test,predicted):
        print t, i
    '''
    lenth = len(predicted)
    number = 0
    for i in range(lenth):
        print predicted[i], types[i]
        if(predicted[i] == types[i]):
            number += 1
    print float(number)/lenth




    
