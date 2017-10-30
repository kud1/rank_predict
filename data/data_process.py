# -*- coding: utf-8 -*-
"""
Created on 2017/10/26 13:08

@author: zhangle
"""
import config

features = ['title_tf_idf', 'content_tf_idf', 'agree_cnt', 'ques_focus_cnt', 'ques_view_cnt', 'category', 'search_rank']


def preprocess(data):
    """
    数据预处理
    :param data:
    :return:
    """
    lables = list()
    targets = list()
    weights = dict()
    all_weights = feature_weight('zhihu')
    for item in data:
        keyword = item.pop('keyword')
        if item.get('title'):
            item['title_tf_idf'] = _tf_idf(keyword, item.pop('title'))
        if item.get('content'):
            item['content_tf_idf'] = _tf_idf(keyword, item.pop('content'))
        result = dict()
        for feature in features:
            result[feature] = item[feature]
            if feature not in weights.keys():
                weights[feature] = all_weights[feature]

        rank = int(result.pop('search_rank'))
        target = rank // 3
        if rank % 3:
            target += 1
        targets.append(target)
        lables.append(list(result.values()))
    return lables, targets, list(weights.values())


def clean(data):
    """
    数据清洗
    :param data:
    :return:
    """
    removed = list()
    for item in data:
        for feature in features:
            if item.get(feature) is None:
                removed.append(item)
                break
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
    import jieba.analyse
    return jieba.analyse.extract_tags(text, topK=1000, withWeight=False, allowPOS=())


def feature_weight(site):
    """
    获取特征权重
    :param site:
    :return:
    """
    weight = config.WEIGHT.get(site)
    # for field in weight.keys():
    #     if field not in features:
    #         weight.pop(field)
    return weight


def _get_text(elem):
    rc = []
    for node in elem.itertext():
        rc.append(node.strip())
    return ''.join(rc)


def read_data():
    import pymysql
    from lxml.html import fromstring
    data = list()
    db = pymysql.connect(**config.DATASET_DB)
    with db.cursor() as cursor:
        cursor.execute('select keyword from rank_yuce.zhihu_question group by keyword having(count(keyword)) <> 50')
        results = cursor.fetchall()
        matched_keywords = list()
        for r in results:
            matched_keywords.append(r[0])
    with db.cursor() as cursor:
        cursor.execute("select count(1) from zhihu_question where keyword not in ('%s')" % "','".join(matched_keywords))
        count = cursor.fetchone()[0]
    # count = 1000
    while count > 0:
        try:
            with db.cursor() as cursor:
                sql = 'select keyword, title, support_num, comment_num, rank, ' \
                      'concerned_num, browse_num, p_ans_num, p_article_num, ' \
                      'p_concerned_num, que_type, context from zhihu_question where keyword not in ("%s") limit 1000' \
                      % '","'.join(matched_keywords)
                cursor.execute(sql)
                rows = cursor.fetchall()
                for row in rows:
                    item = {
                        'keyword': row[0],
                        'title': row[1],
                        'agree_cnt': row[2],
                        'comment_cnt': row[3],
                        'search_rank': row[4],
                        'ques_focus_cnt': row[5],
                        'ques_view_cnt': row[6],
                        'author_ans_cnt': row[7],
                        'author_article_cnt': row[8],
                        'author_follower_cnt': row[9],
                        'category': row[10],
                    }
                    if row[11]:
                        content = row[11]
                        tree = fromstring(content)
                        content = _get_text(tree)
                        item['content'] = content
                    else:
                        item['content'] = ''
                    item['content_tf_idf'] = 0.0
                    item['title_tf_idf'] = 0.0
                    data.append(item)
            db.commit()
        finally:
            count -= 1000
    db.close()
    data = clean(data)
    data = preprocess(data)
    return data

if __name__ == '__main__':
    # _tf_idf('', '你的名字')
    read_data()
    # from lxml.html import fromstring
    # content = """
    #     <img src="https://pic3.zhimg.com/50/532c512a81f6491f60c3764d632297ba_b.jpg" data-rawwidth="838" data-rawheight="523" class="origin_image zh-lightbox-thumb" width="838" data-original="https://pic3.zhimg.com/50/532c512a81f6491f60c3764d632297ba_r.jpg">重庆这个火辣辣的山城，曾经的陪都，现在的直辖市。这里有可以媲美香港的无敌夜景，有乱人眼球的吸睛美女，还有热腾腾的火锅和酣畅淋漓的冰镇啤酒…<br>整理了一下具有代表性的<b>“最”重庆的好去处</b>，带给你极致的重庆旅行体验，跟着这份重庆最地图去浪吧！<br><br>PS：文末有重庆土著的精彩推荐哟~<br><br><h2><b>“最”文艺：</b></h2><ul><li><strong>四川美术学院（黄桷坪校区）</strong><br></li></ul><img src="http://pic2.zhimg.com/aff8e428f101f2b59e1bd0b8b02f374d_b.jpg" data-rawwidth="600" data-rawheight="337" class="origin_image zh-lightbox-thumb" width="600" data-original="http://pic2.zhimg.com/aff8e428f101f2b59e1bd0b8b02f374d_r.jpg"><img src="http://pic1.zhimg.com/043707adc8e1a91613cae4400cf57f28_b.jpg" data-rawwidth="600" data-rawheight="337" class="origin_image zh-lightbox-thumb" width="600" data-original="http://pic1.zhimg.com/043707adc8e1a91613cae4400cf57f28_r.jpg">川美，不能错过的小清新文艺地。至少你应该听过坦克库，微缩版的798，处处都能给你惊喜。毕业季的6月还能看到毕业生的设计作品展。有校园情结的，来这里肯定会喜欢。美院里的看点有三处：<b>美术馆</b>、<b>坦克库</b>和学校外面的<b>涂鸦街</b>。最有名的是学校外面的涂鸦街，一整条街的建筑满墙都是各种涂鸦，涂鸦略显旧了但还是挺壮观的。周围的小吃比较多，<b>梯坎豆花</b>、<b>胡记蹄花汤</b>都在这里，值得一试。另外毕业季的时候，每年大约五月底六月初，川美都有艺术生的<b>毕业展</b>，喜欢的可以关注一下相关信息，前往参观。<br><br>到达方式：轻轨<b>2号线</b>在<b>杨家坪</b>下车，转公交车或的士一个起步价在<b>黄桷坪</b>站或<b>四川美院</b>站下车。<br><br><ul><li><b>方所书店</b></li></ul><img src="http://pic2.zhimg.com/5163bb797705b612c688e13241bfc4b9_b.jpg" data-rawwidth="1200" data-rawheight="787" class="origin_image zh-lightbox-thumb" width="1200" data-original="http://pic2.zhimg.com/5163bb797705b612c688e13241bfc4b9_r.jpg"><img src="http://pic1.zhimg.com/4f3982d71a900d4926cf12cce4121f80_b.jpg" data-rawwidth="1200" data-rawheight="795" class="origin_image zh-lightbox-thumb" width="1200" data-original="http://pic1.zhimg.com/4f3982d71a900d4926cf12cce4121f80_r.jpg">方所不仅仅是一家书店，由“例外”创始人毛继鸿一手打造，更是融合了图书、服装、咖啡、美学生活等多种业态的<strong>复合式文化空间</strong>。店约2400㎡，图书区域面积占到1500㎡，涵盖<strong>14万册图书</strong>，品种多达4万多种。人文、文学、艺术、生活等各类型的优质图书，国内外港台书籍都能在此找到。不仅在入口处用收集来的旧书和花草叠放营造出了山城陡峭、绿树成荫的感觉，整体设计也很有山城味道。<br>到达方式：轻轨3号线至<strong>观音桥站</strong>；或是公交至<strong>建新北路站</strong>。<br><br><h2><b>“最”市井：</b></h2><ul><li><b>十八梯</b></li></ul><img src="http://pic2.zhimg.com/7a03619fbed7883175b01b0d5dab20a1_b.jpg" data-rawwidth="980" data-rawheight="652" class="origin_image zh-lightbox-thumb" width="980" data-original="http://pic2.zhimg.com/7a03619fbed7883175b01b0d5dab20a1_r.jpg"><img src="http://pic3.zhimg.com/81d77b9e1f3c5368c5b63a56ef44defa_b.jpg" data-rawwidth="980" data-rawheight="652" class="origin_image zh-lightbox-thumb" width="980" data-original="http://pic3.zhimg.com/81d77b9e1f3c5368c5b63a56ef44defa_r.jpg">十八梯是<b>典型的重庆式老街</b>，破乱中又承载了很多岁月的记忆，很佩服重庆有勇气愿意保持十八梯本来的样子，不去迎合城市的发展，任凭新城如何发展，十八梯依然我行我素。斑驳的理发店，热闹的小茶馆，孤寂的小商人。到处都是的拆迁现场，告知我们这是一场昨日的告别演出，看不到周围眼神的喜与悲，感觉生活继续，更多的是重庆人身上的恬淡。<br>到达方式：坐<b>地铁2号线</b>到<b>较场口站</b>下车，再步行前往，从石板坡往较场口的那条中兴路上坡的右边就是。<br><br>Tips：多位知友提示十八梯在拆迁中，但是还没有全部拆完，想要去感受一下的要抓紧啦~<br><br><ul><li><b>下浩正街</b><br></li></ul><img src="http://pic1.zhimg.com/bf9667b8b5940cf187b9de42c8934d9c_b.jpg" data-rawwidth="628" data-rawheight="418" class="origin_image zh-lightbox-thumb" width="628" data-original="http://pic1.zhimg.com/bf9667b8b5940cf187b9de42c8934d9c_r.jpg"><img src="http://pic4.zhimg.com/c21bfeb491fe51ff3d3bd0773be9c8fb_b.jpg" data-rawwidth="632" data-rawheight="418" class="origin_image zh-lightbox-thumb" width="632" data-original="http://pic4.zhimg.com/c21bfeb491fe51ff3d3bd0773be9c8fb_r.jpg">走在下浩街头，<b>典型的重庆老街</b>风貌在这里还略有些残存的片断。下浩正街包括米市街地段、门朝街地段、董家桥地段、葡萄院地段4个街坊。这一地区在清乾隆时期就已经形成街市。这条街连接长江，龙门浩老码头是重庆解放前的一个客货两用码头，从码头去上新街，下浩正街和董家桥是必经之路。就是这么一条老街，在繁华落寞淘尽过后，那浓浓的市井味道，反而显得更加从容而真实。<br><br>到达方式：重庆市南岸区<br><br><h2><b>“最”经典：</b></h2><ul><li><b>洪崖洞</b></li></ul><img src="http://pic3.zhimg.com/7bee2d5e444e9dfb7771296b6d37deb6_b.jpg" data-rawwidth="1824" data-rawheight="1225" class="origin_image zh-lightbox-thumb" width="1824" data-original="http://pic3.zhimg.com/7bee2d5e444e9dfb7771296b6d37deb6_r.jpg"><img src="http://pic4.zhimg.com/2c50737558e207ce43b4e46a4c522917_b.jpg" data-rawwidth="1024" data-rawheight="652" class="origin_image zh-lightbox-thumb" width="1024" data-original="http://pic4.zhimg.com/2c50737558e207ce43b4e46a4c522917_r.jpg">如果你看过动漫《<b>千与千寻</b>》你一定会这路所惊呆的，晚上来到这里真的仿佛置身在电影里一样，非常震撼。洪崖洞以最具巴渝传统建筑特色的“<b>吊脚楼</b>”风貌为主体，依山就势，沿崖而建，让解放碑直达江滨，是游吊脚群楼、观洪崖滴翠、逛山城老街、赏巴渝文化、看两江汇流、品天下美食的好地方。<br><br>到达方式：从<b>解放碑</b>步行可达；或出了<b>罗汉寺</b>往西走一公里即到；或乘公交车直达；或乘<b>2号线</b>在<b>临江门</b>站步行前往<br><br><ul><li><b>磁器口</b><br></li></ul><img src="http://pic2.zhimg.com/2e78279b9a4e160e5b87abb15329ee0d_b.jpg" data-rawwidth="960" data-rawheight="640" class="origin_image zh-lightbox-thumb" width="960" data-original="http://pic2.zhimg.com/2e78279b9a4e160e5b87abb15329ee0d_r.jpg"><img src="http://pic4.zhimg.com/f933554dea584b90c61253ebc62de2d7_b.jpg" data-rawwidth="806" data-rawheight="536" class="origin_image zh-lightbox-thumb" width="806" data-original="http://pic4.zhimg.com/f933554dea584b90c61253ebc62de2d7_r.jpg">如果说北京有王府井，武汉有户部巷，南京有夫子庙，西安有回民一条街，那么重庆这个城市的<b>特色古街</b>就是瓷器口了。来磁器口古镇，这个当年热闹的水陆码头，踩踩青石板路，品尝当地的美食小吃，找个茶馆坐坐，感受下老重庆的风土人情是很好的选择。<br><br>Tips：磁器口的主街人满为患，商业化严重，更建议去<b>侧街</b>，也是咖啡馆一条街，客量少，店面装饰都很有文艺味儿，是来磁器口的正确打开方式。（在此安利一家咖啡馆——懒鱼时光馆，上图即是该咖啡馆，是一家有故事的咖啡馆）<br><br>到达方式：乘地铁<b>1号线</b>在<b>磁器口</b>站下车可达（磁器口的大门有两个，下了轻轨走过的第一个大门只是景区的一个区域入口，真正的入口还要往前走500米左右）；公交至<b>正街口</b>站。<br><br><h2><b>“最”地道：</b></h2><ul><li><b>交通茶馆</b></li></ul><img src="http://pic4.zhimg.com/b4cd5ff22eaf8701c27e66b0e146a91f_b.jpg" data-rawwidth="690" data-rawheight="459" class="origin_image zh-lightbox-thumb" width="690" data-original="http://pic4.zhimg.com/b4cd5ff22eaf8701c27e66b0e146a91f_r.jpg"><img src="http://pic3.zhimg.com/ee5c35770c0ce0e0302903ad14bae14e_b.jpg" data-rawwidth="690" data-rawheight="459" class="origin_image zh-lightbox-thumb" width="690" data-original="http://pic3.zhimg.com/ee5c35770c0ce0e0302903ad14bae14e_r.jpg">这个茶馆是《<b>疯狂的石头</b>》中，郭涛召集棒棒们开会的地方。体验最地道的<b>重庆人生活</b>的好去处，点一盏茶，打打小牌，非常惬意。茶馆非常老旧，木头桌椅已经摸花，墙面已经斑驳发黑，看样子有个几十年的历史了。是个原汁原味的老茶馆，没有矫揉造作的仿古，也没有不伦不类的混搭，充满着浓厚的生活气息，贵在这份地道上。<br><br>到达方式：在川美附近，可以一并游览体验，公交在<b>黄角坪正街</b>车站下车。<br><br><ul><li><b>山城步道</b><br></li></ul><img src="http://pic2.zhimg.com/553c022696129917d341a76aa0afe849_b.jpg" data-rawwidth="4304" data-rawheight="2760" class="origin_image zh-lightbox-thumb" width="4304" data-original="http://pic2.zhimg.com/553c022696129917d341a76aa0afe849_r.jpg"><img src="http://pic4.zhimg.com/43d9d13701af8e895909cc019cbda373_b.jpg" data-rawwidth="996" data-rawheight="624" class="origin_image zh-lightbox-thumb" width="996" data-original="http://pic4.zhimg.com/43d9d13701af8e895909cc019cbda373_r.jpg">靠山而修葺的一条步道，很多当地人也常去的一个地方，可以看到长江大桥、前面就是长江，交错的立交桥，反映出了重庆立体3D的地理特征。这条步道地处渝中半岛南向坡面，由北向南，依次经过市中山医院（原国民党政府立法、司法院）、抗建堂、菩提金刚塔、法国仁爱堂旧址、悬空栈道等，全长1748米，紧凑地串联了一系列<b>传统街区</b>和<b>历史文化遗迹</b>。小隐于野，大隐于市，避开纷纷扰扰的人群，静心<b>徒步观景</b>，实属不错的小众线路。<br><br>到达方式：坐公交车或者坐地铁<b>一号线</b>到<b>七星岗</b>站一号出口，找到通远门老城墙（很明显）。公交车站旁边就是，地铁站则要往前走。<br><br><br><h2><b>“最”特别：</b></h2><ul><li><b>长江索道</b><br></li></ul><img src="http://pic3.zhimg.com/14247d8538eee9f065fbd54588db9bc6_b.jpg" data-rawwidth="1136" data-rawheight="756" class="origin_image zh-lightbox-thumb" width="1136" data-original="http://pic3.zhimg.com/14247d8538eee9f065fbd54588db9bc6_r.jpg"><img src="http://pic3.zhimg.com/5a110dd879fb27da10d2070753424856_b.jpg" data-rawwidth="1680" data-rawheight="1118" class="origin_image zh-lightbox-thumb" width="1680" data-original="http://pic3.zhimg.com/5a110dd879fb27da10d2070753424856_r.jpg">长江索道是我国自行设计制造的万里长江上第二条大型跨江客运索道，全长1166米，时速6M/秒，运行时间4分钟，被誉为万里长江第一条空中走廊和“山城空中公共汽车”，是重庆都市旅游唯一的<b>空中交通载体</b>。乘坐的轿厢四面玻璃全透明，可以清楚到看到<b>江两岸的景色</b>。到达对岸后不用着急回来可以在那边拍拍照，然后再返回来。白天和晚上看到的景致完全不一样。白天可以看清楚两岸的景致，晚上夜景很美，前提是天气要好。<br><br>到达方式：索道有两个站，<b>新华路索道</b>站和<b>上新街索道</b>站。一般游客都住在新华路这边，坐地铁<b>1、6号线</b>到<b>小什字</b>站下车，5A或5B出口都是新华路索道站。<br><br><ul><li><b>皇冠大扶梯</b><br></li></ul><img src="http://pic2.zhimg.com/51a38bb1bebb47a14809141e2abd0a91_b.jpg" data-rawwidth="665" data-rawheight="442" class="origin_image zh-lightbox-thumb" width="665" data-original="http://pic2.zhimg.com/51a38bb1bebb47a14809141e2abd0a91_r.jpg"><img src="http://pic3.zhimg.com/8c9baca260a023fa8a14e8572e21bf92_b.jpg" data-rawwidth="900" data-rawheight="638" class="origin_image zh-lightbox-thumb" width="900" data-original="http://pic3.zhimg.com/8c9baca260a023fa8a14e8572e21bf92_r.jpg">来重庆最主要的就是感受山城特有的地形地貌和体验山城特色的交通工具，皇冠大扶梯便是代表作之一。皇冠大扶梯长度是<b>亚洲第二长</b>，站在上面的感觉和普通商场扶梯完全不同，30度的坡道带来的视觉冲击比较强烈，也有点刺激。现在很多景区也有爬山扶梯，但基本上都有很多段，皇冠扶梯就只有超长的一段，票价单面2元，别惊讶，把它想成公交就不奇怪了。到达方式：地铁<b>1号线</b>、轻轨<b>3号线两路口</b>站出来就是，先下去再上来，两次会有不一样的感觉。<br><br><h2><b>“最”馋嘴：</b></h2><ul><li><b>重庆火锅</b><br></li></ul><img src="http://pic1.zhimg.com/48f8f9d248c8432f81aba584456ea9e4_b.jpg" data-rawwidth="2000" data-rawheight="1328" class="origin_image zh-lightbox-thumb" width="2000" data-original="http://pic1.zhimg.com/48f8f9d248c8432f81aba584456ea9e4_r.jpg"><img src="http://pic1.zhimg.com/1a79a0eb3ba688b07be28d8477423e50_b.jpg" data-rawwidth="960" data-rawheight="640" class="origin_image zh-lightbox-thumb" width="960" data-original="http://pic1.zhimg.com/1a79a0eb3ba688b07be28d8477423e50_r.jpg">去重庆如果没吃重庆火锅，可以说是没有来过这个山城。重庆大街小巷内遍布了火锅店，无论春夏秋冬，火锅店内总是座无虚席。重庆火锅，又称为<b>毛肚火锅</b>或<b>麻辣火锅</b>，是中国的传统饮食方式，以调汤考究，麻辣鲜香见长，具有原料多样，荤素皆可，适应广泛，风格独特。推荐店铺：渝味晓宇火锅（上过舌尖上的中国）、朱氏胖子烂火锅（老牌子）、齐齐鳝鱼火锅（鳝鱼必点）、重庆刘一手火锅（传统火锅）、赵二火锅（《Lonely Planet》和《悦食》杂志推荐）。<br><ul><li><b>重庆酸辣粉</b><br></li></ul><img src="http://pic2.zhimg.com/5882c6c1562fc00dfc5684dca1677365_b.jpg" data-rawwidth="672" data-rawheight="461" class="origin_image zh-lightbox-thumb" width="672" data-original="http://pic2.zhimg.com/5882c6c1562fc00dfc5684dca1677365_r.jpg"><img src="http://pic1.zhimg.com/d292d014d2a016b491c84b10301ffc7c_b.jpg" data-rawwidth="1024" data-rawheight="712" class="origin_image zh-lightbox-thumb" width="1024" data-original="http://pic1.zhimg.com/d292d014d2a016b491c84b10301ffc7c_r.jpg">酸辣粉以它的酸辣味而得名，是重庆民间广为流传的<b>传统名小吃</b>。主要采用红薯粉加工而成，因价廉物美，长期以来一直受人喜爱。重庆人吃酸辣粉可从来不在乎什么形象，经常可以看到当地人在街上手端一碗酸辣粉直接吃起来。由于重庆的酸辣粉口味独特、酸辣开胃，长期以来一直深受重庆人的喜爱，其特点是“<b>麻、辣、鲜、香、酸且油而不腻</b>”。<br><br>推荐店铺：好又来酸辣粉（口碑店家）、手工酸辣粉（视觉和味觉两不误）、张老汉手工酸辣粉（磁器口必吃之一）。<br><br><br><ul><li><b>重庆小面</b></li></ul><img src="http://pic1.zhimg.com/cbd8911eb2d87f101f4600e62c80b114_b.jpg" data-rawwidth="988" data-rawheight="666" class="origin_image zh-lightbox-thumb" width="988" data-original="http://pic1.zhimg.com/cbd8911eb2d87f101f4600e62c80b114_r.jpg"><img src="http://pic2.zhimg.com/ed00320fb95018bc4d15d985842fbfc5_b.jpg" data-rawwidth="992" data-rawheight="653" class="origin_image zh-lightbox-thumb" width="992" data-original="http://pic2.zhimg.com/ed00320fb95018bc4d15d985842fbfc5_r.jpg">到了重庆除了麻辣火锅，还有各色面食也非常出名。宜宾燃面，重庆小面，荞面……各式各样，眼花缭乱，放心大胆的吃就对了。重庆小面是一款发源于山城重庆市的一种汉族传统小吃，属于渝菜。小面属于<b>汤面类型</b>，<b>麻辣味型</b>。狭义的小面是指麻辣素面。重庆人对重庆小面的热爱不亚于火锅，亲密度更是有过之而无不及。属于非常亲民的<b>早点小吃</b>。<br>推荐店铺：重庆小面店分布很广，几乎每条街巷甚至每栋楼附近都随处可见。50强的小面可以去搜索做下攻略，但是最好的推荐其实是<b>随意去一家小面店</b>，感受小面在重庆的深厚底蕴。<br><br><h2><b>“最”购物：</b></h2><ul><li><b>解放碑</b><br></li></ul><img src="http://pic1.zhimg.com/59fcce35e0f3a7b67843cf7a6f4c8534_b.jpg" data-rawwidth="920" data-rawheight="645" class="origin_image zh-lightbox-thumb" width="920" data-original="http://pic1.zhimg.com/59fcce35e0f3a7b67843cf7a6f4c8534_r.jpg"><img src="http://pic4.zhimg.com/b2a2b91b475ec4248c22a85776bc4aab_b.jpg" data-rawwidth="990" data-rawheight="653" class="origin_image zh-lightbox-thumb" width="990" data-original="http://pic4.zhimg.com/b2a2b91b475ec4248c22a85776bc4aab_r.jpg">解放碑是重庆著名且重要的地标，是购物的天堂。这里有高档的<b>购物大厦</b>，也有繁华的<b>购物商业街</b>，还有很多美食小吃也聚集在这里。花上一天时间在这里购购物，逛逛街，累了找个小店休息，饿了寻觅那排着长长队伍的小吃。晚上这里更是繁华，坐看来来往往的人，还可以看到不少重庆的美女，霎是养眼！到达方式：乘<b>1号线</b>在<b>较场口</b>站下车，从较场口9号口出直走两个路口即到；或乘<b>2号线</b>在<b>临江门</b>站下。<br><br><ul><li><b>观音桥步行街</b><br></li></ul><img src="http://pic4.zhimg.com/78f1387c1038922fc4f640a8dae727d7_b.jpg" data-rawwidth="924" data-rawheight="590" class="origin_image zh-lightbox-thumb" width="924" data-original="http://pic4.zhimg.com/78f1387c1038922fc4f640a8dae727d7_r.jpg"><img src="http://pic3.zhimg.com/c185543155e009a6cd7286d1fb266b9a_b.jpg" data-rawwidth="1014" data-rawheight="649" class="origin_image zh-lightbox-thumb" width="1014" data-original="http://pic3.zhimg.com/c185543155e009a6cd7286d1fb266b9a_r.jpg">重庆人在厌倦了解放碑的喧嚣之后，更加喜欢观音桥的有条有理，闹中有静，观音桥是重庆人留给自己的一方乐土。观音桥步行街是个集公园、广场、步行街三大功能于一体，商业与景观有机的<b>大型生态商圈</b>。街上有茂业百货、远东百货、上海百联、北京华联、新世界、新世纪、重百等百货商场，有永辉、易初莲花、家乐福等超市，有苏宁、国美等，这时里也是打望的好地方。<br><br>到达方式：地铁3号线至<b>观音桥</b>站。<br><br><h2><b>“最”风景：</b></h2><ul><li><b>南山一棵树观景台</b><br></li></ul><img src="http://pic3.zhimg.com/66ef180f1b3f32d1294a732c7dd4035a_b.jpg" data-rawwidth="1513" data-rawheight="997" class="origin_image zh-lightbox-thumb" width="1513" data-original="http://pic3.zhimg.com/66ef180f1b3f32d1294a732c7dd4035a_r.jpg"><img src="http://pic2.zhimg.com/e4898cb3ab6e6b5c660dde2189435ecd_b.jpg" data-rawwidth="930" data-rawheight="596" class="origin_image zh-lightbox-thumb" width="930" data-original="http://pic2.zhimg.com/e4898cb3ab6e6b5c660dde2189435ecd_r.jpg">这是一个<b>看重庆夜景</b>最美的地方。随便一个人问到重庆的夜景在哪里看最好，都会统一的回答朝天门或者一棵树。这是角度问题，朝天门看江景，南山一棵树是俯瞰全重庆最美的一个角度。站在观景台上，远远望去，重庆渝中区万家灯火；环抱的两江，流光溢彩；飞跨的长桥，轮廓清晰；层见叠出，错落有致，色彩缤纷的整座城市，在夜空的衬托下美轮美奂，光彩夺目。<br><br>到达方式：从解放碑方向出发的话，建议坐<b>长江索道</b>过去到南岸那一头，下索道出马路往右走不远，顺着山上方向走一段路可以看到上<b>新街公交</b>站再坐公车到达山上<b>四中站</b>后，又往回沿马路走一段路，约10分钟就到；最建议的还是索道抵达后<b>打车</b>上山。<br><br><ul><li><b>朝天门</b><br></li></ul><img src="http://pic3.zhimg.com/532c512a81f6491f60c3764d632297ba_b.jpg" data-rawwidth="838" data-rawheight="523" class="origin_image zh-lightbox-thumb" width="838" data-original="http://pic3.zhimg.com/532c512a81f6491f60c3764d632297ba_r.jpg"><img src="http://pic2.zhimg.com/64be71a740f2aacf93900e23817890fd_b.jpg" data-rawwidth="1044" data-rawheight="652" class="origin_image zh-lightbox-thumb" width="1044" data-original="http://pic2.zhimg.com/64be71a740f2aacf93900e23817890fd_r.jpg">这里<b>长江嘉陵江交融并流</b>，长江水流浑厚，嘉陵江水流清澈，它们汇集后一起奔腾流向长江主流河道。江景非常壮观非常有气势。尤其是天气晴朗的时候。这里也是重庆最繁忙的<b>码头</b>之一，这个码头已经不仅仅是一座码头了，赋予很多意义。观光游船停泊在江水中央，依山而建的楼宇，直挺挺地宣示着人类改造自然的能力。<br><br>到达方式：坐地铁<b>1号线</b>到<b>小什字</b>下车，8出口；因施工通行不便，大部分地方都围上围板，要沿着长江边的一条小路（临时的）一直走，最后绕到朝天门广场，路途比较曲折。<br><br>—————————————————<br><h2>然后是来自知乎网友们的良心建议~</h2><br><a data-hash="218f6f179705c486f03b372ec33f487b" href="http://www.zhihu.com/people/218f6f179705c486f03b372ec33f487b" class="member_mention" data-editable="true" data-title="@言西早呢" data-hovercard="p$b$218f6f179705c486f03b372ec33f487b">@言西早呢</a> 提到：还有洋人街啊！各个公园或者花园的，比如南山植物园、中央公园、洪恩寺公园…对了，还有科技馆。<br><br><a data-hash="5bedf3f9ddd8a1bc9e9a1a312860f4a6" href="http://www.zhihu.com/people/5bedf3f9ddd8a1bc9e9a1a312860f4a6" class="member_mention" data-editable="true" data-title="@阡贝同学" data-hovercard="p$b$5bedf3f9ddd8a1bc9e9a1a312860f4a6">@阡贝同学</a> 提到：大家比较熟悉的可能都是重庆主城区的一些景点，比如磁器口，解放碑之类的，要不就是被各种耳熟能详的美食吸引。但重庆也是地大物博，市下的各个区县的景点也非常美，比如合川的钓鱼台，江津的四面山，酉阳的桃花源等等。再者，其他遍地可见的食物可是非常好吃的，比如豆花饭、凉糕之类的。火锅要吃最正宗的九宫格老火锅才满足哦。<a data-hash="d740ba899c1ec7024a659eaec88479c9" href="http://www.zhihu.com/people/d740ba899c1ec7024a659eaec88479c9" class="member_mention" data-editable="true" data-title="@漫天" data-hovercard="p$b$d740ba899c1ec7024a659eaec88479c9">@漫天</a> 提到：十分推荐重庆磁器口的陈麻花，几乎我每个吃过的同学都点赞。<br><br><a data-hash="cdede832c90392f59147045d1fcd11f8" href="http://www.zhihu.com/people/cdede832c90392f59147045d1fcd11f8" class="member_mention" data-editable="true" data-title="@chungguo" data-hovercard="p$b$cdede832c90392f59147045d1fcd11f8">@chungguo</a> 提到：看重庆全景的话，南山老君洞在傍晚比一棵树视角好多了。鹅岭公园的两江楼也比只能看到南岸区的一棵树好太多，可以看全重庆。<br><br><a data-hash="be3dc48f3bc61bcd5a7c3367979d6f2e" href="http://www.zhihu.com/people/be3dc48f3bc61bcd5a7c3367979d6f2e" class="member_mention" data-editable="true" data-title="@白日梦" data-hovercard="p$b$be3dc48f3bc61bcd5a7c3367979d6f2e">@白日梦</a> 提到：重庆莱得快酸辣粉啊，打的广告语：行家一尝知乾坤。<br><br><a data-hash="b4d9b28e9ab01a0d1149431f99c57277" href="http://www.zhihu.com/people/b4d9b28e9ab01a0d1149431f99c57277" class="member_mention" data-editable="true" data-title="@Hiroyuki" data-hovercard="p$b$b4d9b28e9ab01a0d1149431f99c57277">@Hiroyuki</a> 提到：来重庆强烈建议体验轨道交通，一号线石井坡的江景，赖家桥的歌乐山，春天的时候大学城段一路都有油菜花。二号线较场口到佛图关一路江景，轻轨穿楼过和超大弯度过山车就是那截。三号线铜元局到观音桥一次性跨2条江，龙头寺到汽博段上天入地，金渝站的大转弯不熟二号线。六号线不是很熟悉欢迎大家补充。<br><br><a data-hash="1dd35a7a800244cc15008638a14a711b" href="http://www.zhihu.com/people/1dd35a7a800244cc15008638a14a711b" class="member_mention" data-editable="true" data-title="@高丽丽" data-hovercard="p$b$1dd35a7a800244cc15008638a14a711b">@高丽丽</a> 提到：咱们重庆还有纸包鱼呀！！！特别是巫山纸包鱼！还有沙坪坝正宗的李记串串，那也是爆火<br><br><a data-hash="c78c677d9efbfb082edc5153bf201b70" href="http://www.zhihu.com/people/c78c677d9efbfb082edc5153bf201b70" class="member_mention" data-editable="true" data-title="@相迹" data-hovercard="p$b$c78c677d9efbfb082edc5153bf201b70">@相迹</a> 提到：还有重庆大学虎溪校区啊，超级漂亮，差不多是一个景点了，带同学逛之后都说比公园还好看(ง •̀_•́)ง<br><br><a data-hash="e59c2e3e662d36d3896c74c8056de267" href="http://www.zhihu.com/people/e59c2e3e662d36d3896c74c8056de267" class="member_mention" data-editable="true" data-title="@李旨垚" data-hovercard="p$b$e59c2e3e662d36d3896c74c8056de267">@李旨垚</a> 提到：火锅自我感觉要吃老火锅比较正宗，记忆老灶王少龙什么的还可以，秦妈刘一手德庄什么的只是比较出名。小吃有磁器口的毛血旺，歌乐山的辣子鸡，解放碑有一条小吃街。玩的还有朝天门坐船，人民大礼堂看着很大气。<br><br><a data-hash="350c8e1802c9cdea0c125f9832f5ecee" href="http://www.zhihu.com/people/350c8e1802c9cdea0c125f9832f5ecee" class="member_mention" data-editable="true" data-title="@Deeki曦" data-hovercard="p$b$350c8e1802c9cdea0c125f9832f5ecee">@Deeki曦</a> 提到：还有歌乐山的辣子鸡啊，超带感超好吃啊，那个三峡广场的老农民酸辣粉我真是强推吧！不过不能吃辣的同学要做好心理准备，那里的凉面凉皮也好吃，再配几串旁边卖的鱿鱼！还有三峡博物馆，三峡博物馆对面就是人民大礼堂，以前大礼堂前还有喂鸽子的，不过现在好像没了。不远的地方就是中山四路！超文字超有民国风的一条路！从地铁口出去感觉像穿越了一样！很多遗迹也在这里！暂时就想到这么多要补充的了(≧ω≦)<br><br><a data-hash="79943ee1ed2000dc7f57290b088e9186" href="http://www.zhihu.com/people/79943ee1ed2000dc7f57290b088e9186" class="member_mention" data-editable="true" data-title="@沈半夏" data-hovercard="p$b$79943ee1ed2000dc7f57290b088e9186">@沈半夏</a> 提到：最出名最有特色的小面啊！十八梯的牛肉面，老太婆摊摊面，老虎面，猫儿面和盅盅面之类的都不错啊！！<br><br><a data-hash="e449c7d5fa62b5053513ffd70d4def7f" href="http://www.zhihu.com/people/e449c7d5fa62b5053513ffd70d4def7f" class="member_mention" data-editable="true" data-title="@黄敏" data-hovercard="p$b$e449c7d5fa62b5053513ffd70d4def7f">@黄敏</a> 提到：重庆洋人街和海昌加勒比海水世界，都挺好玩的<br><br>@西湖醋鱼 提到：其实我觉得重庆最好吃的酸辣粉是沙坪坝三峡广场的雷家老农民，好久了都吃不厌<br><br><a data-hash="fb4b545b06de3cb11c19ec0eb5e90f48" href="http://www.zhihu.com/people/fb4b545b06de3cb11c19ec0eb5e90f48" class="member_mention" data-editable="true" data-title="@魏相逢" data-hovercard="p$b$fb4b545b06de3cb11c19ec0eb5e90f48">@魏相逢</a> 提到：可以去罗汉寺看看，就在解放碑商圈中心的一座寺庙，疯狂的石头拍摄场地<br><br><a data-hash="9753e4e0ce219e48d6632d1f71e5bc9d" href="http://www.zhihu.com/people/9753e4e0ce219e48d6632d1f71e5bc9d" class="member_mention" data-editable="true" data-title="@王易" data-hovercard="p$b$9753e4e0ce219e48d6632d1f71e5bc9d">@王易</a> 提到：山城步道有很多条，风景最好的当属第三步道。怎么去呢？坐公交车或者坐地铁一号线到七星岗站一号出口，找到通远门老城墙（很明显）。公交车站旁边就是，地铁站则要往前走。通远门老城墙是市区保存较好的老城墙，比较小，可以上去看看，花不了几分钟，然后走到城墙的后面，也就是金汤街，顺着金汤街过领事巷、山城巷，最后走到山城步道的下出口，然后可以去坐较场口站的地铁。这是第一条线路，能看到很多老建筑，但看不到栈道，要看栈道的话是在山城巷靠近出口的时候有一条沿山的栈道，一直通往枇杷山后街。如果只想看栈道的话，就从七星岗地铁站2号出口出来，走枇杷山后街，然后走石板坡正街，，，看见监狱管理所右拐，，顺着一堵围墙就会看到栈道了，（是条小道别害怕）。然后顺着栈道就会进入山城巷了。<br>在我看来，山城步道不仅仅是一条游览的线路，更多的也是给当地人提供小歇的去处。<br><br><a data-hash="46da36ae4b677fc886a999ef4e50a98c" href="http://www.zhihu.com/people/46da36ae4b677fc886a999ef4e50a98c" class="member_mention" data-editable="true" data-title="@唐小糖" data-hovercard="p$b$46da36ae4b677fc886a999ef4e50a98c">@唐小糖</a> 提到：重庆土著表示酸辣粉最出名的是沙坪坝三峡广场的那家老农民酸辣粉啊。还上过天天向上的<br><br><a data-hash="1e9cf527306e6db359e683b4dfd2077a" href="http://www.zhihu.com/people/1e9cf527306e6db359e683b4dfd2077a" class="member_mention" data-editable="true" data-title="@愿为森林" data-hovercard="p$b$1e9cf527306e6db359e683b4dfd2077a">@愿为森林</a> 提到：说到一棵树为何不推荐大金鹰呢 那才是南山最高呀<br>———————————————————<b>知乎专栏：<a href="https://zhuanlan.zhihu.com/bubu-cityguide" class="internal">步步城市指南</a></b>，探索城市吃喝玩乐新姿势。欢迎大家投稿到专栏<a href="https://www.zhihu.com/people/bubutravel" class="internal">步步指南</a>，一起当城市旅行家。<br><br><br><b>微信公众号：<a href="http://link.zhihu.com/?target=http%3A//www.bubu.so/wx" class=" wrap external" target="_blank" rel="nofollow noreferrer">步步指南<i class="icon-external"></i></a></b><br>回复城市关键词（如“厦门”）即可获取更多目的地旅行指南。编辑于 2017-01-10
    # """
    # tree = fromstring(content)
    # content = _get_text(tree)
    # print(content)
