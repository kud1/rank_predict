# -*- coding: utf-8 -*-
"""
Created on 2017/10/26 13:08

@author: zhangle
"""
import config

features = ['weight', 'agree_cnt', 'ques_focus_cnt', 'ques_view_cnt', 'category', 'search_rank']


def grouping(data):
    """
    数据分组，分成训练数据与测试数据两组
    :param data:
    :return:
    """
    import random
    random.shuffle(data)
    train_lable = list()
    train_target = list()
    test_lable = list()
    test_target = list()
    index = 0
    for item in data.items():
        index += 1
        if index/5 == 0:
            test_target.append(item['search_rank'])
            test_lable.append(item.values())
        else:
            train_target.append(item['search_rank'])
            train_lable.append(item.values())
    return train_lable, train_target, test_lable, test_target


def preprocess(data):
    """
    数据预处理
    :param data:
    :return:
    """
    results = list()
    for item in data:
        item['weight'] = _tf_idf(item.pop('kewyord'), item.pop('title')+'。'+item.pop('content'))
        result = dict()
        for feature in features:
            result[feature] = item[feature]
            results.append(result)
    return results


def clean(data):
    """
    数据清洗
    :param data:
    :return:
    """
    removed = list()
    for item in data:
        for feature in features:
            if not item.get(feature):
                removed.append(item)
    # return [x for x in data if x not in removed]
    for r in removed:
        data.remove(r)
    return data


def _tf_idf(keyword, text):
    """
    获取关键词的tf-idf值
    :param keyword:
    :param text:
    :return:
    """
    import jieba
    from sklearn.feature_extraction.text import TfidfTransformer
    from sklearn.feature_extraction.text import CountVectorizer

    keywords = jieba.lcut(keyword)
    text_cut = jieba.lcut(text)
    text_cut = [" ".join(text_cut)]

    vectorizer = CountVectorizer()
    transformer = TfidfTransformer()
    # 第一个fit_transform是计算tf-idf，第二个fit_transform是将文本转为词频矩阵
    tfidf = transformer.fit_transform(vectorizer.fit_transform(text_cut))
    word = vectorizer.get_feature_names()
    weight = tfidf.toarray()
    word_2_weight = dict()
    for i in range(len(word)):
        word_2_weight[word[i]] = weight[0][i]
    value = 0.0
    for key in keywords:
        if key in word_2_weight:
            value += word_2_weight[key]
    return value


def _word_rank(keyword, text):
    """
    利用jieba自带API获取关键词权重
    :return:
    """
    pass


def get_weight(site):
    """
    获取特征权重
    :param site:
    :return:
    """
    weight = config.get(site)
    for field in weight.keys():
        if field not in features:
            weight.pop(field)
    return weight


def read_data():
    import pymysql
    data = list()
    db = pymysql.connect(**config.DATASET_DB)
    db.cursor().execute('select count(1) from xxx')
    count = db.cursor().fetchone()[0]
    while count > 0:
        try:
            with db.cursor() as cursor:
                sql = ''
                cursor.execute(sql)
                rows = cursor.fetchall()
                data.extend(rows)
            db.commit()
        finally:
            db.close()
            count -= 1000
    data = clean(data)
    data = preprocess(data)
    data = grouping(data)
    return data

if __name__ == '__main__':
    _tf_idf('', '你的名字')
