#!/usr/bin/env python2

from cfscrape import *
from requests import session
from bs4 import BeautifulSoup
import json, os, requests, re,sys

class CTFdCrawl:
    def __init__(self, team, passwd, url):
        self.auth   = dict(name=team, password=passwd)
        self.header = {'User-Agent' : 'curl/7.37.0'}
        self.ses    = session()
        # self.ses.verify = False
        self.entry  = dict()
        self.keys   = 'data'
        self.url    = url
        self.ch_url = self.url + '/api/v1/challenges'
        self.hi_url = self.url + '/api/v1/hints'

        if not self.login():
            raise Exception('Login Failed')
        print '\n[+] Collecting resources'
        self.checkVersion()

    def login(self):
        resp  = self.ses.get(self.url + '/login', headers=self.header)
        soup  = BeautifulSoup(resp.text,'lxml')
        nonce = soup.find('input', {'name':'nonce'}).get('value')

        self.auth['nonce'] = nonce
        self.title = soup.title.string

        resp  = self.ses.post(self.url + '/login', data=self.auth, headers=self.header)
        return 'incorrect' not in resp.text

    def checkVersion(self):
        resp = self.ses.get(self.ch_url, headers=self.header)
        self.version = 'v.1.2.0' if '404' not in resp.text else 'v.1.0'

    def antiCloudflare(self, page):
        scrape = create_scraper()
        tokens = get_tokens('{}/{}'.format(self.URL, page))
        return tokens

    def checkHint(self, id):
        for i in range(10):
            resp = self.ses.get('{}/{}'.format(self.hi_url,i), headers=self.header)
            data = resp.json()
            if not data.keys()[0] == 'message':
                if data['data']['challenge'] == id:
                    return data['data'] if self.version == 'v.1.2.0' else data

    def parseChall(self, id):
        resp = self.ses.get('{}/{}'.format(self.ch_url,id), headers=self.header).json()
        return resp['data'] if self.version == 'v.1.2.0' else resp

    def parseAll(self):
        print '[+] Finding challs'
        if self.version == 'v.1.0':
            self.ch_url = self.url + '/chals'
            self.hi_url = self.url + '/hints'
            self.keys   = 'game'
        # print self.ses.get(self.ch_url).text
        # print self.ses.get(self.ch_url, headers=self.header).json()
        html  = sorted(self.ses.get(self.ch_url, headers=self.header).json()[self.keys])
        ids   = [i['id'] for i in html]

        # for i in html:
        #     ch_name = i['name']
        #     ch_cat  = i['category'] if i['category'] else 'Uncategorized'
        #     try:
        #         ch_hint = self.checkHint(id)['content'] if i['hints'] else ''
        #     except:
        #         ch_hint = ''

        #     if not self.entry.get(ch_cat):
        #         self.entry[ch_cat] = {}
        #         count = 1
        #         print '\n [v]', ch_cat
        #     print '  {}. {}'.format(count, ch_name.encode('utf-8').strip())

        #     entries = {ch_name : {
        #       'ID'          : i['id'],
        #       'Points'      : i['value'],
        #       'Description' : i['description'],
        #       'Files'       : i['files'],
        #       'Hint'        : ch_hint
        #      }
        #     }

        #     self.entry[ch_cat].update(entries)
        #     count += 1


        # print ids
        # print json.dumps(html ,sort_keys=True, indent=4)
        for id in ids:
            data    = self.parseChall(id)
            ch_name = data['name']
            ch_cat  = data['category'] if data['category'] else 'Uncategorized'
            try:
                ch_hint = self.checkHint(id)['content'] if data['hints'] else ''
            except:
                ch_hint = ''

            if not self.entry.get(ch_cat):
                self.entry[ch_cat] = {}
                count = 1
                print '\n [v]', ch_cat
            print '  {}. {}'.format(count, ch_name.encode('utf-8').strip())

            entries = {ch_name : {
              'ID'          : data['id'],
              'Points'      : data['value'],
              'Description' : data['description'],
              'Files'       : data['files'],
              'Hint'        : ch_hint
             }
            }

            self.entry[ch_cat].update(entries)
            count += 1

    def createArchive(self):
        print '\n[+] Downloading assets . . .'
        if not os.path.exists(self.title):
            os.makedirs(self.title)

        os.chdir(self.title)
        with open('challs.json','wb') as f:
            f.write(json.dumps(self.entry ,sort_keys=True, indent=4))

        r = re.compile("[^A-Za-z0-9 .\'_-]")
        for key, val in self.entry.iteritems():
            for keys, vals in val.iteritems():
                keys      = r.sub('',keys.strip())
                directory = '{}/{} [{} pts]'.format(key,keys,vals['Points'])
                directory = directory.replace(' / ','-')
                print 'Directory', directory,'has been created'
                if not os.path.exists(directory):
                    os.makedirs(directory)
                with open('{}/README.md'.format(directory),'wb') as f:
                    desc = vals['Description'].encode('utf-8').strip()
                    f.write('Description:\n{}'.format(desc))
                    f.write('\n\nHint:\n{}'.format(''.join(vals['Hint'])))

                files = vals['Files']
                if files:
                    for i in files:
                        #filename = i.split('/')[1]
                        filename=i.split('/')[3].split('?')[0]
                        print filename
                        if not os.path.exists(directory + '/' + filename):
                            print self.url + '/files/' + i
                            # resp = self.ses.get(self.url + '/files/' + i, stream=False) # slashroot ctfd lama
                            resp = self.ses.get(self.url + i, stream=False)
                            with open(directory + '/' + filename, 'wb') as f:
                            # with open(directory + '/' + i.split('/')[1], 'wb') as f:
                                f.write(resp.content)
                                f.close()

def main():
    url    = sys.argv[1]
    user   = sys.argv[2]
    passwd = sys.argv[3]
    ctf    = CTFdCrawl(user,passwd,url)
    ctf.parseAll()
    ctf.createArchive()

if __name__ == '__main__':
    main()
