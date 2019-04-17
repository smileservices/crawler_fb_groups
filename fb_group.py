import re, pickle, os, time
from log_setup import log, log_html


class NoCursor(Exception):
    pass


class NoUsersFound(Exception):
    pass


class RepeatingMembers(Exception):
    pass


class FBGroup:
    members_url = 'https://www.facebook.com/ajax/browser/list/group_confirmed_members/'
    cache_path = 'cache'
    requests = 0

    def __init__(self, group_id, user_id, basket_size, sess):
        self.group_id = group_id
        self.user_id = user_id
        self.basket_size = basket_size
        self.sess = sess
        self.cursor = ''
        self.members = set()
        self.cache_file_path = os.path.join(self.cache_path, '{}.pkl'.format(self.group_id))
        # set current result to members page
        self.current_result = self.sess.get('https://www.facebook.com/groups/{}/members/'.format(group_id))
        log_html(self.current_result, 'group_members')
        log('Retrieving members from initial group page..')
        self.gather_members()
        self.get_current_cursor()
        self.next_req_params = self.get_next_req_params()

    def get_cached_members(self):
        '''
        check if we cached the group and parse its members as set
        if the group is not cached, just create empty set
        '''
        try:
            cached_members = pickle.load(open(self.cache_file_path, 'rb'))
            log('Loaded {} cached members'.format(len(cached_members)))
            self.members |= cached_members
        except FileNotFoundError:
            log('No cache found for group id {}'.format(self.group_id))

    def get_current_cursor(self):
        '''
        If no match is found, cursor is set no None
        :return:
        '''
        log('Retrieving cursor from response ..')
        self.cursor = re.search(r'sectiontype=recently_joined&amp;memberstabexp=1&amp;cursor=(.*?)&',
                                self.current_result.text)
        if self.cursor is None:
            log('No cursor found in current response!')
            log_html(self.current_result, 'cursor_error')
            raise NoCursor('No cursor found in current response!')
        log('Current cursor is now {}'.format(self.cursor.group(1)))

    def get_next_req_params(self):
        spin_r = re.search('"__spin_r":(\d*),"', self.current_result.text)
        spin_t = re.search('"__spin_t":(\d*),"',
                           self.current_result.text[spin_r.start():spin_r.end() + 50])  # to limit the search string
        return {
            '__rev': spin_r.group(1),
            '__spin_r': spin_r.group(1),
            '__spin_t': spin_t.group(1),
        }

    def gather_members(self):
        regexp = 'member_id=(\d*)'
        members = set()
        duplicate = False
        for m in re.finditer(regexp, self.current_result.text):
            if m.group(1) not in self.members:
                members.add(m.group(1))
            else:
                duplicate = True
                break
        self.members |= members
        if duplicate is True:
            raise RepeatingMembers("Found duplicate member_id. Halting this group")


    def get_members(self):
        '''
        1. Retrieves member ids from request, makes new ones and if no more cursors or memberids start to repeat, then halts and serializes all members
        :return:
        '''
        log('Retrieving members from group id {}'.format(self.group_id))
        self.get_cached_members()
        try:
            while True:
                self.make_new_members_request()
                self.gather_members()
                self.get_current_cursor()
        except NoCursor:
            log('No cursor found')
        except RepeatingMembers:
            log('Repeating members')
        if len(self.members) > 0:
            pickle.dump(self.members, open(self.cache_file_path, 'wb'))
        else:
            log('No members found for group {}'.format(self.group_id))
            raise (NoUsersFound)

    def make_new_members_request(self):
        log('Doing the request with cursor {}'.format(self.cursor.group(1)))
        payload = {
            'gid': self.group_id,
            'order': 'date',
            'view': 'list',
            'limit': self.basket_size,
            'sectiontype': 'recently_joined',
            'memberstabexp': 1,
            'cursor': self.cursor.group(1),
            'start': 15,
            'dpr': 1,
            '__user': self.user_id,
            '__a': 1,
            '__dyn': self.dyn_rand(),
            '__req': 1,
            '__be': 1,
            '__pc': 'PHASED%3ADEFAULT',
            '__rev': self.next_req_params['__rev'],
            '__spin_r': self.next_req_params['__spin_r'],
            '__spin_b': 'trunk',
            '__spin_t': self.next_req_params['__spin_t']
        }
        start_time = time.time()
        self.current_result = self.sess.get(self.members_url, params=payload)
        log('Doing new request:')
        exec_time = round(time.time() - start_time, 2)
        self.requests += 1
        log('~~~~URL~~~~')
        log(self.current_result.url)
        log_html(self.current_result, 'members_last_req')
        log('Request number {} finished with status code {} in {} seconds'.format(self.requests,
                                                                                  self.current_result.status_code,
                                                                                  exec_time))
        time.sleep(2)

    def dyn_rand(self):
        '''
        randomize some string
        :return:
        '''
        import random
        from random import randint
        char_set = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-_'
        res = '7AgNe-'  # this seems to be the regular fb dyn start
        for i in range(randint(167, 186)):
            res += random.choice(char_set)
        return res
