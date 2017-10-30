DATASET_DB = {
    "host": "123.206.214.163",
    "password": "ZhangLe@0910",
    "db": "rank_yuce",
    "user": "zhangle",
    "charset": "utf8",
}

# 为每个feature设置weight
WEIGHT = {
    'zhihu': {
        'agree_cnt': 1,
        'against_cnt': 1,
        'comment_cnt': 1,
        'ques_focus_cnt': 1,
        'ques_view_cnt': 1,
        'ques_ans_cnt': 1,
        'title_tf_idf': 2,
        'content_tf_idf': 1,
        'author_ans_cnt': 1,
        'author_follower_cnt': 1,
        'author_article_cnt': 1,
        'author_name': 1,
        'search_rank': 1,
        'ques_inner_rank': 1,
        'category': 1,
    }
}