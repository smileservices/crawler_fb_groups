import io


def log(message):
    print(message.encode('utf-8'))
    with io.open('logs/log', 'a', encoding="utf-8") as file:
        file.write(message + '\n')


def log_html(response, name):
    # from main import logs_count
    with io.open('logs/log_responses', 'a', encoding="utf-8") as file:
        file.write('-----------------' + '\n')
        file.write(response.url + ' with status code {}'.format(response.status_code) + '\n')
    with io.open('logs/responses/req_log_{}.html'.format(name), 'wb') as file:
        file.write(response.text.encode('utf-8'))
