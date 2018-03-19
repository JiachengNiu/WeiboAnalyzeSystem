# -*- coding: utf-8 -*-
import web
import model
#from echarts import Echart, Legend, Bar, Axis

### Url mappings

urls = (
    '/', 'Index',
    '/en', 'Index_en' ,
    #'/(.*[^\x00-\xff]+.*)', 'Analyze',
    '/((?!hotspot|weibo|timeline|data|.*/en).*)', 'Analyze',
    '/((?!hotspot|weibo|timeline|data).*)', 'Analyze_en',
    '/timeline', 'Timeline',
    '/timeline/en', 'Timeline_en',
    '/weibo' , 'Weibo',
    '/weibo/en' , 'Weibo_en',
    '/data' , 'Data' ,
    '/data/en' , 'Data_en' ,
    '/hotspot' , 'Hotspot' , 
    '/hotspot/en' , 'Hotspot_en'
)


### Templates
render = web.template.render('templates', base='base')


class Hotspot:
    def GET(self):
        """ Show page """
        items = model.get_items()
        x = {'keywords':None, 't_rank':None, 't_type':None, 't_keyword':None, 't_date':None, 't_freq':None}
        return render.hotspot(items, x)

    def POST(self):
        x = web.input(keywords='', t_rank='', t_keyword='', t_date='', t_freq='')
        items, x = model.search(x)
        return render.hotspot(items, x)
        raise web.seeother('/')

class Hotspot_en:
    def GET(self):
        """ Show page """
        items = model.get_items()
        x = {'keywords':None, 't_rank':None, 't_type':None, 't_keyword':None, 't_date':None, 't_freq':None}
        return render.hotspot_en(items, x)

    def POST(self):
        x = web.input(keywords='', t_rank='', t_keyword='', t_date='', t_freq='')
        items, x = model.search(x)
        return render.hotspot_en(items, x)
        raise web.seeother('/')

        

class Analyze:
    def GET(self, keyword):
        dates, freqs, items, results, words, types, values, type, imgsrc = model.get_item(keyword)
        '''
        chart = Echart(keyword, 'hot analysis')
        chart.use(Bar('hot', freqs))
        chart.use(Legend(['hot']))
        chart.use(Axis('category', 'bottom', data=dates))
        print str(chart).strip()
        chart.plot()
        '''
        return render.analyze(keyword, freqs, dates, items, results, words, types, values, type, imgsrc)

class Analyze_en:
    def GET(self, keyword):
        keyword = keyword[:-3]
        print keyword
        dates, freqs, items, results, words, types, values, type, imgsrc = model.get_item(keyword)
        '''
        chart = Echart(keyword, 'hot analysis')
        chart.use(Bar('hot', freqs))
        chart.use(Legend(['hot']))
        chart.use(Axis('category', 'bottom', data=dates))
        print str(chart).strip()
        chart.plot()
        '''
        return render.analyze_en(keyword, freqs, dates, items, results, words, types, values, type, imgsrc)


class Timeline:
    def GET(self):
        items = model.get_timeline()
        return render.timeline(items)

class Timeline_en:
    def GET(self):
        items = model.get_timeline()
        return render.timeline_en(items)


class Weibo:
    def GET(self):
        items = model.get_weibo()
        return render.weibo(items)

class Weibo_en:
    def GET(self):
        items = model.get_weibo()
        return render.weibo_en(items)
    

class Data:
    def GET(self):
        return render.data([], [], [], '', None)
    
    def POST(self):
        x = web.input(text='')
        if x['text'] == None or x['text'] == '':
            return render.data({}, [], [], '', None)
        results, wordfreqs, types, values, type = model.get_content_tags(x['text'])
        model.generate_cloud('data', wordfreqs)
        words = sorted(wordfreqs.iteritems(), key=lambda a:a[1], reverse=True)
        if len(words) > 20:
            words = words[0:20]
        print results, words, types, values, type
        return render.data(words, types, values, type, x['text'])

class Data_en:
    def GET(self):
        return render.data_en([], [], [], '', None)
    
    def POST(self):
        x = web.input(text='')
        if x['text'] == None or x['text'] == '':
            return render.data({}, [], [], '', None)
        results, wordfreqs, types, values, type = model.get_content_tags(x['text'])
        model.generate_cloud('data', wordfreqs)
        words = sorted(wordfreqs.iteritems(), key=lambda a:a[1], reverse=True)
        if len(words) > 20:
            words = words[0:20]
        print results, words, types, values, type
        return render.data_en(words, types, values, type, x['text'])


class Index:
    def GET(self):
        return render.index()

class Index_en:
    def GET(self):
        return render.index_en()
        



app = web.application(urls, globals())

if __name__ == '__main__':
    app.run()
