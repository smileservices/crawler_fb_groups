import json
from log_setup import log
from fb_crawler import FBCrawler

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
    log('!!!!!!!!!! Done with user {} !!!!!!!!!!!!!!'.format(user.username))

log('Done!')
