import os
import subprocess
import threading
from selenium import webdriver
from pyquery import PyQuery as Pq


class Lesson:
    """
    <Lesson
  name=([第17集]正交矩阵和Gram-Schmidt正交化)
  url=(http://open.163.com/movie/2010/11/L/S/M6V0BQC4M_M6V2AORLS.html)>,
    """
    def __init__(self):
        # 课时 名称 课程页面
        self.name = ''
        self.url = ''

    def __repr__(self):
        name = self.__class__.__name__
        properties = ('{}=({})'.format(k, v) for k, v in self.__dict__.items())
        s = '\n<{} \n  {}>'.format(name, '\n  '.join(properties))
        return s


class Crawler:
    """
    爬取页面，生成lesson对象
    url: 课程目录主页的网址
    """
    def __init__(self, url):
        self.url = url

    def get_page(self):
        # 检查网页是否已经缓存，没有就下载
        folder = 'cache'
        filename = self.url.split('/')[-1]
        path = os.path.join(folder, filename)
        if os.path.exists(path):
            print('正在获取缓存')
            with open(path, 'rb') as f:
                r = f.read()
            return r
        else:
            if not os.path.exists(folder):
                os.mkdir(folder)
            driver = webdriver.Chrome()
            driver.get(self.url)
            # content = driver.page_source.replace('xmlns', 'sthelse').encode('UTF-8')
            content = driver.page_source.encode('UTF-8')
            with open(path, 'wb') as f:
                f.write(content)
            return content

    def vod_from_td(self, td):
        # 从单元格中获取每课的信息
        l = Lesson()
        e = Pq(td, parser='xml')
        l.name = e('.u-ctitle').text().replace(' ', '')
        l.url =  e('a').attr('href')
        return l

    def lessons_from_url(self):
        # 从课程目录页面获取各课时信息
        page = self.get_page()
        # <html xmlns = "http://www.w3.org/1999/xhtml"> 所以设置parser='xml'
        e = Pq(page, parser='xml')('#list2')
        items = e('.u-ctitle')
        # print(items)
        lessons = [self.vod_from_td(i) for i in items]
        return lessons


class YouGet:
    """
    调用you-get下载
    path: 视频保存位置，default：vod/
    lessons: 包含视频所在网页链接的leeson实例列表
    """
    def __init__(self, lessons, path='vod/'):
        self.lessons = lessons
        self.path = path
        if not os.path.exists(path):
            os.mkdir(path)

    def vod_down(self, link):
        """
        subprocess 调用 you-get 下载视频
        """
        subprocess.call(f"you-get -o {self.path} '{link}'", shell=True)

    def multi_thread(self):
        threads = []
        for i, l in enumerate(self.lessons):
            t = threading.Thread(target=self.vod_down, args=(l.url,), name=f'No.{i}')
            t.start()
            threads.append(t)
            # t.join()
        for t in threads:
            t.join()

    def check_complete(self):
        # 如果有以.downloading结尾的文件，说明下载未完成
        file_list = os.listdir(self.path)
        # file_downloaded = [f for f in file_list if f.endswith('.mp4')]
        for f in file_list:
            if f.endswith('.downloading'):
                return False
        return True

    def change_name(self):
        # 修改文件名 '麻省理工公开课：线性代数_正交矩阵和Gram-Schmidt正交化_网易公开课' -> [第17集]正交矩阵和Gram-Schmidt正交化
        file_list = [(name.split('_')[1], name) for name in os.listdir(self.path) if name.endswith('.mp4')]
        name_list = [l.name for l in self.lessons]
        # print(file_list,'\n-----------', name_list,  '\n------------')
        for a, b in file_list:
            for name in name_list:
                if a in name:
                    # print(os.path.join(self.path, b), os.path.join(self.path, name))
                    os.rename(os.path.join(self.path, b), os.path.join(self.path, name+'.mp4'))

    def get(self):
        # 多线程下载，最大重试次数3
        for i in range(1, 4):
            self.multi_thread()
            if self.check_complete():
                self.change_name()
                print('全部文件下载完成')
                break
            elif i < 3:
                print(f'有文件下载不成功, 正在进行第{i}次重试')
            else:
                print('部分文件下载失败')

if __name__ == '__main__':
    # 课程目录主页地址
    root = 'http://open.163.com/special/opencourse/daishu.html'
    craw = Crawler(root)
    lessons = craw.lessons_from_url()
    # print(lessons)
    yg = YouGet(lessons)
    yg.get()
