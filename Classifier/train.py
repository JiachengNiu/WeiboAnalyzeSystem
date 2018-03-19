#-*-coding:utf-8-*-
import jieba
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
import csv


stoplist = [u'nbsp', u'xb0', u'quot', u'12', u'一个', u'170511', u'170512', u'gt', u'lr', u'hiv', u'展开', u'全文', u'秒拍', u'视频', u'微博']

def loaddata():
    f = open('train.txt', 'rb')
    items = f.readlines()
    f.close()
    distinctitems = []
    for i in items:
        if i not in distinctitems:
            distinctitems.append(i)
    contents = []
    types = []
    type_content = {}
    for i in distinctitems:
        i = i.replace('\n', '').strip().decode('utf8')
        if len(i.split('|')[0]) > 1 and len(i.split('|')[1]) > 8:
            if i.split('|')[0] not in type_content:
                type_content.setdefault(i.split('|')[0], [i.split('|')[1]])
            else:
                type_content[i.split('|')[0]].append(i.split('|')[1])
            words = jieba.cut(i.split('|')[1])
            content = ''
            for word in words:
                if not word in stoplist:
                    content = content + word + ' '
            contents.append(content)
            types.append(i.split('|')[0])
    print len(distinctitems)
    f1 = open('train1.txt', 'w')
    for type in type_content:
        for content in type_content[type]:
            f1.write(type.encode('utf8') + '|' + content.encode('utf8') + '\n')
    f1.close()
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

if __name__ == '__main__':
    types, contents = loaddata()
    print len(set(types))
    print '[',
    for i in set(types):
        print "u'" + i + "', ",
    print ']'
    print types

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
            print word, type, word_dict[word][type]
            f.write(word.encode('utf8') + ' ' + type.encode('utf8') + ' ' + str(word_dict[word][type]).encode('utf8'))
            f.write('\n')
    f.close()
