import json, os, errno
from log_setup import log
from fb_crawler import FBCrawler

#set up folders
for directory in ['results', 'logs', 'logs/responses', 'cache']:
    try:
        os.makedirs(directory)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
        continue

log('--------------------')
log('Starting a new session')

# import user config file
users_file = 'users.json'
users = json.load(open(users_file))

logs_count = 0

# login into fb account
for user in users:

    fb_handle = FBCrawler(user)
    fb_handle.refresh_members()
    log('!!!!!!!!!! Done with user {} !!!!!!!!!!!!!!'.format(user['username']))

log('Done!')
