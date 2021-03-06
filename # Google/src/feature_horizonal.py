# -*- coding: utf-8 -*-
"""
Created on Mon Oct 15 00:27:28 2018

@author: Franc
"""
import pandas as pd
import numpy as np
from data_cleaner import googleCleaner

class googleHorizonal(googleCleaner):
    
    def __init__(self):
        super(googleCleaner, self).__init__()
        self.feature_id = ['totals_transactionRevenue',
                'fullVisitorId','sessionId','visitId','date',
                'visitStartTime','visitDate','visitTime']
        self.feature_ratio_dict = {}
        
    def featureHorizonal(self, df, train_mode=True):
        df = df.copy()
        df.replace({'not available in demo dataset':'not available'},
                   inplace=True)
        """ device_browser """
        if train_mode:
            feature_list = [
                    'device_browser','device_operatingSystem',
                    'geoNetwork_networkDomain']
            self.feature_ratio_generate(df, feature_list)
        df = df.merge(self.feature_ratio_dict['device_browser'],
                      on=['device_browser'], how='left')
        df['device_browser'] = df['device_browser'].map(
                lambda x: self.browser_transform(str(x).lower())).astype('str')
                
        """ device_operatingSystem """
        df = df.merge(self.feature_ratio_dict['device_operatingSystem'], 
                      on=['device_operatingSystem'], how='left')
        
        """ totals_hits & totals_pageviews """
        df['totals_hits_interval'] = np.where(
                df['totals_hits']==1, 0,
                np.where(df['totals_hits']<4,1,
                         np.where(df['totals_hits']<7,2,
                                  np.where(df['totals_hits']<11,3,\
                np.where(df['totals_hits']<22,4,
                         np.where(df['totals_hits']<33,5,
                                  np.where(df['totals_hits']<49,6,7)))))))
        df['totals_pageviews_interval'] = np.where(
                df['totals_pageviews']==1, 0,
                np.where(df['totals_pageviews']<4,1,
                         np.where(df['totals_pageviews']<7,2,
                                  np.where(df['totals_pageviews']<10,3,\
                np.where(df['totals_pageviews']<16,4,
                         np.where(df['totals_pageviews']<24,5,
                                  np.where(df['totals_pageviews']<49,6,7)))))))
        df['totals_hits_pageviews_ratio'] = \
            (df['totals_hits'] + 1)/(df['totals_pageviews'] + 1)
        df['totals_high_visit'] = \
            np.logical_or(df['totals_hits']>4,
                          df['totals_pageviews']>4).astype(int)
            
        """ geoNetwork_networkDomain """
        df = df.merge(self.feature_ratio_dict['geoNetwork_networkDomain'], 
                      on=['geoNetwork_networkDomain'], how='left')
        
        """ trafficSource_adContent """
        df['trafficSource_adContent_dominant'] = np.where(
                df['trafficSource_adContent'].notnull(),
                np.where(df['trafficSource_adContent'].isin([
                        'Google Merchandise Collection', 'Google Online Store', 
                        'Full auto ad IMAGE ONLY','Swag with Google Logos',
                        '20% discount','{KeyWord:Google Branded Gear}',
                        '{KeyWord:Want Google Stickers?}']),
                        df['trafficSource_adContent'],'others'), np.nan)
        df['trafficSource_adContent'] = df['trafficSource_adContent'].map(
                lambda x:self.adContent_transform(str(x).lower())).astype('str')
        
        """ trafficSource_keyword """
        df['trafficSource_keyword_dominant'] = np.where(
                df['trafficSource_keyword'].notnull(),
                np.where(df['trafficSource_keyword'].isin([
                        '(not provided)', '6qEhsCssdK0z36ri', 
                        '1hZbAqLCbjwfgOH7', '(Remarketing/Content targeting)',
                        '1X4Me6ZKNV0zg-jV']), df['trafficSource_keyword'],
                    np.where(df['trafficSource_keyword'].isin([
                            'google merchandise store','google store',
                            'Google Merchandise','+Google +Merchandise']),
                            'Google','others')),np.nan)
        
        """ trafficSource_source """        
        df['trafficSource_source'] = df['trafficSource_source'].map(
                lambda x: self.source_transform(str(x).lower())).astype('str')

        """ visitStartTime """
        df['visitDate'] = df['visitStartTime'].dt.date.apply(
                lambda x: x.strftime('%Y%m%d')).astype(int)
        df['visitTime'] = df['visitStartTime'].dt.time.apply(
                lambda x:int(x.strftime('%H%M%S')))
        df['visitMonth'] = df['visitStartTime'].dt.month
        df['visitHour'] = df['visitStartTime'].dt.hour
        df['visitWeekday'] = df['visitStartTime'].dt.dayofweek

        """ visit time """
        df['visitHour_interval'] = np.where(
                (0<df['visitHour'])&(df['visitHour']<9),1,
                np.where((13<df['visitHour'])&(df['visitHour']<21),3,2))
        df['visitWeekday_weekend_bool'] = \
            ((0<df['visitWeekday'])&(df['visitWeekday']<7)).astype('int32')        
        
        """ Weird Feature """
        df['id_incoherence'] = (pd.to_datetime(
                df['visitId'], unit='s') != df['visitStartTime']).astype(int)
        df['visitId_dublicates'] = df['visitId'].map(df['visitId'].value_counts())
        df['session_dublicates'] = df['sessionId'].map(df['sessionId'].value_counts())
        
        feature_to_count = [
                'geoNetwork_networkDomain','trafficSource_referralPath',
                'device_operatingSystem','geoNetwork_country',
                'geoNetwork_city','geoNetwork_metro',
                'geoNetwork_networkDomain','geoNetwork_region',
                'geoNetwork_subContinent','trafficSource_adContent',
                'trafficSource_campaign','trafficSource_keyword',
                'trafficSource_medium','trafficSource_referralPath',
                'trafficSource_source']
        for feature in feature_to_count:
            component = self.feature_count_ratio(df, feature)
            df = df.merge(component, on=[feature], how='left')
        
        self.feature_horizonal = list(set(df.columns)-set(self.feature_id))
        df = df.reindex(columns=self.feature_id+sorted(self.feature_horizonal))
        return df

    def feature_ratio_generate(self, df, feature_list):
        df = df.copy()
        for feature in feature_list:
            component = pd.crosstab(
                    self.validTarget, df[feature], margins=True).T.reset_index()
            component[f'{feature}_ratio'] = np.log(
                    (component[1]+1)/(component[0]+1))
            self.feature_ratio_dict[feature] = component[[
                    feature, f'{feature}_ratio']]
        return self
    
    def feature_count_ratio(self, data, feature):
        component = data[feature].value_counts().sort_values(
                ascending=False).reset_index().rename(
                        columns={'index':feature, feature:f'{feature}_count'})
        return component
    
    def browser_transform(self, x):
        browsers = ['chrome','safari','firefox','internet explorer',
                    'edge','opera','coc coc','maxthon','iron']
        if x in browsers:
            return x.lower()
        elif  ('android' in x) or ('samsung' in x) or ('mini' in x) or (
                'iphone' in x) or ('in-app' in x) or ('playstation' in x):
            return 'mobile browser'
        elif  ('mozilla' in x) or ('chrome' in x) or ('blackberry' in x) or (
                'nokia' in x) or ('browser' in x) or ('amazon' in x):
            return 'mobile browser'
        elif  ('lunascape' in x) or ('netscape' in x) or (
                'blackberry' in x) or ('konqueror' in x) or (
                        'puffin' in x) or ('amazon' in x):
            return 'mobile browser'
        elif '(not set)' in x:
            return x
        else:
            return 'others'
        
    def adContent_transform(self, x):
        if  ('google' in x):
            return 'google'
        elif  ('placement' in x) | ('placememnt' in x):
            return 'placement'
        elif ('(not set)' in x) or ('nan' in x):
            return x
        elif 'ad' in x:
            return 'ad'
        else:
            return 'others'
        
    def source_transform(self, x):
        if  'google' in x:
            return 'google'
        elif  'youtube' in x:
            return 'youtube'
        elif 'nan' in x:
            return x
        elif 'yahoo' in x:
            return 'yahoo'
        elif 'facebook' in x:
            return 'facebook'
        elif 'reddit' in x:
            return 'reddit'
        elif 'bing' in x:
            return 'bing'
        elif 'quora' in x:
            return 'quora'
        elif 'outlook' in x:
            return 'outlook'
        elif 'linkedin' in x:
            return 'linkedin'
        elif 'pinterest' in x:
            return 'pinterest'
        elif 'ask' in x:
            return 'ask'
        elif 'siliconvalley' in x:
            return 'siliconvalley'
        elif 'lunametrics' in x:
            return 'lunametrics'
        elif 'amazon' in x:
            return 'amazon'
        elif 'mysearch' in x:
            return 'mysearch'
        elif 'qiita' in x:
            return 'qiita'
        elif 'messenger' in x:
            return 'messenger'
        elif 'twitter' in x:
            return 'twitter'
        elif 't.co' in x:
            return 't.co'
        elif 'vk.com' in x:
            return 'vk.com'
        elif 'search' in x:
            return 'search'
        elif 'edu' in x:
            return 'edu'
        elif 'mail' in x:
            return 'mail'
        elif 'ad' in x:
            return 'ad'
        elif 'golang' in x:
            return 'golang'
        elif 'direct' in x:
            return 'direct'
        elif 'dealspotr' in x:
            return 'dealspotr'
        elif 'sashihara' in x:
            return 'sashihara'
        elif 'phandroid' in x:
            return 'phandroid'
        elif 'baidu' in x:
            return 'baidu'
        elif 'mdn' in x:
            return 'mdn'
        elif 'duckduckgo' in x:
            return 'duckduckgo'
        elif 'seroundtable' in x:
            return 'seroundtable'
        elif 'metrics' in x:
            return 'metrics'
        elif 'sogou' in x:
            return 'sogou'
        elif 'businessinsider' in x:
            return 'businessinsider'
        elif 'github' in x:
            return 'github'
        elif 'gophergala' in x:
            return 'gophergala'
        elif 'yandex' in x:
            return 'yandex'
        elif 'msn' in x:
            return 'msn'
        elif 'dfa' in x:
            return 'dfa'
        elif '(not set)' in x:
            return '(not set)'
        elif 'feedly' in x:
            return 'feedly'
        elif 'arstechnica' in x:
            return 'arstechnica'
        elif 'squishable' in x:
            return 'squishable'
        elif 'flipboard' in x:
            return 'flipboard'
        elif 't-online.de' in x:
            return 't-online.de'
        elif 'sm.cn' in x:
            return 'sm.cn'
        elif 'wow' in x:
            return 'wow'
        elif 'baidu' in x:
            return 'baidu'
        elif 'partners' in x:
            return 'partners'
        else:
            return 'others'